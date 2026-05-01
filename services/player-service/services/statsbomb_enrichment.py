"""
StatsBomb Enrichment Service

Reads StatsBomb CSV event data, aggregates per-player advanced metrics
(xG, OBV, pass success probability), and writes them as statsbombEnrichment
onto the matching player documents in MongoDB.

Resolution strategy:
  1. Exact match on uID (StatsBomb player_id == Opta/F24 player uID)
  2. Fuzzy name match (normalised lower-case substring) as fallback

This service is intentionally simple — it operates on the one StatsBomb
match we have (Samsunspor vs Beşiktaş, 3946949) and can be extended when
more CSV files are available.
"""
from __future__ import annotations

import logging
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

sys.path.append("/app")

from motor.motor_asyncio import AsyncIOMotorDatabase
from shared.adapters.statsbomb.statsbomb_connector import StatsBombConnector

logger = logging.getLogger(__name__)


def _normalise_name(name: Optional[str]) -> str:
    """Lower-case, collapse whitespace, strip leading/trailing spaces."""
    if not name:
        return ""
    n = name.lower().strip()
    n = re.sub(r"\s+", " ", n)
    return n


class StatsBombEnrichmentService:
    """
    Matches StatsBomb player stats to MongoDB players and writes
    statsbombEnrichment onto each matched document.
    """

    def __init__(self, db: AsyncIOMotorDatabase, data_root: Optional[str] = None):
        self.db = db
        self.players_col = db["players"]
        config = {"data_root": data_root} if data_root else {}
        self.connector = StatsBombConnector(config)

    async def enrich(self, match_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the enrichment pipeline.

        Args:
            match_id: Specific StatsBomb match to process.
                      If None, processes all available CSV files.

        Returns:
            Summary dict with counts of matched, updated, and unmatched players.
        """
        matches_to_process: List[str]
        if match_id:
            matches_to_process = [match_id]
        else:
            matches_to_process = [m["match_id"] for m in self.connector.list_matches()]

        if not matches_to_process:
            return {"matched": 0, "updated": 0, "unmatched": 0, "errors": ["No StatsBomb CSV files found"]}

        totals = {"matched": 0, "updated": 0, "unmatched": 0, "errors": []}

        for mid in matches_to_process:
            result = await self._enrich_match(mid)
            totals["matched"] += result["matched"]
            totals["updated"] += result["updated"]
            totals["unmatched"] += result["unmatched"]
            totals["errors"].extend(result.get("errors", []))

        return totals

    async def _enrich_match(self, match_id: str) -> Dict[str, Any]:
        logger.info("Enriching players from StatsBomb match %s", match_id)

        sb_players = await self.connector.fetch_players(match_id=match_id)
        if not sb_players:
            return {"matched": 0, "updated": 0, "unmatched": 0,
                    "errors": [f"No players extracted from match {match_id}"]}

        # Build lookup indexes from MongoDB
        # - uid_index:  opta numeric uid → scoutpro_id
        # - name_index: normalised name  → scoutpro_id
        all_players = await self.players_col.find(
            {}, {"uID": 1, "scoutpro_id": 1, "provider_ids": 1, "name": 1}
        ).to_list(length=None)

        uid_index: Dict[str, str] = {}    # opta numeric uid → scoutpro_id
        name_index: Dict[str, str] = {}   # normalised name → scoutpro_id

        for p in all_players:
            scoutpro_id = str(p.get("scoutpro_id", p.get("uID", "")))
            # Index by numeric Opta ID (from provider_ids.opta or from uID)
            opta_num = str(p.get("provider_ids", {}).get("opta", "")).lstrip("p")
            if not opta_num:
                opta_num = str(p.get("uID", "")).lstrip("p")
            if opta_num:
                uid_index[opta_num] = scoutpro_id
            name = _normalise_name(p.get("name"))
            if name and scoutpro_id:
                name_index[name] = scoutpro_id

        matched = 0
        updated = 0
        unmatched_names: List[str] = []

        for sb_player in sb_players:
            sb_player_id = str(sb_player["player_id"])   # StatsBomb numeric ID
            player_name = sb_player["player_name"]

            # Strategy 1: exact Opta numeric UID match (they coincide for this dataset)
            target_scoutpro_id = uid_index.get(sb_player_id)

            # Strategy 2: normalised name match
            if not target_scoutpro_id:
                norm = _normalise_name(player_name)
                target_scoutpro_id = name_index.get(norm)

            # Strategy 3: partial last-name match
            if not target_scoutpro_id:
                parts = _normalise_name(player_name).split()
                if parts:
                    last = parts[-1]
                    candidates = [(sid, n) for n, sid in name_index.items() if last in n]
                    if len(candidates) == 1:
                        target_scoutpro_id = candidates[0][0]

            if not target_scoutpro_id:
                unmatched_names.append(player_name)
                continue

            matched += 1

            enrichment_doc = {
                # Write the StatsBomb provider reference into the golden record
                "provider_ids.statsbomb": sb_player_id,
                "statsbombEnrichment": {
                    "match_id": match_id,
                    "statsbomb_player_id": sb_player_id,
                    "total_xg": sb_player["total_xg"],
                    "total_obv": sb_player["total_obv"],
                    "passes": sb_player["passes"],
                    "shots": sb_player["shots"],
                    "goals": sb_player["goals"],
                    "avg_pass_success_prob": sb_player["avg_pass_success_prob"],
                    "position_name": sb_player.get("position_name"),
                    "team_name": sb_player.get("team_name"),
                }
            }

            result = await self.players_col.update_one(
                {"scoutpro_id": target_scoutpro_id},
                {"$set": enrichment_doc},
            )
            if result.modified_count > 0 or result.matched_count > 0:
                updated += 1

        unmatched = len(unmatched_names)
        if unmatched_names:
            logger.warning(
                "Unmatched StatsBomb players for match %s: %s",
                match_id, unmatched_names
            )

        logger.info(
            "StatsBomb enrichment for match %s: matched=%d updated=%d unmatched=%d",
            match_id, matched, updated, unmatched
        )

        return {
            "matched": matched,
            "updated": updated,
            "unmatched": unmatched,
            "unmatched_names": unmatched_names,
        }
