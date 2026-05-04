"""Project provider event batches into Mongo read models used by APIs and analytics."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo import UpdateOne

from shared.adapters.opta.opta_parser import OptaParser
from shared.adapters.statsbomb.statsbomb_parser import StatsbombParser
from shared.utils.database import DatabaseManager
from shared.utils.id_generator import generate as _gen_id


class BatchEventReadModelProjector:
    """Mirror batch-synced events into the live-style read models."""

    def __init__(
        self,
        mongodb_url: Optional[str] = None,
        mongodb_database: Optional[str] = None,
    ):
        self.mongodb_url = mongodb_url or os.getenv(
            "MONGODB_URL",
            f"mongodb://{os.getenv('MONGODB_HOST', 'mongo')}:"
            f"{os.getenv('MONGODB_PORT', '27017')}/scoutpro",
        )
        self.mongodb_database = mongodb_database or os.getenv("MONGODB_DATABASE", "scoutpro")
        self.db_manager = DatabaseManager()
        self.mongo_db = None
        self.match_events_collection = None
        self.matches_collection = None
        self.parsers = {
            "opta": OptaParser(),
            "statsbomb": StatsbombParser(),
        }

    async def _ensure_database(self):
        if self.mongo_db is not None:
            return

        self.mongo_db = await self.db_manager.connect_mongodb(
            self.mongodb_url,
            self.mongodb_database,
        )
        self.match_events_collection = self.mongo_db["match_events"]
        self.matches_collection = self.mongo_db["matches"]

    async def close(self):
        await self.db_manager.close_all()

    async def project(
        self,
        provider: str,
        match_id: str,
        raw_events: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        normalized_provider = str(provider or "").lower()
        match_key = str(match_id or "").strip()

        if normalized_provider not in self.parsers or not match_key or not raw_events:
            return {"projected_events": 0, "updated_matches": 0}

        await self._ensure_database()

        parsed_events = self._parse_events(normalized_provider, match_key, raw_events)
        if not parsed_events:
            return {"projected_events": 0, "updated_matches": 0}

        operations = []
        for parsed_event in parsed_events:
            event_doc = self._to_match_event_document(match_key, parsed_event, provider=normalized_provider)
            operations.append(
                UpdateOne(
                    {"matchID": match_key, "event_id": event_doc["event_id"]},
                    {"$set": event_doc},
                    upsert=True,
                )
            )

        projected_events = 0
        if operations:
            result = await self.match_events_collection.bulk_write(operations, ordered=False)
            projected_events = (
                int(getattr(result, "upserted_count", 0) or 0)
                + int(getattr(result, "modified_count", 0) or 0)
            )

        updated_matches = await self._update_match_document(match_key, parsed_events, normalized_provider)
        return {
            "projected_events": projected_events,
            "updated_matches": updated_matches,
        }

    def _parse_events(
        self,
        provider: str,
        match_id: str,
        raw_events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        parser = self.parsers[provider]

        if provider == "statsbomb":
            parsed_events = parser.parse_events(raw_events)
            for parsed_event in parsed_events:
                parsed_event.setdefault("match_id", match_id)
            return parsed_events

        return parser.parse_events({"match_id": match_id, "events": raw_events})

    async def _update_match_document(
        self,
        match_id: str,
        parsed_events: List[Dict[str, Any]],
        provider: str = "unknown",
    ) -> int:
        existing_match = await self.matches_collection.find_one(
            {"uID": {"$in": [match_id, self._coerce_identifier(match_id)]}},
            {
                "uID": 1,
                "homeTeamID": 1,
                "awayTeamID": 1,
                "home_team_id": 1,
                "away_team_id": 1,
                "date": 1,
                "status": 1,
            },
        ) or {}

        # Fallback team IDs converted to ScoutPro integers when no existing match
        opta_team_ids = self._collect_team_ids(parsed_events)
        sp_fallback_home = _gen_id("team", provider, str(opta_team_ids[0])) if opta_team_ids else ""
        sp_fallback_away = _gen_id("team", provider, str(opta_team_ids[1])) if len(opta_team_ids) > 1 else ""

        home_team_id = str(
            existing_match.get("homeTeamID")
            or existing_match.get("home_team_id")
            or sp_fallback_home
        )
        away_team_id = str(
            existing_match.get("awayTeamID")
            or existing_match.get("away_team_id")
            or sp_fallback_away
        )

        home_score = 0
        away_score = 0
        for parsed_event in parsed_events:
            if not parsed_event.get("is_goal"):
                continue

            # Convert raw Opta team_id to ScoutPro to match home/away_team_id
            raw_tid = parsed_event.get("team_id")
            event_team_id = str(_gen_id("team", provider, str(raw_tid))) if raw_tid else ""
            if event_team_id == home_team_id:
                home_score += 1
            elif event_team_id == away_team_id:
                away_score += 1

        match_update = {
            "uID": match_id,
            "homeTeamID": home_team_id,
            "awayTeamID": away_team_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "homeScore": home_score,
            "awayScore": away_score,
            "home_score": home_score,
            "away_score": away_score,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }

        if existing_match.get("date") is None:
            match_update["date"] = datetime.now(timezone.utc).isoformat()

        if existing_match.get("status") is None:
            match_update["status"] = "finished"

        result = await self.matches_collection.update_one(
            {"uID": match_id},
            {"$set": match_update},
            upsert=True,
        )
        if result.modified_count or result.upserted_id:
            return 1
        return 0

    @staticmethod
    def _to_match_event_document(
        match_id: str,
        parsed_event: Dict[str, Any],
        provider: str = "unknown",
    ) -> Dict[str, Any]:
        minute = BatchEventReadModelProjector._optional_int(parsed_event.get("minute")) or 0
        second = BatchEventReadModelProjector._optional_int(parsed_event.get("second")) or 0
        event_id = str(
            parsed_event.get("event_id")
            or parsed_event.get("id")
            or f"{match_id}-{minute}-{second}-{parsed_event.get('type_name', 'event')}"
        )

        event_source = parsed_event.get("event_source") or f"{provider}_batch"

        # Convert raw provider team/player IDs to ScoutPro integers so that
        # downstream queries using the frontend's homeTeamId/awayTeamId work.
        raw_team_id = parsed_event.get("team_id")
        raw_player_id = parsed_event.get("player_id")
        sp_team_id = _gen_id("team", provider, str(raw_team_id)) if raw_team_id else None
        sp_player_id = _gen_id("player", provider, str(raw_player_id)) if raw_player_id else None

        payload = {
            **parsed_event,
            "event_id": event_id,
            "matchID": match_id,
            "match_id": match_id,
            "scoutpro_match_id": _gen_id("match", provider, match_id),
            "player_id": sp_player_id,
            "team_id": sp_team_id,
            "minute": minute,
            "second": second,
            "period": BatchEventReadModelProjector._optional_int(parsed_event.get("period")) or 0,
            "timestamp_seconds": parsed_event.get("timestamp_seconds", minute * 60 + second),
            "timestamp": parsed_event.get("timestamp_seconds", minute * 60 + second),
            # event_source: stable tag for provenance tracking
            "event_source": event_source,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "raw_event": parsed_event,
        }
        payload.pop("id", None)
        return payload

    @staticmethod
    def _collect_team_ids(events: List[Dict[str, Any]]) -> List[int]:
        seen: List[int] = []
        for event in events:
            team_id = BatchEventReadModelProjector._optional_int(event.get("team_id"))
            if team_id is not None and team_id not in seen:
                seen.append(team_id)
        return seen

    @staticmethod
    def _coerce_identifier(value: Any) -> Any:
        text = str(value)
        return int(text) if text.isdigit() else text

    @staticmethod
    def _optional_int(value: Any) -> Optional[int]:
        if value in (None, "", "None"):
            return None
        text = str(value)
        return int(text) if text.isdigit() else None