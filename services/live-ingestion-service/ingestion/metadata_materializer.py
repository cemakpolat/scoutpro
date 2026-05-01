"""Materialize provider metadata into canonical player and team read models."""

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from shared.messaging import EventType, create_event, get_kafka_producer
from shared.resolution import ProviderMappingStore
from shared.utils.database import DatabaseManager

logger = logging.getLogger(__name__)


class MetadataMaterializer:
    """Persist provider metadata into Mongo-backed read models."""

    def __init__(self, mongodb_url: str, mongodb_database: str):
        self.mongodb_url = mongodb_url
        self.mongodb_database = mongodb_database
        self.db_manager = DatabaseManager()
        self.mongo_db = None
        self.players_collection = None
        self.teams_collection = None
        self.provider_mapping_store = None

    async def _ensure_database(self):
        if self.mongo_db is not None:
            return

        self.mongo_db = await self.db_manager.connect_mongodb(
            self.mongodb_url,
            self.mongodb_database,
        )
        self.players_collection = self.mongo_db["players"]
        self.teams_collection = self.mongo_db["teams"]
        self.provider_mapping_store = ProviderMappingStore(self.mongo_db)
        await self.provider_mapping_store.initialize()

    async def close(self):
        await self.db_manager.close_all()

    async def materialize(self, provider: str, match_id: str, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        if provider not in {"opta", "statsbomb"} or not documents:
            return {"teams": 0, "players": 0}

        await self._ensure_database()

        touched_team_ids = set()
        touched_player_ids = set()

        if provider == "opta":
            entity_sets = [self._extract_opta_entities(raw_document, match_id) for raw_document in documents]
        else:
            entity_sets = [self._extract_statsbomb_entities(documents, match_id)]

        for teams, players in entity_sets:
            for team_doc in teams:
                if not team_doc.get("uID"):
                    continue
                persisted_team = await self._upsert_team(team_doc)
                touched_team_ids.add(persisted_team["uID"])

            for player_doc in players:
                if not player_doc.get("uID"):
                    continue
                persisted_player = await self._upsert_player(player_doc)
                touched_player_ids.add(persisted_player["uID"])

        if touched_team_ids or touched_player_ids:
            logger.info(
                "Materialized metadata for match %s: %s teams, %s players",
                match_id,
                len(touched_team_ids),
                len(touched_player_ids),
            )

        return {
            "teams": len(touched_team_ids),
            "players": len(touched_player_ids),
        }

    def _extract_statsbomb_entities(self, rows: List[Dict[str, Any]], match_id: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        timestamp = datetime.now(timezone.utc).isoformat()
        teams_by_id: Dict[str, Dict[str, Any]] = {}
        players_by_id: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            if not isinstance(row, dict):
                continue

            team_provider_id = self._clean_text(row.get("team_id") or row.get("possession_team_id"))
            team_name = self._clean_text(row.get("team_name") or row.get("possession_team_name"))

            if team_provider_id and team_name:
                team_id = self._canonical_id(team_provider_id)
                team_doc = {
                    "uID": team_id,
                    "name": team_name,
                    "shortName": self._clean_text(row.get("team_short_name")),
                    "country": self._clean_text(row.get("country_name")),
                    "league": self._clean_text(row.get("competition_name")),
                    "sourceMatchID": str(match_id),
                    "updatedAt": timestamp,
                    "_provider_mapping": {
                        "provider": "statsbomb",
                        "provider_id": team_provider_id,
                        "source_match_id": str(match_id),
                        "metadata": {"team_name": team_name},
                    },
                }
                self._merge_documents(teams_by_id, team_id, team_doc)

            player_provider_id = self._clean_text(
                row.get("player_id") or row.get("formation_player_id") or row.get("substituted_player_id")
            )
            player_name = self._clean_text(
                row.get("player_name") or row.get("formation_player_name") or row.get("substituted_player_name")
            )

            if player_provider_id and player_name:
                player_id = self._canonical_id(player_provider_id)
                first_name, last_name = self._split_name(player_name)
                player_doc = {
                    "uID": player_id,
                    "name": player_name,
                    "first": first_name,
                    "last": last_name,
                    "position": self._clean_text(
                        row.get("player_position_name") or row.get("position_name") or row.get("formation_position_name") or "Unknown"
                    ),
                    "shirtNumber": self._optional_int(row.get("formation_jersey_number")),
                    "club": team_name,
                    "teamID": self._optional_int(team_provider_id) if team_provider_id else None,
                    "teamName": team_name,
                    "sourceMatchID": str(match_id),
                    "updatedAt": timestamp,
                    "_provider_mapping": {
                        "provider": "statsbomb",
                        "provider_id": player_provider_id,
                        "source_match_id": str(match_id),
                        "metadata": {"player_name": player_name},
                    },
                }
                self._merge_documents(players_by_id, player_id, player_doc)

        return list(teams_by_id.values()), list(players_by_id.values())

    def _extract_opta_entities(self, raw_document: Dict[str, Any], match_id: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        soccer_feed = raw_document.get("SoccerFeed", {})
        soccer_document = soccer_feed.get("SoccerDocument", {})

        if not isinstance(soccer_document, dict):
            return [], []

        document_attrs = soccer_document.get("@attributes", {})
        lineup_map = self._build_lineup_map(soccer_document)
        timestamp = datetime.now(timezone.utc).isoformat()

        teams: List[Dict[str, Any]] = []
        players: List[Dict[str, Any]] = []

        for team_node in self._ensure_list(soccer_document.get("Team")):
            team_doc = self._build_team_doc(team_node, document_attrs, match_id, timestamp)
            if not team_doc:
                continue

            teams.append(team_doc)

            team_lineup = lineup_map.get(team_doc["uID"], {})
            for player_node in self._ensure_list(team_node.get("Player")):
                player_doc = self._build_player_doc(
                    player_node,
                    team_doc,
                    document_attrs,
                    team_lineup,
                    timestamp,
                )
                if player_doc:
                    players.append(player_doc)

        return teams, players

    def _build_team_doc(
        self,
        team_node: Dict[str, Any],
        document_attrs: Dict[str, Any],
        match_id: str,
        timestamp: str,
    ) -> Optional[Dict[str, Any]]:
        attrs = team_node.get("@attributes", {})
        raw_team_id = attrs.get("uID")
        team_id = self._canonical_id(raw_team_id)

        if not team_id:
            return None

        stadium = team_node.get("Stadium") if isinstance(team_node.get("Stadium"), dict) else {}
        manager = self._format_person_name(team_node.get("TeamOfficial", {}).get("PersonName"))

        team_doc = {
            "uID": team_id,
            "name": self._clean_text(team_node.get("Name")),
            "shortName": self._clean_text(attrs.get("short_club_name") or team_node.get("SYMID")),
            "country": self._clean_text(team_node.get("Country") or attrs.get("country")),
            "stadium": self._clean_text(stadium.get("Name")),
            "capacity": self._optional_int(stadium.get("Capacity")),
            "manager": manager,
            "competitionID": self._optional_int(document_attrs.get("competition_id")),
            "seasonID": self._optional_int(document_attrs.get("season_id")),
            "league": self._clean_text(document_attrs.get("competition_name")),
            "sourceMatchID": str(match_id),
            "updatedAt": timestamp,
            "_provider_mapping": {
                "provider": "opta",
                "provider_id": raw_team_id,
                "source_match_id": str(match_id),
                "metadata": {"team_name": self._clean_text(team_node.get("Name"))},
            },
        }

        return self._compact(team_doc)

    def _build_player_doc(
        self,
        player_node: Dict[str, Any],
        team_doc: Dict[str, Any],
        document_attrs: Dict[str, Any],
        team_lineup: Dict[str, Dict[str, Any]],
        timestamp: str,
    ) -> Optional[Dict[str, Any]]:
        attrs = player_node.get("@attributes", {})
        raw_player_id = attrs.get("uID")
        player_id = self._canonical_id(raw_player_id)

        if not player_id:
            return None

        stat_map = self._extract_stat_map(player_node.get("Stat"))
        person_name = player_node.get("PersonName") if isinstance(player_node.get("PersonName"), dict) else {}
        lineup = team_lineup.get(player_id, {})

        first_name = self._clean_text(stat_map.get("first_name") or person_name.get("First"))
        last_name = self._clean_text(stat_map.get("last_name") or person_name.get("Last"))
        display_name = self._player_display_name(player_node, stat_map, first_name, last_name)
        canonical_team_id = team_doc["uID"]

        player_doc = {
            "uID": player_id,
            "name": display_name,
            "first": first_name,
            "last": last_name,
            "position": self._clean_text(
                lineup.get("position")
                or stat_map.get("real_position")
                or attrs.get("Position")
                or player_node.get("Position")
                or "Unknown"
            ),
            "age": self._age_from_birth_date(stat_map.get("birth_date")),
            "nationality": self._clean_text(stat_map.get("first_nationality") or stat_map.get("country")),
            "club": team_doc.get("name"),
            "height": self._clean_measurement(stat_map.get("height")),
            "weight": self._clean_measurement(stat_map.get("weight")),
            "shirtNumber": lineup.get("shirt_number") or self._optional_int(stat_map.get("jersey_num")),
            "teamID": self._optional_int(canonical_team_id) or canonical_team_id,
            "teamName": team_doc.get("name"),
            "competitionID": self._optional_int(document_attrs.get("competition_id")),
            "seasonID": self._optional_int(document_attrs.get("season_id")),
            "squadStatus": lineup.get("status"),
            "updatedAt": timestamp,
            "_provider_mapping": {
                "provider": "opta",
                "provider_id": raw_player_id,
                "source_match_id": team_doc.get("sourceMatchID"),
                "metadata": {"player_name": display_name},
            },
        }

        return self._compact(player_doc)

    def _build_lineup_map(self, soccer_document: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        lineup_map: Dict[str, Dict[str, Dict[str, Any]]] = {}

        for match_data in self._ensure_list(soccer_document.get("MatchData")):
            for team_data in self._ensure_list(match_data.get("TeamData")):
                attrs = team_data.get("@attributes", {})
                team_id = self._canonical_id(attrs.get("TeamRef"))
                if not team_id:
                    continue

                player_lineup = team_data.get("PlayerLineUp", {})
                for match_player in self._ensure_list(player_lineup.get("MatchPlayer")):
                    match_player_attrs = match_player.get("@attributes", {})
                    player_id = self._canonical_id(match_player_attrs.get("PlayerRef"))
                    if not player_id:
                        continue

                    lineup_map.setdefault(team_id, {})[player_id] = {
                        "position": self._clean_text(
                            match_player_attrs.get("Position") or match_player_attrs.get("SubPosition")
                        ),
                        "shirt_number": self._optional_int(match_player_attrs.get("ShirtNumber")),
                        "status": self._clean_text(match_player_attrs.get("Status")),
                    }

        return lineup_map

    async def _upsert_team(self, team_doc: Dict[str, Any]) -> Dict[str, Any]:
        team_payload = self._sanitize_document(team_doc)
        existing = await self.teams_collection.find_one({"uID": team_payload["uID"]}, {"_id": 1})
        await self._persist_provider_mapping("team", team_doc)
        await self.teams_collection.update_one(
            {"uID": team_payload["uID"]},
            {
                "$set": team_payload,
                "$unset": {"provider": "", "providerMappings": ""},
            },
            upsert=True,
        )
        await self._publish_entity_event(
            topic="team.events",
            event_type=EventType.TEAM_CREATED if existing is None else EventType.TEAM_UPDATED,
            entity_key="team",
            entity_id_key="team_id",
            document=team_payload,
        )
        return team_payload

    async def _upsert_player(self, player_doc: Dict[str, Any]) -> Dict[str, Any]:
        player_payload = self._sanitize_document(player_doc)
        existing = await self.players_collection.find_one({"uID": player_payload["uID"]}, {"_id": 1})
        await self._persist_provider_mapping("player", player_doc)
        await self.players_collection.update_one(
            {"uID": player_payload["uID"]},
            {
                "$set": player_payload,
                "$unset": {"provider": "", "providerMappings": ""},
            },
            upsert=True,
        )
        await self._publish_entity_event(
            topic="player.events",
            event_type=EventType.PLAYER_CREATED if existing is None else EventType.PLAYER_UPDATED,
            entity_key="player",
            entity_id_key="player_id",
            document=player_payload,
        )
        return player_payload

    async def _persist_provider_mapping(self, entity_type: str, document: Dict[str, Any]):
        mapping = document.get("_provider_mapping") or {}
        provider = mapping.get("provider")
        provider_id = mapping.get("provider_id")

        if not provider or not provider_id:
            return

        await self.provider_mapping_store.upsert_mapping(
            entity_type=entity_type,
            provider=provider,
            provider_id=str(provider_id),
            canonical_id=str(document["uID"]),
            display_name=document.get("name"),
            source_match_id=mapping.get("source_match_id"),
            metadata=mapping.get("metadata") or {},
        )

    async def _publish_entity_event(
        self,
        topic: str,
        event_type: EventType,
        entity_key: str,
        entity_id_key: str,
        document: Dict[str, Any],
    ):
        try:
            producer = await get_kafka_producer()
            event = create_event(
                event_type=event_type,
                data={
                    entity_id_key: document["uID"],
                    entity_key: document,
                },
                source_service="live-ingestion-service",
            )
            await producer.send_event(
                topic=topic,
                event=event.model_dump(mode="json"),
                key=str(document["uID"]),
            )
        except Exception as exc:
            logger.error("Failed to publish %s event for %s: %s", event_type.value, document.get("uID"), exc)

    @staticmethod
    def _extract_stat_map(stats: Any) -> Dict[str, Any]:
        stat_map: Dict[str, Any] = {}
        for stat in MetadataMaterializer._ensure_list(stats):
            if not isinstance(stat, dict):
                continue

            stat_type = stat.get("@attributes", {}).get("Type")
            if stat_type:
                stat_map[stat_type] = stat.get("@value")

        return stat_map

    @staticmethod
    def _player_display_name(
        player_node: Dict[str, Any],
        stat_map: Dict[str, Any],
        first_name: Optional[str],
        last_name: Optional[str],
    ) -> str:
        explicit_name = MetadataMaterializer._clean_text(player_node.get("Name"))
        if explicit_name:
            return explicit_name

        person_name = player_node.get("PersonName") if isinstance(player_node.get("PersonName"), dict) else {}
        known_name = MetadataMaterializer._clean_text(stat_map.get("known_name") or person_name.get("Known"))
        if known_name:
            return known_name

        full_name = " ".join(part for part in [first_name, last_name] if part)
        return full_name or "Unknown"

    @staticmethod
    def _split_name(name: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        cleaned = MetadataMaterializer._clean_text(name)
        if not cleaned:
            return None, None

        parts = cleaned.split()
        if len(parts) == 1:
            return parts[0], None
        return parts[0], " ".join(parts[1:])

    @staticmethod
    def _format_person_name(person: Any) -> Optional[str]:
        if isinstance(person, dict):
            known = MetadataMaterializer._clean_text(person.get("Known"))
            if known:
                return known

            full_name = " ".join(
                part
                for part in [
                    MetadataMaterializer._clean_text(person.get("First")),
                    MetadataMaterializer._clean_text(person.get("Last")),
                ]
                if part
            )
            return full_name or None

        return MetadataMaterializer._clean_text(person)

    @staticmethod
    def _canonical_id(value: Any) -> Optional[str]:
        if value in (None, "", "None"):
            return None

        text = str(value).strip()
        digits = "".join(character for character in text if character.isdigit())
        return digits or text

    @staticmethod
    def _optional_int(value: Any) -> Optional[int]:
        if value in (None, "", "None", "Unknown"):
            return None

        text = str(value).strip()
        return int(text) if text.isdigit() else None

    @staticmethod
    def _clean_measurement(value: Any) -> Optional[str]:
        if value in (None, "", "None", "Unknown"):
            return None
        return str(value).strip()

    @staticmethod
    def _clean_text(value: Any) -> Optional[str]:
        if value in (None, "", "None", "Unknown"):
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _age_from_birth_date(value: Any) -> Optional[int]:
        if value in (None, "", "None", "Unknown"):
            return None

        try:
            birth_date = date.fromisoformat(str(value))
        except ValueError:
            return None

        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    @staticmethod
    def _ensure_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    @staticmethod
    def _merge_documents(target: Dict[str, Dict[str, Any]], key: str, document: Dict[str, Any]):
        if key not in target:
            target[key] = document
            return

        existing = target[key]
        for field, value in document.items():
            if field not in existing or existing[field] in (None, "", {}, []):
                existing[field] = value

    @staticmethod
    def _sanitize_document(document: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in document.items() if not key.startswith("_")}

    @staticmethod
    def _compact(document: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: value
            for key, value in document.items()
            if value is not None and value != ""
        }