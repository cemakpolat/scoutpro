"""Batch statistics aggregator for the statistics-service.

Replaces scripts/event_aggregation_pipeline.py and
scripts/unified_event_evaluator.py.

Reads enriched events from the ``match_events`` MongoDB collection (written
by ``data-sync-service/sync/read_model_projector.py``) and aggregates
per-player and per-team statistics into:

  * ``player_statistics``   — one document per (player_id, match_id)
  * ``team_statistics``     — one document per (team_id, match_id)

The aggregator is designed to be called:
  1. From the statistics-service API endpoint ``POST /api/v1/aggregate/run``
  2. Programmatically after a data-sync-service batch sync completes

Both Opta and StatsBomb events share the same ``match_events`` schema
(normalized by the shared parsers), so this aggregator is provider-agnostic.

It also materializes match-level projections into ``match_statistics``,
``match_tactical_snapshot``, ``match_pass_network``, and
``match_sequence_summary``.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, UpdateOne

from services.match_projection_builder import MatchProjectionBuilder

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Unified event-type → metric bucket map (provider-agnostic names)
# ---------------------------------------------------------------------------
_PASS_TYPES = {"pass", "cross", "offside_pass", "corner_taken"}
_SHOT_TYPES = {"shot", "miss", "post", "attempt_saved", "goal", "blocked_shot"}
_TACKLE_TYPES = {"tackle"}
_INTERCEPTION_TYPES = {"interception"}
_CLEARANCE_TYPES = {"clearance"}
_DUEL_TYPES = {"duel", "aerial"}
_FOUL_TYPES = {"foul"}
_CARD_TYPES = {"card"}
_RECOVERY_TYPES = {"ball_recovery", "recovery"}


class BatchAggregator:
    """Aggregate match_events → player_statistics and team_statistics.

    Args:
        mongo_uri: MongoDB connection string. Defaults to the standard
                   Docker-compose URI.
        db_name:   Database name (default: ``scoutpro``).
    """

    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        db_name: str = "scoutpro",
    ) -> None:
        import os

        uri = mongo_uri or os.getenv(
            "MONGODB_URL",
            "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin",
        )
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]
        self.matches_collection = self.db.matches
        self.match_statistics_collection = self.db.match_statistics
        self.match_tactical_snapshot_collection = self.db.match_tactical_snapshot
        self.match_pass_network_collection = self.db.match_pass_network
        self.match_sequence_summary_collection = self.db.match_sequence_summary

    def close(self) -> None:
        self.client.close()

    @staticmethod
    def _append_identifier_variants(
        string_values: List[str],
        numeric_values: List[int],
        value: Any,
        prefix: str = '',
    ) -> None:
        if value in (None, ''):
            return

        raw_value = str(value).strip()
        if not raw_value:
            return

        if raw_value not in string_values:
            string_values.append(raw_value)

        stripped_value = raw_value
        if prefix and raw_value.lower().startswith(prefix.lower()):
            stripped_value = raw_value[1:]
            if stripped_value and stripped_value not in string_values:
                string_values.append(stripped_value)

        if stripped_value.isdigit():
            numeric_value = int(stripped_value)
            if numeric_value not in numeric_values:
                numeric_values.append(numeric_value)
            if prefix:
                prefixed_value = f'{prefix}{stripped_value}'
                if prefixed_value not in string_values:
                    string_values.append(prefixed_value)

    def _find_match_doc(self, match_id: str) -> Dict[str, Any]:
        string_values: List[str] = []
        numeric_values: List[int] = []
        self._append_identifier_variants(string_values, numeric_values, match_id, prefix='g')

        or_clauses: List[Dict[str, Any]] = []
        if string_values:
            or_clauses.extend([
                {'uID': {'$in': string_values}},
                {'provider_ids.opta': {'$in': string_values}},
                {'matchID': {'$in': string_values}},
                {'id': {'$in': string_values}},
                {'scoutpro_id': {'$in': string_values}},
            ])
        if numeric_values:
            or_clauses.extend([
                {'matchID': {'$in': numeric_values}},
                {'id': {'$in': numeric_values}},
                {'scoutpro_id': {'$in': numeric_values}},
            ])

        if not or_clauses:
            return {}

        return self.matches_collection.find_one({'$or': or_clauses}, {'_id': 0}) or {}

    @staticmethod
    def _resolve_scoutpro_match_id(match_doc: Dict[str, Any], events: List[Dict[str, Any]]) -> Optional[Any]:
        for candidate in (match_doc.get('scoutpro_id'), match_doc.get('id')):
            if candidate not in (None, ''):
                return candidate

        for event in events:
            candidate = event.get('scoutpro_match_id')
            if candidate not in (None, ''):
                return candidate

        return None

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def run(
        self,
        match_id: Optional[str] = None,
        competition_id: Optional[str] = None,
        season_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """Execute the full aggregation pipeline, processing one match at a time.

        Args:
            match_id:       Limit to a single match (optional).
            competition_id: Limit to a competition (optional).
            season_id:      Limit to a season (optional).

        Returns:
            Dict with counts of player/team/match projection docs written.
        """
        base_query: Dict[str, Any] = {}
        if competition_id:
            base_query["competition_id"] = competition_id
        if season_id:
            base_query["season_id"] = season_id

        # Determine which matches to aggregate
        if match_id:
            match_ids = [match_id]
        else:
            match_ids = self.db.match_events.distinct("matchID", base_query)

        if not match_ids:
            logger.warning("BatchAggregator: no match IDs found for query %s", base_query)
            return {"player_docs": 0, "team_docs": 0, "match_docs": 0}

        total_player_docs = 0
        total_team_docs = 0
        total_match_docs = 0

        # Process one match at a time to avoid loading all events into memory
        for mid in match_ids:
            query = dict(base_query)
            query["matchID"] = mid
            events = list(self.db.match_events.find(query))
            if not events:
                continue

            player_stats = self._aggregate_player_stats(events)
            team_stats = self._aggregate_team_stats(events)
            match_projections = self._aggregate_match_projections(str(mid), events)
            total_player_docs += self._upsert_player_stats(player_stats)
            total_team_docs += self._upsert_team_stats(team_stats)
            total_match_docs += self._upsert_match_projections(str(mid), match_projections)

        logger.info(
            "BatchAggregator: wrote %d player docs, %d team docs, %d match projection docs across %d matches",
            total_player_docs,
            total_team_docs,
            total_match_docs,
            len(match_ids),
        )
        return {
            "player_docs": total_player_docs,
            "team_docs": total_team_docs,
            "match_docs": total_match_docs,
        }

    # ------------------------------------------------------------------
    # Internal: player aggregation
    # ------------------------------------------------------------------

    def _aggregate_player_stats(
        self, events: List[Dict[str, Any]]
    ) -> Dict[tuple, Dict[str, Any]]:
        """Group events by (player_id, match_id) and compute stats."""
        buckets: Dict[tuple, Dict[str, Any]] = defaultdict(
            lambda: self._empty_player_stat()
        )

        for ev in events:
            player_id = ev.get("player_id") or ev.get("playerID")
            match_id = ev.get("matchID") or ev.get("match_id")
            if not player_id or not match_id:
                continue

            key = (str(player_id), str(match_id))
            b = buckets[key]

            b["player_id"] = player_id
            b["match_id"] = match_id
            b.setdefault("team_id", ev.get("team_id") or ev.get("teamID"))
            b.setdefault("competition_id", ev.get("competition_id"))
            b.setdefault("season_id", ev.get("season_id"))
            # ScoutPro IDs (will be set if the event was projected with new mapper)
            b.setdefault("scoutpro_player_id", ev.get("scoutpro_player_id"))
            b.setdefault("scoutpro_match_id", ev.get("scoutpro_match_id"))

            type_name = str(ev.get("type_name", "")).lower()
            is_ok = bool(ev.get("is_successful") or ev.get("outcome") == 1
                         or ev.get("outcome") == "1")

            b["total_events"] += 1
            self._update_type_bucket(b, type_name, is_ok, ev)

        return buckets

    def _empty_player_stat(self) -> Dict[str, Any]:
        return {
            "total_events": 0,
            "passes": 0,
            "passes_successful": 0,
            "crosses": 0,
            "crosses_successful": 0,
            "shots": 0,
            "shots_on_target": 0,
            "goals": 0,
            "tackles": 0,
            "tackles_successful": 0,
            "interceptions": 0,
            "clearances": 0,
            "aerials": 0,
            "aerials_won": 0,
            "fouls_committed": 0,
            "yellow_cards": 0,
            "red_cards": 0,
            "ball_recoveries": 0,
            "progressive_passes": 0,
            "entered_final_third": 0,
            "entered_box": 0,
            "total_xg": 0.0,
            "high_regains": 0,
            "minutes_played": 0,
        }

    def _update_type_bucket(
        self,
        b: Dict[str, Any],
        type_name: str,
        is_ok: bool,
        ev: Dict[str, Any],
    ) -> None:
        if type_name in _PASS_TYPES:
            b["passes"] += 1
            if is_ok:
                b["passes_successful"] += 1
            if ev.get("is_cross"):
                b["crosses"] += 1
                if is_ok:
                    b["crosses_successful"] += 1
            if ev.get("progressive_pass"):
                b["progressive_passes"] += 1
            if ev.get("entered_final_third"):
                b["entered_final_third"] += 1
            if ev.get("entered_box"):
                b["entered_box"] += 1

        elif type_name in _SHOT_TYPES:
            b["shots"] += 1
            if type_name in {"attempt_saved", "goal"} or ev.get("shot_outcome") in (
                "saved", "goal", "goal_confirmed"
            ):
                b["shots_on_target"] += 1
            if type_name == "goal" or ev.get("is_goal"):
                b["goals"] += 1
            xg = ev.get("analytical_xg") or ev.get("xg") or 0
            try:
                b["total_xg"] += float(xg)
            except (TypeError, ValueError):
                pass

        elif type_name in _TACKLE_TYPES:
            b["tackles"] += 1
            if is_ok:
                b["tackles_successful"] += 1

        elif type_name in _INTERCEPTION_TYPES:
            b["interceptions"] += 1

        elif type_name in _CLEARANCE_TYPES:
            b["clearances"] += 1
            if ev.get("high_regain"):
                b["high_regains"] += 1

        elif type_name in _DUEL_TYPES:
            b["aerials"] += 1
            if is_ok:
                b["aerials_won"] += 1

        elif type_name in _FOUL_TYPES:
            b["fouls_committed"] += 1

        elif type_name in _CARD_TYPES:
            card = str(ev.get("card_type", "")).lower()
            if "yellow" in card:
                b["yellow_cards"] += 1
            elif "red" in card:
                b["red_cards"] += 1

        elif type_name in _RECOVERY_TYPES:
            b["ball_recoveries"] += 1

    # ------------------------------------------------------------------
    # Internal: team aggregation
    # ------------------------------------------------------------------

    def _aggregate_team_stats(
        self, events: List[Dict[str, Any]]
    ) -> Dict[tuple, Dict[str, Any]]:
        buckets: Dict[tuple, Dict[str, Any]] = defaultdict(
            lambda: {
                "total_events": 0,
                "passes": 0,
                "passes_successful": 0,
                "shots": 0,
                "goals": 0,
                "tackles": 0,
                "interceptions": 0,
                "clearances": 0,
                "fouls": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "total_xg": 0.0,
            }
        )

        for ev in events:
            team_id = ev.get("team_id") or ev.get("teamID")
            match_id = ev.get("matchID") or ev.get("match_id")
            if not team_id or not match_id:
                continue

            key = (str(team_id), str(match_id))
            b = buckets[key]
            b.setdefault("team_id", team_id)
            b.setdefault("match_id", match_id)
            b.setdefault("competition_id", ev.get("competition_id"))
            b.setdefault("season_id", ev.get("season_id"))

            type_name = str(ev.get("type_name", "")).lower()
            is_ok = bool(ev.get("is_successful") or ev.get("outcome") == 1
                         or ev.get("outcome") == "1")
            b["total_events"] += 1

            if type_name in _PASS_TYPES:
                b["passes"] += 1
                if is_ok:
                    b["passes_successful"] += 1
            elif type_name in _SHOT_TYPES:
                b["shots"] += 1
                if type_name == "goal" or ev.get("is_goal"):
                    b["goals"] += 1
                xg = ev.get("analytical_xg") or 0
                try:
                    b["total_xg"] += float(xg)
                except (TypeError, ValueError):
                    pass
            elif type_name in _TACKLE_TYPES:
                b["tackles"] += 1
            elif type_name in _INTERCEPTION_TYPES:
                b["interceptions"] += 1
            elif type_name in _CLEARANCE_TYPES:
                b["clearances"] += 1
            elif type_name in _FOUL_TYPES:
                b["fouls"] += 1
            elif type_name in _CARD_TYPES:
                card = str(ev.get("card_type", "")).lower()
                if "yellow" in card:
                    b["yellow_cards"] += 1
                elif "red" in card:
                    b["red_cards"] += 1

        return buckets

    # ------------------------------------------------------------------
    # Internal: upsert helpers
    # ------------------------------------------------------------------

    def _upsert_player_stats(
        self, stats: Dict[tuple, Dict[str, Any]]
    ) -> int:
        if not stats:
            return 0
        ops = []
        now = datetime.now(timezone.utc).isoformat()
        for stat in stats.values():
            stat["updated_at"] = now
            ops.append(
                UpdateOne(
                    {"player_id": stat["player_id"], "match_id": stat["match_id"]},
                    {"$set": stat},
                    upsert=True,
                )
            )
        result = self.db.player_statistics.bulk_write(ops, ordered=False)
        return int(getattr(result, "upserted_count", 0) or 0) + int(
            getattr(result, "modified_count", 0) or 0
        )

    def _upsert_team_stats(
        self, stats: Dict[tuple, Dict[str, Any]]
    ) -> int:
        if not stats:
            return 0
        ops = []
        now = datetime.now(timezone.utc).isoformat()
        for stat in stats.values():
            stat["updated_at"] = now
            ops.append(
                UpdateOne(
                    {"team_id": stat["team_id"], "match_id": stat["match_id"]},
                    {"$set": stat},
                    upsert=True,
                )
            )
        result = self.db.team_statistics.bulk_write(ops, ordered=False)
        return int(getattr(result, "upserted_count", 0) or 0) + int(
            getattr(result, "modified_count", 0) or 0
        )

    def _aggregate_match_projections(
        self,
        match_id: str,
        events: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        match_doc = self._find_match_doc(match_id)
        scoutpro_match_id = self._resolve_scoutpro_match_id(match_doc, events)

        projections = {
            "match_statistics": MatchProjectionBuilder.build_advanced_metrics(match_id, match_doc, events, time_bucket="5m"),
            "match_tactical_snapshot": MatchProjectionBuilder.build_tactical_snapshot(match_id, events),
            "match_pass_network": MatchProjectionBuilder.build_pass_network(match_id, events),
            "match_sequence_summary": MatchProjectionBuilder.build_sequence_summary(match_id, match_doc, events) or {
                "matchId": match_id,
                "matchLabel": "",
                "providers": [],
                "teamSummaries": [],
                "topSequences": [],
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
        }

        if scoutpro_match_id not in (None, ''):
            for payload in projections.values():
                payload.setdefault('scoutpro_match_id', scoutpro_match_id)

        return projections

    def _upsert_match_projections(
        self,
        match_id: str,
        projections: Dict[str, Dict[str, Any]],
    ) -> int:
        if not projections:
            return 0

        collections = {
            "match_statistics": self.match_statistics_collection,
            "match_tactical_snapshot": self.match_tactical_snapshot_collection,
            "match_pass_network": self.match_pass_network_collection,
            "match_sequence_summary": self.match_sequence_summary_collection,
        }

        writes = 0
        for name, payload in projections.items():
            result = collections[name].update_one(
                {"match_id": match_id},
                {
                    "$set": {
                        **payload,
                        "match_id": match_id,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                },
                upsert=True,
            )
            writes += int(getattr(result, "modified_count", 0) or 0)
            writes += 1 if getattr(result, "upserted_id", None) else 0

        return writes
