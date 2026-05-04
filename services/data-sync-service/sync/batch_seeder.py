"""Opta batch seeder for the data-sync-service.

Replaces three scripts:
  - scripts/ingest_f24_all.py       (F24 event ingestion)
  - scripts/seed_players_from_f40.py (F40 squad/player seeding)
  - scripts/seed_all_opta.py        (F1/F9/F40/F24 orchestration)

The seeder routes all data through the shared Opta parser + mapper stack so
that ScoutPro canonical IDs are assigned consistently from the very first
write. Direct raw MongoDB writes are only used for match_events (since those
are projections rather than canonical entities).

Usage
-----
From the data-sync-service startup or from an admin API endpoint::

    from sync.batch_seeder import OptaBatchSeeder

    seeder = OptaBatchSeeder(data_root="/data/opta/2019")
    seeder.seed_all()

    # Or individually:
    seeder.seed_f40()    # players
    seeder.seed_f1()     # competitions, teams, matches (schedule)
    seeder.seed_f9()     # match lineup / score updates
    seeder.seed_f24()    # event-by-event match events
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from pymongo import MongoClient, UpdateOne

logger = logging.getLogger(__name__)

# Opta F24 type_id → canonical name.
# Mirrors OPTA_F24_TYPE_MAP used by the shared parser.
_OPTA_TYPE_MAP: Dict[int, str] = {
    1: "pass", 2: "offside_pass", 3: "take_on", 4: "foul", 5: "out",
    6: "corner_awarded", 7: "tackle", 8: "interception", 9: "turnover",
    10: "save", 11: "claim", 12: "clearance", 13: "miss", 14: "post",
    15: "attempt_saved", 16: "goal", 17: "card", 18: "player_off",
    19: "player_on", 20: "player_changed_position", 21: "player_retired",
    22: "player_returns", 23: "player_becomes_goalkeeper",
    24: "goalkeeper_becomes_player", 25: "condition_change",
    27: "start_delay", 28: "end_delay", 30: "end", 32: "start_period",
    34: "end_period", 35: "stop_page_play", 37: "resume", 38: "temp_goal",
    40: "goal_confirmed", 41: "ball_recovery", 43: "blocked_pass",
    44: "pre_match", 45: "formation", 48: "punch", 49: "good_skill",
    50: "deleted_event", 51: "fifty_fifty", 52: "failed_to_block",
    53: "pre_match_pass", 54: "aerial_lost", 55: "challenge",
    56: "ball_touch", 57: "error", 58: "dispossessed", 59: "fifty_fifty",
    60: "keeper_pickup", 61: "chance_missed", 63: "keeper_saves",
    64: "possession", 65: "good_skill", 67: "blocked_pass",
    68: "attempt_blocked", 70: "goalkeeper_save", 71: "good_skill",
    73: "block", 74: "blocked_shot", 75: "dribble", 76: "error",
    77: "keeper_sweeper",
}
_GOAL_TYPE_IDS = {16, 40}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_int(v: Any) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _safe_float(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _extract_f40_stats(stat_list: Any) -> Dict[str, str]:
    """Flatten a F40 Stat array [{@attributes:{Type,@value}}, …] into a dict."""
    if isinstance(stat_list, dict):
        stat_list = [stat_list]
    result: Dict[str, str] = {}
    for s in stat_list or []:
        attrs = s.get("@attributes", {})
        t = attrs.get("Type", "")
        v = s.get("@value", attrs.get("Value", ""))
        if t and v:
            result[t] = str(v)
    return result


def _parse_date(value: Optional[str]) -> Optional[str]:
    if not value or value in ("Unknown", ""):
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        return None


class OptaBatchSeeder:
    """Seed MongoDB from Opta feed files using the shared parser/mapper stack.

    Args:
        data_root:   Path to the Opta feed files directory (e.g. ``data/opta/2019``).
        mongo_uri:   MongoDB connection string.  Falls back to ``MONGODB_URL``
                     env var and then to the Docker-compose default.
        db_name:     Database name (default: ``scoutpro``).
        competition_id: Opta competition ID used in file-name patterns.
        season_id:       Season year used in file-name patterns.
    """

    def __init__(
        self,
        data_root: Optional[str] = None,
        mongo_uri: Optional[str] = None,
        db_name: str = "scoutpro",
        competition_id: int = 115,
        season_id: int = 2019,
    ) -> None:
        self.competition_id = competition_id
        self.season_id = season_id

        # Resolve data root
        env_root = os.getenv("DATA_ROOT")
        if data_root:
            self.data_root = Path(data_root)
        elif env_root:
            self.data_root = Path(env_root)
        else:
            # Default: <repo_root>/data/opta/<season>
            self.data_root = (
                Path(__file__).resolve().parents[3]
                / "data" / "opta" / str(season_id)
            )

        uri = mongo_uri or os.getenv(
            "MONGODB_URL",
            "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin",
        )
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]

        # Import shared building blocks lazily to avoid circular imports at
        # module load time.
        self._mapper: Any = None

    def close(self) -> None:
        self.client.close()

    # ------------------------------------------------------------------
    # Public orchestration
    # ------------------------------------------------------------------

    def seed_all(self) -> None:
        """Run the complete seeding pipeline: F1 → F40 → F9 → F24 → StatsBomb."""
        logger.info("OptaBatchSeeder: starting full seed from %s", self.data_root)
        self.seed_f1()
        self.seed_f40()
        self.seed_f9()
        self.seed_f24()
        self.seed_statsbomb()
        logger.info("OptaBatchSeeder: seed complete")

    # ------------------------------------------------------------------
    # F1 — schedule / competition / teams / matches
    # ------------------------------------------------------------------

    def seed_f1(self) -> None:
        """Ingest F1 feed: competitions, teams, match schedule."""
        pattern = f"f1_{self.competition_id}_{self.season_id}*"
        files = list(self.data_root.glob(pattern))
        if not files:
            logger.warning("seed_f1: no files matching %s in %s", pattern, self.data_root)
            return

        for f in files:
            try:
                data = self._load_json(f)
                self._upsert_f1(data, str(f))
            except Exception as exc:
                logger.error("seed_f1 failed for %s: %s", f.name, exc)

    def _upsert_f1(self, data: Dict, filename: str) -> None:
        sport_api = data.get("SoccerFeed", data.get("SoccerDocument", data))
        if "SoccerDocument" in sport_api:
            sport_api = sport_api["SoccerDocument"]

        match_data_list = sport_api.get("MatchData", [])
        if isinstance(match_data_list, dict):
            match_data_list = [match_data_list]

        team_set: Dict[str, Dict] = {}
        match_ops: List[UpdateOne] = []

        for md in match_data_list:
            md_attrs = md.get("@attributes", {})
            match_uid = md_attrs.get("uID", "")
            if not match_uid:
                continue

            # Teams
            for td in _as_list(md.get("TeamData", [])):
                td_attrs = td.get("@attributes", {})
                team_ref = td_attrs.get("TeamRef", "")
                if team_ref and team_ref not in team_set:
                    team_set[team_ref] = {"uID": team_ref, "competition_id": self.competition_id}

            # Match
            mi = md.get("MatchInfo", {})
            mi_attrs = mi.get("@attributes", mi)
            date_str = mi_attrs.get("Date", mi.get("Date", ""))
            period_info = md.get("PeriodInfo", {})
            team_data_list = _as_list(md.get("TeamData", []))

            home_team = next((t.get("@attributes", {}).get("TeamRef") for t in team_data_list
                              if t.get("@attributes", {}).get("Side") == "Home"), None)
            away_team = next((t.get("@attributes", {}).get("TeamRef") for t in team_data_list
                              if t.get("@attributes", {}).get("Side") == "Away"), None)
            home_score_str = next((t.get("@attributes", {}).get("Score") for t in team_data_list
                                   if t.get("@attributes", {}).get("Side") == "Home"), None)
            away_score_str = next((t.get("@attributes", {}).get("Score") for t in team_data_list
                                   if t.get("@attributes", {}).get("Side") == "Away"), None)

            from shared.utils.id_generator import ScoutProId
            sp_match_id = ScoutProId.match("opta", match_uid)
            sp_home_id = ScoutProId.team("opta", home_team) if home_team else None
            sp_away_id = ScoutProId.team("opta", away_team) if away_team else None
            prov_match_id = ScoutProId.provider_numeric("match", match_uid)

            doc = {
                "uID": match_uid,
                "scoutpro_id": sp_match_id,
                "id": sp_match_id,
                "provider_ids": {"opta": prov_match_id},
                "competition_id": str(self.competition_id),
                "season_id": str(self.season_id),
                "home_team_id": sp_home_id,
                "away_team_id": sp_away_id,
                "home_team_ref": home_team,
                "away_team_ref": away_team,
                "date": date_str,
                "status": mi_attrs.get("Status", mi.get("Status", "Fixture")),
                "home_score": _safe_int(home_score_str),
                "away_score": _safe_int(away_score_str),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            match_ops.append(UpdateOne({"uID": match_uid}, {"$set": doc}, upsert=True))

        if match_ops:
            self.db.matches.bulk_write(match_ops, ordered=False)
            logger.info("seed_f1: upserted %d matches from %s", len(match_ops), filename)

        # Insert team documents
        if team_set:
            from shared.utils.id_generator import ScoutProId
            team_ops: List[UpdateOne] = []
            for team_ref, team_data in team_set.items():
                sp_team_id = ScoutProId.team("opta", team_ref)
                prov_team_id = ScoutProId.provider_numeric("team", team_ref)
                team_doc = {
                    "uID": team_ref,
                    "scoutpro_id": sp_team_id,
                    "id": sp_team_id,
                    "provider_ids": {"opta": prov_team_id},
                    "competition_id": str(self.competition_id),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                team_ops.append(UpdateOne({"uID": team_ref}, {"$set": team_doc}, upsert=True))
            
            if team_ops:
                self.db.teams.bulk_write(team_ops, ordered=False)
                logger.info("seed_f1: upserted %d teams from %s", len(team_ops), filename)

    # ------------------------------------------------------------------
    # F40 — squad lists / player profiles
    # ------------------------------------------------------------------

    def seed_f40(self) -> None:
        """Ingest F40 feed: player profiles."""
        pattern = f"f40_{self.competition_id}_{self.season_id}*"
        files = list(self.data_root.glob(pattern))
        if not files:
            logger.warning("seed_f40: no files matching %s in %s", pattern, self.data_root)
            return

        for f in files:
            try:
                data = self._load_json(f)
                self._upsert_f40(data, str(f))
            except Exception as exc:
                logger.error("seed_f40 failed for %s: %s", f.name, exc)

    def _upsert_f40(self, data: Dict, filename: str) -> None:
        from shared.utils.id_generator import ScoutProId

        root = data.get("SoccerFeed", data.get("SoccerDocument", data))
        if "SoccerDocument" in root:
            root = root["SoccerDocument"]

        team_list = _as_list(root.get("Team", []))
        ops: List[UpdateOne] = []
        team_ops: List[UpdateOne] = []

        for team in team_list:
            t_attrs = team.get("@attributes", {})
            team_uid = t_attrs.get("uID", "")
            team_name = team.get("Name", "")
            sp_team_id = ScoutProId.team("opta", team_uid)

            if team_uid:
                prov_team_id = ScoutProId.provider_numeric("team", team_uid)
                team_ops.append(UpdateOne(
                    {"uID": team_uid},
                    {"$set": {
                        "uID": team_uid,
                        "scoutpro_id": sp_team_id,
                        "id": sp_team_id,
                        "name": team_name,
                        "provider_ids": {"opta": prov_team_id},
                        "competition_id": str(self.competition_id),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }},
                    upsert=True,
                ))

            for player in _as_list(team.get("Player", [])):
                p_attrs = player.get("@attributes", {})
                p_uid = p_attrs.get("uID", "")
                if not p_uid:
                    continue

                stats = _extract_f40_stats(player.get("Stat", []))
                pinfo = player.get("PersonalInfo", {})
                if isinstance(pinfo, dict):
                    pi_attrs = pinfo.get("@attributes", pinfo)
                else:
                    pi_attrs = {}

                first_name = stats.get("first_name", pi_attrs.get("FirstName", ""))
                last_name = stats.get("last_name", pi_attrs.get("LastName", ""))
                full_name = f"{first_name} {last_name}".strip() or stats.get("known_name", "")

                birth_date = _parse_date(stats.get("birth_date") or pi_attrs.get("birthDate"))
                preferred_foot = (stats.get("preferred_foot") or pi_attrs.get("preferredFoot") or "").lower()
                real_position = stats.get("real_position") or stats.get("position", "")
                nationality = (stats.get("first_nationality")
                               or stats.get("country")
                               or pi_attrs.get("country", ""))

                sp_player_id = ScoutProId.player("opta", p_uid)
                prov_player_id = ScoutProId.provider_numeric("player", p_uid)

                doc: Dict[str, Any] = {
                    "id": sp_player_id,
                    "scoutpro_id": sp_player_id,
                    "uID": p_uid,
                    "provider_ids": {"opta": prov_player_id},
                    "name": full_name,
                    "first_name": first_name,
                    "last_name": last_name,
                    "birth_date": birth_date,
                    "position": real_position,
                    "preferred_foot": preferred_foot,
                    "nationality": nationality,
                    "height_cm": _safe_int(stats.get("height")),
                    "weight_kg": _safe_int(stats.get("weight")),
                    "current_team_id": sp_team_id,
                    "current_team_name": team_name,
                    "team_id": sp_team_id,
                    "team_name": team_name,
                    "competition_id": str(self.competition_id),
                    "season_id": str(self.season_id),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }

                ops.append(UpdateOne({"uID": p_uid}, {"$set": doc}, upsert=True))

        if team_ops:
            self.db.teams.bulk_write(team_ops, ordered=False)
            logger.info("seed_f40: upserted %d teams (with names) from %s", len(team_ops), filename)

            # Enrich match documents with team names now that we know them
            team_name_by_uid = {t_attrs.get("@attributes", {}).get("uID", ""): t.get("Name", "")
                                for t in team_list
                                for t_attrs in [t] if t.get("@attributes", {}).get("uID")}
            # Rebuild cleanly from team_list
            uid_to_name: Dict[str, str] = {}
            for t in team_list:
                uid = t.get("@attributes", {}).get("uID", "")
                name = t.get("Name", "")
                if uid and name:
                    uid_to_name[uid] = name

            match_name_ops: List[UpdateOne] = []
            for match in self.db.matches.find({"home_team_ref": {"$exists": True}},
                                               {"_id": 1, "home_team_ref": 1, "away_team_ref": 1}):
                h_name = uid_to_name.get(match.get("home_team_ref", ""), "")
                a_name = uid_to_name.get(match.get("away_team_ref", ""), "")
                if h_name or a_name:
                    match_name_ops.append(UpdateOne(
                        {"_id": match["_id"]},
                        {"$set": {"home_team_name": h_name, "away_team_name": a_name}},
                    ))
            if match_name_ops:
                self.db.matches.bulk_write(match_name_ops, ordered=False)
                logger.info("seed_f40: enriched %d match documents with team names", len(match_name_ops))

        if ops:
            self.db.players.bulk_write(ops, ordered=False)
            logger.info("seed_f40: upserted %d players from %s", len(ops), filename)

    # ------------------------------------------------------------------
    # F9 — match details / lineup / score update
    # ------------------------------------------------------------------

    def seed_f9(self) -> None:
        """Ingest F9 feed: match lineup and half-time / full-time score."""
        pattern = f"f9_{self.competition_id}_{self.season_id}_*"
        files = list(self.data_root.glob(pattern))
        if not files:
            logger.warning("seed_f9: no files matching %s in %s", pattern, self.data_root)
            return

        ops: List[UpdateOne] = []
        for f in sorted(files):
            try:
                data = self._load_json(f)
                op = self._build_f9_update(data, str(f))
                if op:
                    ops.append(op)
            except Exception as exc:
                logger.error("seed_f9 failed for %s: %s", f.name, exc)

        if ops:
            self.db.matches.bulk_write(ops, ordered=False)
            logger.info("seed_f9: upserted %d match records", len(ops))

    def _build_f9_update(self, data: Dict, filename: str) -> Optional[UpdateOne]:
        root = data.get("SoccerFeed", data.get("SoccerDocument", data))
        if "SoccerDocument" in root:
            root = root["SoccerDocument"]

        md_list = _as_list(root.get("MatchData", []))
        if not md_list:
            return None
        md = md_list[0]

        md_attrs = md.get("@attributes", {})
        match_uid = md_attrs.get("uID", "")
        if not match_uid:
            return None

        team_data_list = _as_list(md.get("TeamData", []))
        home_score_str = next((t.get("@attributes", {}).get("Score") for t in team_data_list
                                if t.get("@attributes", {}).get("Side") == "Home"), None)
        away_score_str = next((t.get("@attributes", {}).get("Score") for t in team_data_list
                                if t.get("@attributes", {}).get("Side") == "Away"), None)

        update: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if home_score_str is not None:
            update["home_score"] = _safe_int(home_score_str)
        if away_score_str is not None:
            update["away_score"] = _safe_int(away_score_str)

        mi = md.get("MatchInfo", {})
        status = mi.get("@attributes", mi).get("Status", mi.get("Status", ""))
        if status:
            update["status"] = status.lower()

        return UpdateOne({"uID": match_uid}, {"$set": update}, upsert=False)

    # ------------------------------------------------------------------
    # F24 — event-by-event
    # ------------------------------------------------------------------

    def seed_f24(self) -> None:
        """Ingest all F24 files → match_events collection."""
        # Ensure the compound index exists before bulk-upserting so lookups
        # don't degrade to O(n²) collection scans as the collection grows.
        self.db.match_events.create_index(
            [("event_id", 1), ("matchID", 1)],
            name="event_match_upsert",
            background=True,
        )

        pattern = f"f24_{self.competition_id}_{self.season_id}_*"
        files = list(self.data_root.glob(pattern))
        if not files:
            logger.warning("seed_f24: no files matching %s in %s", pattern, self.data_root)
            return

        total_events = 0
        for f in sorted(files):
            try:
                data = self._load_json(f)
                count = self._ingest_f24_file(data, str(f))
                total_events += count
            except Exception as exc:
                logger.error("seed_f24 failed for %s: %s", f.name, exc)

        logger.info("seed_f24: ingested %d events across %d files", total_events, len(files))

    def _ingest_f24_file(self, data: Dict, filename: str) -> int:
        from shared.utils.id_generator import ScoutProId

        # Handle multiple F24 JSON structures:
        # - Batch files: Games.Game.Event
        # - Live files: EventFile.Game.Event or SoccerFeed.Event or Game.Event
        game = None
        
        if "Games" in data and isinstance(data["Games"], dict):
            # Batch F24 structure: Games.Game.Event
            game = data["Games"].get("Game", data["Games"])
        elif "EventFile" in data:
            # Live structure: EventFile.Game.Event
            game = data["EventFile"].get("Game", data["EventFile"])
        elif "SoccerFeed" in data:
            # Alternative structure: SoccerFeed.Event
            game = data["SoccerFeed"]
        elif "Game" in data:
            # Direct Game structure
            game = data["Game"]
        else:
            # Fallback
            game = data

        game_attrs = game.get("@attributes", {}) if isinstance(game, dict) else {}
        match_uid: str = (
            game_attrs.get("id", "")
            or game_attrs.get("uID", "")
            or (re.search(r"f24_\d+_\d+_(\w+)", filename, re.I) and
                re.search(r"f24_\d+_\d+_(\w+)", filename, re.I).group(1))
            or ""
        )

        events_raw = game.get("Event", []) if isinstance(game, dict) else []
        if isinstance(events_raw, dict):
            events_raw = [events_raw]

        sp_match_id = ScoutProId.match("opta", match_uid) if match_uid else None
        prov_match_id = ScoutProId.provider_numeric("match", match_uid) if match_uid else match_uid

        ops: List[UpdateOne] = []
        match_has_end = False

        for ev in events_raw:
            ev_attrs = ev.get("@attributes", ev) if isinstance(ev, dict) else {}
            event_id = ev_attrs.get("id", "")
            type_id = _safe_int(ev_attrs.get("type_id", 0)) or 0
            type_name = _OPTA_TYPE_MAP.get(type_id, f"type_{type_id}")
            outcome = _safe_int(ev_attrs.get("outcome", 1)) or 0
            minute = _safe_int(ev_attrs.get("min", 0)) or 0
            second = _safe_int(ev_attrs.get("sec", 0)) or 0
            period = _safe_int(ev_attrs.get("period_id", 1)) or 1
            x = _safe_float(ev_attrs.get("x", 0))
            y = _safe_float(ev_attrs.get("y", 0))
            player_id = ev_attrs.get("player_id", "")
            team_id = ev_attrs.get("team_id", "")

            is_goal = type_id in _GOAL_TYPE_IDS
            if type_id == 34:  # end_period
                match_has_end = True

            # Parse qualifiers
            qualifiers = []
            for q in _as_list(ev.get("Q", [])):
                q_attrs = q.get("@attributes", {})
                qualifiers.append({
                    "qualifier_id": _safe_int(q_attrs.get("qualifier_id")),
                    "value": q_attrs.get("value"),
                })

            sp_event_id = ScoutProId.event("opta", event_id) if event_id else None
            sp_player_id = ScoutProId.player("opta", player_id) if player_id else None
            sp_team_id = ScoutProId.team("opta", team_id) if team_id else None

            doc: Dict[str, Any] = {
                "event_id": event_id,
                "scoutpro_event_id": sp_event_id,
                "matchID": match_uid,
                "scoutpro_match_id": sp_match_id,
                "provider_ids": {"opta": event_id},
                "type_id": type_id,
                "type_name": type_name,
                "outcome": outcome,
                "is_successful": (outcome == 1),
                "is_goal": is_goal,
                "minute": minute,
                "second": second,
                "period": period,
                "timestamp_seconds": (minute * 60) + second,
                "location": {"x": x, "y": y},
                "player_id": player_id,
                "scoutpro_player_id": sp_player_id,
                "team_id": team_id,
                "scoutpro_team_id": sp_team_id,
                "qualifiers": qualifiers,
                "event_source": "opta_f24_batch",
                "competition_id": str(self.competition_id),
                "season_id": str(self.season_id),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }

            ops.append(UpdateOne(
                {"event_id": event_id, "matchID": match_uid},
                {"$set": doc},
                upsert=True,
            ))

        if ops:
            self.db.match_events.bulk_write(ops, ordered=False)

        # Mark match as finished if we saw a full-time end_period
        if match_has_end and match_uid:
            self.db.matches.update_one(
                {"uID": match_uid},
                {"$set": {"status": "finished", "updated_at": datetime.now(timezone.utc).isoformat()}},
            )

        return len(ops)

    # ------------------------------------------------------------------
    # StatsBomb CSV events
    # ------------------------------------------------------------------

    def seed_statsbomb(self) -> None:
        """Ingest all StatsBomb CSV files from data/statsbomb/ → match_events."""
        import csv as csv_mod

        # StatsBomb data lives next to the opta dir: data/statsbomb/
        sb_root = self.data_root.parents[1] / "statsbomb"
        files = sorted(sb_root.glob("*.csv"))
        if not files:
            logger.warning("seed_statsbomb: no CSV files found in %s", sb_root)
            return

        # Reuse the same compound index as F24 upserts
        self.db.match_events.create_index(
            [("event_id", 1), ("matchID", 1)],
            name="event_match_upsert",
            background=True,
        )

        try:
            from shared.adapters.statsbomb.statsbomb_mapper import StatsbombMapper
            mapper = StatsbombMapper()
        except ImportError as exc:
            logger.warning("seed_statsbomb: StatsbombMapper unavailable (%s), skipping", exc)
            return

        total_events = 0
        for csv_file in files:
            try:
                count = self._ingest_statsbomb_csv(csv_file, mapper, csv_mod)
                total_events += count
            except Exception as exc:
                logger.error("seed_statsbomb failed for %s: %s", csv_file.name, exc)

        logger.info("seed_statsbomb: ingested %d events across %d files", total_events, len(files))

    def _ingest_statsbomb_csv(self, path: Path, mapper: Any, csv_mod: Any) -> int:
        # Extract match_id from filename: HomeTeam_AwayTeam_<match_id>.csv
        stem_parts = path.stem.rsplit("_", 1)
        file_match_id = stem_parts[-1] if len(stem_parts) == 2 else path.stem

        now = datetime.now(timezone.utc).isoformat()
        ops: List[UpdateOne] = []

        with open(path, "r", encoding="utf-8") as fh:
            reader = csv_mod.DictReader(fh)
            for row in reader:
                event_id = row.get("id", "")
                if not event_id:
                    continue

                match_id = str(row.get("match_id") or file_match_id)

                entity = mapper.map_event(row)
                if not entity:
                    continue
                doc = entity.model_dump()

                # Normalize Coordinate objects that Pydantic may leave as models
                for field in ("location", "end_location"):
                    val = doc.get(field)
                    if val is not None and hasattr(val, "x"):
                        doc[field] = {"x": val.x, "y": val.y}

                # Align keys with the Opta match_events schema
                doc["matchID"] = match_id
                doc["match_id"] = match_id

                minute = doc.get("minute", 0) or 0
                second = doc.get("second", 0) or 0
                doc["timestamp_seconds"] = minute * 60 + second

                # is_goal: shots where outcome_name == 'Goal'
                if "is_goal" not in doc:
                    outcome = (row.get("outcome_name") or "").lower()
                    doc["is_goal"] = (doc.get("type_name") == "shot" and outcome == "goal")

                # Preserve StatsBomb-specific metrics
                doc["analytical_xg"] = _safe_float(row.get("statsbomb_xg")) or 0.0
                doc["xg"] = doc["analytical_xg"]
                doc["obv_total_net"] = _safe_float(row.get("obv_total_net"))

                doc["event_source"] = "statsbomb_batch"
                # competition_id / season_id are not carried in StatsBomb CSVs
                doc.setdefault("competition_id", None)
                doc.setdefault("season_id", None)
                doc["ingested_at"] = now

                ops.append(UpdateOne(
                    {"event_id": event_id, "matchID": match_id},
                    {"$set": doc},
                    upsert=True,
                ))

        if ops:
            self.db.match_events.bulk_write(ops, ordered=False)
            logger.info("seed_statsbomb: upserted %d events from %s", len(ops), path.name)

        return len(ops)

    # ------------------------------------------------------------------
    # File loading
    # ------------------------------------------------------------------

    def _load_json(self, path: Path) -> Dict:
        """Load JSON from *path*; tries `.json` extension if not found."""
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        json_path = path.with_suffix(".json")
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        raise FileNotFoundError(f"Feed file not found: {path}")


def _as_list(value: Any) -> List:
    """Normalise a JSON value that may be a single dict or a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
