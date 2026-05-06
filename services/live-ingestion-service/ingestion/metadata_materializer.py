"""Materialize provider metadata into Mongo-backed canonical read models."""

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from shared.messaging import EventType, create_event, get_kafka_producer
from shared.resolution import ProviderMappingStore
from shared.utils.database import DatabaseManager
from shared.utils.id_generator import ScoutProId

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
        self.competitions_collection = None
        self.seasons_collection = None
        self.venues_collection = None
        self.matches_collection = None
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
        self.competitions_collection = self.mongo_db["competitions"]
        self.seasons_collection = self.mongo_db["seasons"]
        self.venues_collection = self.mongo_db["venues"]
        self.matches_collection = self.mongo_db["matches"]
        self.provider_mapping_store = ProviderMappingStore(self.mongo_db)
        await self.provider_mapping_store.initialize()

    async def close(self):
        await self.db_manager.close_all()

    async def materialize(self, provider: str, match_id: str, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        if provider not in {"opta", "statsbomb"} or not documents:
            return {
                "competitions": 0,
                "seasons": 0,
                "venues": 0,
                "matches": 0,
                "teams": 0,
                "players": 0,
            }

        await self._ensure_database()

        touched_competition_ids = set()
        touched_season_ids = set()
        touched_venue_ids = set()
        touched_match_ids = set()
        touched_team_ids = set()
        touched_player_ids = set()

        if provider == "opta":
            entity_sets = [self._extract_opta_entities(raw_document, match_id) for raw_document in documents]
        else:
            entity_sets = [self._extract_statsbomb_entities(documents, match_id)]

        for entity_set in entity_sets:
            for competition_doc in entity_set["competitions"]:
                if competition_doc.get("scoutpro_id") in (None, ""):
                    continue
                persisted_competition = await self._upsert_competition(competition_doc)
                touched_competition_ids.add(str(persisted_competition["scoutpro_id"]))

            for season_doc in entity_set["seasons"]:
                if season_doc.get("scoutpro_id") in (None, ""):
                    continue
                persisted_season = await self._upsert_season(season_doc)
                touched_season_ids.add(str(persisted_season["scoutpro_id"]))

            for venue_doc in entity_set["venues"]:
                if venue_doc.get("scoutpro_id") in (None, ""):
                    continue
                persisted_venue = await self._upsert_venue(venue_doc)
                touched_venue_ids.add(str(persisted_venue["scoutpro_id"]))

            for match_doc in entity_set["matches"]:
                if not match_doc.get("uID"):
                    continue
                persisted_match = await self._upsert_match(match_doc)
                touched_match_ids.add(str(persisted_match["uID"]))

            for team_doc in entity_set["teams"]:
                if not team_doc.get("uID"):
                    continue
                persisted_team = await self._upsert_team(team_doc)
                touched_team_ids.add(persisted_team["uID"])

            for player_doc in entity_set["players"]:
                if not player_doc.get("uID"):
                    continue
                persisted_player = await self._upsert_player(player_doc)
                touched_player_ids.add(persisted_player["uID"])

        if touched_competition_ids or touched_season_ids or touched_venue_ids or touched_match_ids or touched_team_ids or touched_player_ids:
            logger.info(
                "Materialized metadata for match %s: %s competitions, %s seasons, %s venues, %s matches, %s teams, %s players",
                match_id,
                len(touched_competition_ids),
                len(touched_season_ids),
                len(touched_venue_ids),
                len(touched_match_ids),
                len(touched_team_ids),
                len(touched_player_ids),
            )

        return {
            "competitions": len(touched_competition_ids),
            "seasons": len(touched_season_ids),
            "venues": len(touched_venue_ids),
            "matches": len(touched_match_ids),
            "teams": len(touched_team_ids),
            "players": len(touched_player_ids),
        }

    def _extract_statsbomb_entities(self, rows: List[Dict[str, Any]], match_id: str) -> Dict[str, List[Dict[str, Any]]]:
        timestamp = datetime.now(timezone.utc).isoformat()
        competitions_by_id: Dict[str, Dict[str, Any]] = {}
        seasons_by_id: Dict[str, Dict[str, Any]] = {}
        venues_by_id: Dict[str, Dict[str, Any]] = {}
        matches_by_id: Dict[str, Dict[str, Any]] = {}
        teams_by_id: Dict[str, Dict[str, Any]] = {}
        players_by_id: Dict[str, Dict[str, Any]] = {}
        team_order: List[str] = []

        match_provider_id = self._clean_text(match_id) or str(match_id)
        competition_provider_id: Optional[str] = None
        competition_name: Optional[str] = None
        competition_country: Optional[str] = None
        season_provider_id: Optional[str] = None
        season_name: Optional[str] = None
        venue_provider_id: Optional[str] = None
        venue_name: Optional[str] = None
        venue_city: Optional[str] = None
        venue_country: Optional[str] = None
        match_date: Optional[str] = None

        for row in rows:
            if not isinstance(row, dict):
                continue

            row_competition_provider_id = self._coalesce_identifier(
                row.get("competition_id"),
                row.get("competition_name"),
            )
            row_competition_name = self._clean_text(row.get("competition_name"))
            row_season_name = self._clean_text(row.get("season_name"))
            row_season_provider_id = self._coalesce_identifier(
                row.get("season_id"),
                row_season_name,
                f"{row_competition_provider_id}:{row_season_name}" if row_competition_provider_id and row_season_name else None,
            )
            row_venue_provider_id = self._coalesce_identifier(
                row.get("venue_id"),
                row.get("stadium_id"),
                row.get("venue_name"),
                row.get("stadium_name"),
            )

            competition_provider_id = competition_provider_id or row_competition_provider_id
            competition_name = competition_name or row_competition_name
            competition_country = competition_country or self._clean_text(row.get("competition_country")) or self._clean_text(row.get("country_name"))
            season_provider_id = season_provider_id or row_season_provider_id
            season_name = season_name or row_season_name
            venue_provider_id = venue_provider_id or row_venue_provider_id
            venue_name = venue_name or self._clean_text(row.get("venue_name") or row.get("stadium_name"))
            venue_city = venue_city or self._clean_text(row.get("venue_city") or row.get("stadium_city"))
            venue_country = venue_country or self._clean_text(row.get("venue_country") or row.get("country_name"))
            match_date = match_date or self._clean_text(row.get("match_date") or row.get("kick_off") or row.get("match_date_utc"))

            if row_competition_provider_id and row_competition_name:
                self._merge_documents(
                    competitions_by_id,
                    row_competition_provider_id,
                    self._build_competition_doc(
                        provider="statsbomb",
                        provider_id=row_competition_provider_id,
                        name=row_competition_name,
                        timestamp=timestamp,
                        source_match_id=str(match_id),
                        country=self._clean_text(row.get("competition_country") or row.get("country_name")),
                        current_season_provider_id=row_season_provider_id,
                    ),
                )

            if row_season_provider_id:
                self._merge_documents(
                    seasons_by_id,
                    row_season_provider_id,
                    self._build_season_doc(
                        provider="statsbomb",
                        provider_id=row_season_provider_id,
                        name=row_season_name or str(row_season_provider_id),
                        timestamp=timestamp,
                        source_match_id=str(match_id),
                        competition_provider_id=row_competition_provider_id,
                        year=self._optional_int(row.get("season_year") or row.get("season_id")),
                    ),
                )

            if row_venue_provider_id and self._clean_text(row.get("venue_name") or row.get("stadium_name")):
                self._merge_documents(
                    venues_by_id,
                    row_venue_provider_id,
                    self._build_venue_doc(
                        provider="statsbomb",
                        provider_id=row_venue_provider_id,
                        name=self._clean_text(row.get("venue_name") or row.get("stadium_name")) or str(row_venue_provider_id),
                        timestamp=timestamp,
                        source_match_id=str(match_id),
                        city=self._clean_text(row.get("venue_city") or row.get("stadium_city")),
                        country=self._clean_text(row.get("venue_country") or row.get("country_name")),
                        capacity=self._optional_int(row.get("venue_capacity") or row.get("stadium_capacity")),
                    ),
                )

            team_provider_id = self._clean_text(row.get("team_id") or row.get("possession_team_id"))
            team_name = self._clean_text(row.get("team_name") or row.get("possession_team_name"))

            if team_provider_id and team_name:
                canonical_team_provider_id = self._canonical_id(team_provider_id)
                if canonical_team_provider_id and canonical_team_provider_id not in team_order:
                    team_order.append(canonical_team_provider_id)

                team_id = self._canonical_id(team_provider_id)
                team_doc = {
                    "uID": team_id,
                    "name": team_name,
                    "shortName": self._clean_text(row.get("team_short_name")),
                    "country": self._clean_text(row.get("country_name")),
                    "league": self._clean_text(row.get("competition_name")),
                    "competitionName": row_competition_name,
                    "seasonName": row_season_name,
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
                    "competitionName": row_competition_name,
                    "seasonName": row_season_name,
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

        if match_provider_id:
            home_team_provider_id = team_order[0] if team_order else None
            away_team_provider_id = team_order[1] if len(team_order) > 1 else None
            home_team = teams_by_id.get(home_team_provider_id or "", {})
            away_team = teams_by_id.get(away_team_provider_id or "", {})
            self._merge_documents(
                matches_by_id,
                match_provider_id,
                self._build_match_doc(
                    provider="statsbomb",
                    provider_id=match_provider_id,
                    timestamp=timestamp,
                    source_match_id=str(match_id),
                    competition_provider_id=competition_provider_id,
                    season_provider_id=season_provider_id,
                    venue_provider_id=venue_provider_id,
                    competition_name=competition_name,
                    venue_name=venue_name,
                    match_date=match_date,
                    status="finished",
                    home_team_name=home_team.get("name"),
                    away_team_name=away_team.get("name"),
                    home_team_provider_id=home_team_provider_id,
                    away_team_provider_id=away_team_provider_id,
                ),
            )

        return {
            "competitions": list(competitions_by_id.values()),
            "seasons": list(seasons_by_id.values()),
            "venues": list(venues_by_id.values()),
            "matches": list(matches_by_id.values()),
            "teams": list(teams_by_id.values()),
            "players": list(players_by_id.values()),
        }

    def _extract_opta_entities(self, raw_document: Dict[str, Any], match_id: str) -> Dict[str, List[Dict[str, Any]]]:
        soccer_feed = raw_document.get("SoccerFeed", {})
        soccer_document = soccer_feed.get("SoccerDocument", {})

        if not isinstance(soccer_document, dict):
            return {
                "competitions": [],
                "seasons": [],
                "venues": [],
                "matches": [],
                "teams": [],
                "players": [],
            }

        document_attrs = soccer_document.get("@attributes", {})
        competition_node = soccer_document.get("Competition") if isinstance(soccer_document.get("Competition"), dict) else {}
        lineup_map = self._build_lineup_map(soccer_document)
        timestamp = datetime.now(timezone.utc).isoformat()

        competitions: List[Dict[str, Any]] = []
        seasons: List[Dict[str, Any]] = []
        venues: List[Dict[str, Any]] = []
        matches: List[Dict[str, Any]] = []
        teams: List[Dict[str, Any]] = []
        players: List[Dict[str, Any]] = []
        team_names_by_provider_id: Dict[str, str] = {}

        for team_node in self._ensure_list(soccer_document.get("Team")):
            team_doc = self._build_team_doc(team_node, document_attrs, match_id, timestamp)
            if not team_doc:
                continue

            teams.append(team_doc)
            raw_team_id = self._clean_text(team_node.get("@attributes", {}).get("uID"))
            if raw_team_id and team_doc.get("name"):
                team_names_by_provider_id[raw_team_id] = team_doc["name"]

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

        competition_provider_id = self._clean_text(document_attrs.get("competition_id") or competition_node.get("@attributes", {}).get("uID"))
        competition_name = self._clean_text(document_attrs.get("competition_name") or competition_node.get("Name"))
        season_provider_id = self._clean_text(document_attrs.get("season_id") or document_attrs.get("season_name"))
        season_name = self._clean_text(document_attrs.get("season_name") or document_attrs.get("season_id"))
        match_context = self._extract_opta_match_context(soccer_document, team_names_by_provider_id)

        if competition_provider_id and competition_name:
            competitions.append(
                self._build_competition_doc(
                    provider="opta",
                    provider_id=competition_provider_id,
                    name=competition_name,
                    timestamp=timestamp,
                    source_match_id=str(match_id),
                    country=self._clean_text(competition_node.get("Country") or document_attrs.get("competition_country")),
                    current_season_provider_id=season_provider_id,
                )
            )

        if season_provider_id:
            seasons.append(
                self._build_season_doc(
                    provider="opta",
                    provider_id=season_provider_id,
                    name=season_name or str(season_provider_id),
                    timestamp=timestamp,
                    source_match_id=str(match_id),
                    competition_provider_id=competition_provider_id,
                    year=self._optional_int(document_attrs.get("season_id")),
                )
            )

        venue_provider_id = self._clean_text(match_context.get("venue_id") or match_context.get("venue_name"))
        if venue_provider_id and match_context.get("venue_name"):
            venues.append(
                self._build_venue_doc(
                    provider="opta",
                    provider_id=venue_provider_id,
                    name=match_context.get("venue_name") or str(venue_provider_id),
                    timestamp=timestamp,
                    source_match_id=str(match_id),
                    capacity=self._optional_int(match_context.get("venue_capacity")),
                )
            )

        match_provider_id = self._clean_text(document_attrs.get("uID") or match_id)
        if match_provider_id:
            matches.append(
                self._build_match_doc(
                    provider="opta",
                    provider_id=match_provider_id,
                    timestamp=timestamp,
                    source_match_id=str(match_id),
                    competition_provider_id=competition_provider_id,
                    season_provider_id=season_provider_id,
                    venue_provider_id=venue_provider_id,
                    competition_name=competition_name,
                    venue_name=match_context.get("venue_name"),
                    match_date=match_context.get("date"),
                    status=match_context.get("status") or "scheduled",
                    referee=match_context.get("referee"),
                    home_team_name=match_context.get("home_team_name"),
                    away_team_name=match_context.get("away_team_name"),
                    home_team_provider_id=match_context.get("home_team_provider_id"),
                    away_team_provider_id=match_context.get("away_team_provider_id"),
                )
            )

        return {
            "competitions": competitions,
            "seasons": seasons,
            "venues": venues,
            "matches": matches,
            "teams": teams,
            "players": players,
        }

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

    def _extract_opta_match_context(
        self,
        soccer_document: Dict[str, Any],
        team_names_by_provider_id: Dict[str, str],
    ) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "date": None,
            "status": None,
            "venue_id": None,
            "venue_name": None,
            "venue_capacity": None,
            "referee": None,
            "home_team_provider_id": None,
            "away_team_provider_id": None,
            "home_team_name": None,
            "away_team_name": None,
        }

        for match_data in self._ensure_list(soccer_document.get("MatchData")):
            if not isinstance(match_data, dict):
                continue

            match_info = match_data.get("MatchInfo") if isinstance(match_data.get("MatchInfo"), dict) else {}
            match_info_attrs = match_info.get("@attributes", {})
            context["date"] = context["date"] or self._clean_text(match_info.get("Date"))
            context["status"] = context["status"] or self._clean_text(match_info_attrs.get("Status") or match_info_attrs.get("MatchType"))
            context["venue_id"] = context["venue_id"] or self._clean_text(match_info_attrs.get("Venue_id"))
            context["venue_name"] = context["venue_name"] or self._clean_text(match_info.get("Venue"))

            match_official = match_data.get("MatchOfficial") if isinstance(match_data.get("MatchOfficial"), dict) else {}
            context["referee"] = context["referee"] or self._format_person_name(match_official.get("OfficialName"))

            for team_data in self._ensure_list(match_data.get("TeamData")):
                if not isinstance(team_data, dict):
                    continue
                attrs = team_data.get("@attributes", {})
                side = self._clean_text(attrs.get("Side"))
                team_provider_id = self._clean_text(attrs.get("TeamRef"))
                if not side or not team_provider_id:
                    continue

                if side.lower() == "home":
                    context["home_team_provider_id"] = context["home_team_provider_id"] or team_provider_id
                    context["home_team_name"] = context["home_team_name"] or team_names_by_provider_id.get(team_provider_id)
                elif side.lower() == "away":
                    context["away_team_provider_id"] = context["away_team_provider_id"] or team_provider_id
                    context["away_team_name"] = context["away_team_name"] or team_names_by_provider_id.get(team_provider_id)

        if not context["venue_name"]:
            team_stadiums = [
                self._clean_text(team.get("Stadium", {}).get("Name"))
                for team in self._ensure_list(soccer_document.get("Team"))
                if isinstance(team, dict) and isinstance(team.get("Stadium"), dict)
            ]
            context["venue_name"] = next((stadium for stadium in team_stadiums if stadium), None)

        if context["venue_name"] and not context["venue_id"]:
            context["venue_id"] = context["venue_name"]

        return context

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

    async def _upsert_competition(self, competition_doc: Dict[str, Any]) -> Dict[str, Any]:
        competition_payload = self._sanitize_document(competition_doc)
        await self._persist_provider_mapping("competition", competition_doc)
        await self.competitions_collection.update_one(
            self._document_identity_filter(competition_payload),
            {
                "$set": competition_payload,
                "$unset": {"provider": "", "providerMappings": ""},
            },
            upsert=True,
        )
        return competition_payload

    async def _upsert_season(self, season_doc: Dict[str, Any]) -> Dict[str, Any]:
        season_payload = self._sanitize_document(season_doc)
        await self._persist_provider_mapping("season", season_doc)
        await self.seasons_collection.update_one(
            self._document_identity_filter(season_payload),
            {
                "$set": season_payload,
                "$unset": {"provider": "", "providerMappings": ""},
            },
            upsert=True,
        )
        return season_payload

    async def _upsert_venue(self, venue_doc: Dict[str, Any]) -> Dict[str, Any]:
        venue_payload = self._sanitize_document(venue_doc)
        await self._persist_provider_mapping("venue", venue_doc)
        await self.venues_collection.update_one(
            self._document_identity_filter(venue_payload),
            {
                "$set": venue_payload,
                "$unset": {"provider": "", "providerMappings": ""},
            },
            upsert=True,
        )
        return venue_payload

    async def _upsert_match(self, match_doc: Dict[str, Any]) -> Dict[str, Any]:
        match_payload = self._sanitize_document(match_doc)
        await self._persist_provider_mapping("match", match_doc)
        await self.matches_collection.update_one(
            {"uID": match_payload["uID"]},
            {
                "$set": match_payload,
                "$unset": {"provider": "", "providerMappings": ""},
            },
            upsert=True,
        )
        return match_payload

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
            canonical_id=str(document.get("scoutpro_id") or document.get("id") or document["uID"]),
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
    def _coalesce_identifier(*values: Any) -> Optional[str]:
        for value in values:
            cleaned = MetadataMaterializer._clean_text(value)
            if cleaned:
                return cleaned
        return None

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
    def _document_identity_filter(document: Dict[str, Any]) -> Dict[str, Any]:
        if document.get("scoutpro_id") not in (None, ""):
            return {"scoutpro_id": document["scoutpro_id"]}
        return {"uID": document["uID"]}

    def _build_competition_doc(
        self,
        provider: str,
        provider_id: str,
        name: str,
        timestamp: str,
        source_match_id: str,
        country: Optional[str] = None,
        current_season_provider_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        scoutpro_id = ScoutProId.competition(provider, provider_id)
        return self._compact({
            "uID": provider_id,
            "scoutpro_id": scoutpro_id,
            "id": scoutpro_id,
            "provider_ids": {provider: ScoutProId.provider_numeric("competition", provider_id)},
            "name": name,
            "country": country,
            "currentSeasonID": ScoutProId.season(provider, current_season_provider_id) if current_season_provider_id else None,
            "seasonCount": 1 if current_season_provider_id else None,
            "updatedAt": timestamp,
            "sourceMatchID": source_match_id,
            "_provider_mapping": {
                "provider": provider,
                "provider_id": provider_id,
                "source_match_id": source_match_id,
                "metadata": {"competition_name": name},
            },
        })

    def _build_season_doc(
        self,
        provider: str,
        provider_id: str,
        name: str,
        timestamp: str,
        source_match_id: str,
        competition_provider_id: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        scoutpro_id = ScoutProId.season(provider, provider_id)
        return self._compact({
            "uID": provider_id,
            "scoutpro_id": scoutpro_id,
            "id": scoutpro_id,
            "provider_ids": {provider: ScoutProId.provider_numeric("season", provider_id)},
            "name": name,
            "year": year,
            "competitionID": ScoutProId.competition(provider, competition_provider_id) if competition_provider_id else None,
            "updatedAt": timestamp,
            "sourceMatchID": source_match_id,
            "_provider_mapping": {
                "provider": provider,
                "provider_id": provider_id,
                "source_match_id": source_match_id,
                "metadata": {"season_name": name},
            },
        })

    def _build_venue_doc(
        self,
        provider: str,
        provider_id: str,
        name: str,
        timestamp: str,
        source_match_id: str,
        city: Optional[str] = None,
        country: Optional[str] = None,
        capacity: Optional[int] = None,
    ) -> Dict[str, Any]:
        scoutpro_id = ScoutProId.venue(provider, provider_id)
        return self._compact({
            "uID": provider_id,
            "scoutpro_id": scoutpro_id,
            "id": scoutpro_id,
            "provider_ids": {provider: ScoutProId.provider_numeric("venue", provider_id)},
            "name": name,
            "city": city,
            "country": country,
            "capacity": capacity,
            "updatedAt": timestamp,
            "sourceMatchID": source_match_id,
            "_provider_mapping": {
                "provider": provider,
                "provider_id": provider_id,
                "source_match_id": source_match_id,
                "metadata": {"venue_name": name},
            },
        })

    def _build_match_doc(
        self,
        provider: str,
        provider_id: str,
        timestamp: str,
        source_match_id: str,
        competition_provider_id: Optional[str] = None,
        season_provider_id: Optional[str] = None,
        venue_provider_id: Optional[str] = None,
        competition_name: Optional[str] = None,
        venue_name: Optional[str] = None,
        match_date: Optional[str] = None,
        status: Optional[str] = None,
        referee: Optional[str] = None,
        home_team_name: Optional[str] = None,
        away_team_name: Optional[str] = None,
        home_team_provider_id: Optional[str] = None,
        away_team_provider_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        scoutpro_id = ScoutProId.match(provider, provider_id)
        return self._compact({
            "uID": provider_id,
            "scoutpro_id": scoutpro_id,
            "id": scoutpro_id,
            "provider_ids": {provider: ScoutProId.provider_numeric("match", provider_id)},
            "competitionID": competition_provider_id,
            "scoutpro_competition_id": ScoutProId.competition(provider, competition_provider_id) if competition_provider_id else None,
            "seasonID": season_provider_id,
            "scoutpro_season_id": ScoutProId.season(provider, season_provider_id) if season_provider_id else None,
            "venue": venue_name,
            "scoutpro_venue_id": ScoutProId.venue(provider, venue_provider_id) if venue_provider_id else None,
            "competition": competition_name,
            "date": match_date,
            "status": status,
            "referee": referee,
            "homeTeamName": home_team_name,
            "awayTeamName": away_team_name,
            "home_provider_team_id": home_team_provider_id,
            "away_provider_team_id": away_team_provider_id,
            "updatedAt": timestamp,
            "sourceMatchID": source_match_id,
            "_provider_mapping": {
                "provider": provider,
                "provider_id": provider_id,
                "source_match_id": source_match_id,
                "metadata": {
                    "competition_name": competition_name,
                    "venue_name": venue_name,
                },
            },
        })

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