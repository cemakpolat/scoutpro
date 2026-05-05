"""
MongoDB implementation of Match Repository
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .interfaces import IMatchRepository
import sys
sys.path.append('/app')
from shared.models.base import Match
import logging

logger = logging.getLogger(__name__)


class MongoMatchRepository(IMatchRepository):
    """MongoDB implementation of match repository"""

    @staticmethod
    def _extract_date_text(value: Any) -> Optional[str]:
        if isinstance(value, dict):
            raw_value = value.get('@value')
            return str(raw_value) if raw_value else None

        if value is None:
            return None

        return str(value)

    @staticmethod
    def _parse_match_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None

        normalized = value.replace('Z', '+00:00')
        for candidate in (normalized, normalized.replace(' ', 'T')):
            try:
                parsed = datetime.fromisoformat(candidate)
                return parsed.replace(tzinfo=None) if parsed.tzinfo is not None else parsed
            except ValueError:
                continue

        return None

    @classmethod
    def _normalize_live_status(
        cls,
        raw_status: str,
        date_text: Optional[str],
        raw_home_score: Any,
        raw_away_score: Any,
    ) -> str:
        if raw_status != 'live':
            return raw_status

        parsed_date = cls._parse_match_datetime(date_text)
        if not parsed_date:
            return 'live'

        # Historical/offline fixtures should not be surfaced as live just because
        # the stored Opta status never transitioned after ingestion.
        age_in_hours = (datetime.utcnow() - parsed_date).total_seconds() / 3600
        if age_in_hours <= 8:
            return 'live'

        if raw_home_score is None and raw_away_score is None:
            return 'scheduled'

        return 'finished'

    @classmethod
    def _match_quality_score(cls, doc: Dict[str, Any]) -> int:
        score = 0

        for field in ('homeTeamID', 'awayTeamID', 'competitionID', 'seasonID'):
            value = doc.get(field)
            if value not in (None, '', 0, '0'):
                score += 2

        for field in ('homeTeamName', 'awayTeamName', 'venue', 'competition'):
            if doc.get(field):
                score += 4

        for field in ('homeScore', 'awayScore'):
            if doc.get(field) is not None:
                score += 1

        status = str(doc.get('status', '')).lower()
        if status == 'finished':
            score += 2
        elif status == 'live':
            score += 1

        if cls._parse_match_datetime(cls._extract_date_text(doc.get('date'))):
            score += 1

        return score

    @classmethod
    def _select_best_docs(cls, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        best_by_id: Dict[str, Dict[str, Any]] = {}

        for doc in docs:
            normalized_id = str(doc.get('uID'))
            current_best = best_by_id.get(normalized_id)
            if not current_best or cls._match_quality_score(doc) > cls._match_quality_score(current_best):
                best_by_id[normalized_id] = doc

        return sorted(
            best_by_id.values(),
            key=lambda doc: cls._parse_match_datetime(cls._extract_date_text(doc.get('date'))) or datetime.min,
            reverse=True,
        )

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.matches_collection = db['matches']
        self.events_collection = db['match_events']
        self.teams_collection = db['teams']
        self._team_name_cache: Dict[str, Optional[str]] = {}

    @staticmethod
    def _collect_identifier_variants(value: Any, prefix: str = '') -> tuple[list[str], list[int]]:
        string_values: list[str] = []
        numeric_values: list[int] = []

        if value in (None, '', 0, '0'):
            return string_values, numeric_values

        raw_value = str(value).strip()
        if not raw_value:
            return string_values, numeric_values

        def add_string(candidate: str) -> None:
            if candidate and candidate not in string_values:
                string_values.append(candidate)

        def add_number(candidate: int) -> None:
            if candidate not in numeric_values:
                numeric_values.append(candidate)

        add_string(raw_value)

        stripped_value = raw_value
        if prefix and raw_value.lower().startswith(prefix.lower()):
            stripped_value = raw_value[1:]
            add_string(stripped_value)

        if stripped_value.isdigit():
            add_number(int(stripped_value))
            if prefix:
                add_string(f'{prefix}{stripped_value}')

        return string_values, numeric_values

    @classmethod
    def _build_team_lookup_query(cls, team_id: Any) -> Dict[str, Any]:
        string_values, numeric_values = cls._collect_identifier_variants(team_id, prefix='t')
        or_clauses: List[Dict[str, Any]] = []

        if string_values:
            or_clauses.extend([
                {'uID': {'$in': string_values}},
                {'provider_ids.opta': {'$in': string_values}},
                {'id': {'$in': string_values}},
                {'scoutpro_id': {'$in': string_values}},
            ])
        if numeric_values:
            or_clauses.extend([
                {'id': {'$in': numeric_values}},
                {'scoutpro_id': {'$in': numeric_values}},
            ])

        return {'$or': or_clauses} if or_clauses else {'uID': str(team_id)}

    @classmethod
    def _build_match_lookup_query(cls, match_id: str) -> Dict[str, Any]:
        string_values, numeric_values = cls._collect_identifier_variants(match_id, prefix='g')
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

        return {'$or': or_clauses} if or_clauses else {'uID': str(match_id)}

    @classmethod
    def _build_match_team_query(cls, team_id: str) -> Dict[str, Any]:
        string_values, numeric_values = cls._collect_identifier_variants(team_id, prefix='t')
        or_clauses: List[Dict[str, Any]] = []

        for field in (
            'homeTeamID',
            'awayTeamID',
            'home_team_id',
            'away_team_id',
            'home_team_ref',
            'away_team_ref',
            'home_opta_team_id',
            'away_opta_team_id',
        ):
            if string_values:
                or_clauses.append({field: {'$in': string_values}})
            if numeric_values:
                or_clauses.append({field: {'$in': numeric_values}})

        return {'$or': or_clauses} if or_clauses else {'homeTeamID': str(team_id)}

    @classmethod
    def _build_event_match_query(cls, match_id: str) -> Dict[str, Any]:
        string_values, numeric_values = cls._collect_identifier_variants(match_id, prefix='g')
        or_clauses: List[Dict[str, Any]] = []

        for field in ('matchID', 'match_id', 'scoutpro_match_id'):
            if string_values:
                or_clauses.append({field: {'$in': string_values}})
            if numeric_values:
                or_clauses.append({field: {'$in': numeric_values}})

        return {'$or': or_clauses} if or_clauses else {'matchID': str(match_id)}

    @staticmethod
    def _normalize_team_id(value: Any) -> Optional[str]:
        if value in (None, '', 0, '0'):
            return None

        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _first_non_empty_text(*values: Any) -> Optional[str]:
        for value in values:
            if value is None:
                continue

            text = str(value).strip()
            if text:
                return text

        return None

    async def _resolve_team_name_from_metadata(self, team_id: Any) -> Optional[str]:
        normalized_team_id = self._normalize_team_id(team_id)
        if not normalized_team_id:
            return None

        if normalized_team_id in self._team_name_cache:
            return self._team_name_cache[normalized_team_id]

        team_doc = await self.teams_collection.find_one(
            self._build_team_lookup_query(normalized_team_id),
            {'_id': 0, 'name': 1, 'shortName': 1, 'uID': 1, 'id': 1, 'scoutpro_id': 1, 'provider_ids': 1},
        )
        team_name = self._first_non_empty_text(
            team_doc.get('name') if team_doc else None,
            team_doc.get('shortName') if team_doc else None,
        )

        if not team_name:
            team_string_values, team_numeric_values = self._collect_identifier_variants(normalized_team_id, prefix='t')
            if team_doc:
                for candidate in (
                    team_doc.get('uID'),
                    team_doc.get('id'),
                    team_doc.get('scoutpro_id'),
                    (team_doc.get('provider_ids') or {}).get('opta'),
                ):
                    strings, numbers = self._collect_identifier_variants(candidate, prefix='t')
                    for value in strings:
                        if value not in team_string_values:
                            team_string_values.append(value)
                    for value in numbers:
                        if value not in team_numeric_values:
                            team_numeric_values.append(value)

            def side_matches(match_doc: Dict[str, Any], fields: List[str]) -> bool:
                for field in fields:
                    field_value = match_doc.get(field)
                    if field_value in (None, ''):
                        continue

                    text_value = str(field_value).strip()
                    if text_value in team_string_values:
                        return True

                    if text_value.isdigit() and int(text_value) in team_numeric_values:
                        return True

                return False

            named_docs = await self.matches_collection.find(
                self._build_match_team_query(normalized_team_id),
                {
                    '_id': 0,
                    'homeTeamID': 1,
                    'awayTeamID': 1,
                    'home_team_id': 1,
                    'away_team_id': 1,
                    'home_team_ref': 1,
                    'away_team_ref': 1,
                    'home_opta_team_id': 1,
                    'away_opta_team_id': 1,
                    'homeTeamName': 1,
                    'awayTeamName': 1,
                    'home_team': 1,
                    'away_team': 1,
                    'date': 1,
                },
            ).sort('date', -1).to_list(length=5)

            for match_doc in named_docs:
                if side_matches(match_doc, ['homeTeamID', 'home_team_id', 'home_team_ref', 'home_opta_team_id']):
                    team_name = self._first_non_empty_text(
                        match_doc.get('homeTeamName'),
                        match_doc.get('home_team'),
                    )
                elif side_matches(match_doc, ['awayTeamID', 'away_team_id', 'away_team_ref', 'away_opta_team_id']):
                    team_name = self._first_non_empty_text(
                        match_doc.get('awayTeamName'),
                        match_doc.get('away_team'),
                    )

                if team_name:
                    break

        self._team_name_cache[normalized_team_id] = team_name
        return team_name

    async def _enrich_match_team_names(self, normalized_doc: Dict[str, Any]) -> Dict[str, Any]:
        home_team_name = self._first_non_empty_text(normalized_doc.get('homeTeamName'))
        if not home_team_name:
            home_team_name = await self._resolve_team_name_from_metadata(normalized_doc.get('homeTeamID'))
            if home_team_name:
                normalized_doc['homeTeamName'] = home_team_name

        away_team_name = self._first_non_empty_text(normalized_doc.get('awayTeamName'))
        if not away_team_name:
            away_team_name = await self._resolve_team_name_from_metadata(normalized_doc.get('awayTeamID'))
            if away_team_name:
                normalized_doc['awayTeamName'] = away_team_name

        return normalized_doc

    async def get_by_id(self, match_id: str) -> Optional[Match]:
        """Get match by ID from MongoDB"""
        try:
            docs = await self.matches_collection.find(self._build_match_lookup_query(match_id)).to_list(length=10)
            selected_docs = self._select_best_docs(docs)
            doc = selected_docs[0] if selected_docs else None

            if not doc:
                from bson import ObjectId
                if ObjectId.is_valid(match_id):
                    doc = await self.matches_collection.find_one({"_id": ObjectId(match_id)})

            if doc:
                normalized_doc = await self._enrich_match_team_names(self._normalize_match_doc(doc))
                return Match(**normalized_doc)

            return None
        except Exception as e:
            logger.error(f"Error getting match {match_id}: {e}")
            return None

    async def find_by_filters(self, filters: Dict[str, Any], limit: int = 100) -> List[Match]:
        """Find matches by filters"""
        try:
            query = {}

            if 'competition_id' in filters and filters['competition_id']:
                # competitionID may be stored as string ('c115') or int; accept both
                cid = filters['competition_id']
                try:
                    query['competitionID'] = {'$in': [str(cid), int(cid)]}
                except (ValueError, TypeError):
                    query['competitionID'] = str(cid)

            if 'season_id' in filters and filters['season_id']:
                sid = filters['season_id']
                try:
                    query['seasonID'] = {'$in': [str(sid), int(sid)]}
                except (ValueError, TypeError):
                    query['seasonID'] = str(sid)

            if 'status' in filters and filters['status']:
                query['status'] = filters['status']

            if 'team_id' in filters and filters['team_id']:
                query['$or'] = self._build_match_team_query(filters['team_id'])['$or']

            cursor = self.matches_collection.find(query).limit(limit).sort('date', -1)
            docs = await cursor.to_list(length=limit)
            docs = self._select_best_docs(docs)

            matches = []
            for doc in docs:
                try:
                    matches.append(Match(**self._normalize_match_doc(doc)))
                except Exception as e:
                    logger.warning(f"Skipping invalid match doc: {e}")
                    continue

            return matches
        except Exception as e:
            logger.error(f"Error finding matches: {e}")
            return []

    async def get_by_team(self, team_id: str, limit: int = 20) -> List[Match]:
        """Get matches for a team"""
        try:
            query = self._build_match_team_query(team_id)

            cursor = self.matches_collection.find(query).limit(limit).sort('date', -1)
            docs = await cursor.to_list(length=limit)
            docs = self._select_best_docs(docs)

            matches = []
            for doc in docs:
                try:
                    matches.append(Match(**self._normalize_match_doc(doc)))
                except Exception as e:
                    logger.warning(f"Skipping invalid match doc: {e}")
                    continue

            return matches
        except Exception as e:
            logger.error(f"Error getting matches for team {team_id}: {e}")
            return []

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[Match]:
        """Get matches in date range"""
        try:
            query = {
                'date': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            }

            cursor = self.matches_collection.find(query).limit(limit).sort('date', 1)
            docs = await cursor.to_list(length=limit)
            docs = self._select_best_docs(docs)

            matches = []
            for doc in docs:
                try:
                    matches.append(Match(**self._normalize_match_doc(doc)))
                except Exception as e:
                    logger.warning(f"Skipping invalid match doc: {e}")
                    continue

            return matches
        except Exception as e:
            logger.error(f"Error getting matches by date range: {e}")
            return []

    async def get_live_matches(self) -> List[Match]:
        """Get currently live matches"""
        try:
            query = {'status': 'live'}

            cursor = self.matches_collection.find(query)
            docs = await cursor.to_list(length=None)

            recent_live_sources: Dict[str, Dict[str, Any]] = {}
            for doc in docs:
                if str(doc.get('status', '')).lower() != 'live':
                    continue

                parsed_date = self._parse_match_datetime(self._extract_date_text(doc.get('date')))
                if parsed_date is not None:
                    age_in_hours = (datetime.utcnow() - parsed_date).total_seconds() / 3600
                    if age_in_hours > 48:
                        continue

                normalized_id = str(doc.get('uID', '')).strip()
                if not normalized_id:
                    continue

                current_source = recent_live_sources.get(normalized_id)
                if not current_source:
                    recent_live_sources[normalized_id] = doc
                    continue

                current_date = self._parse_match_datetime(self._extract_date_text(current_source.get('date')))
                if parsed_date and (current_date is None or parsed_date > current_date):
                    recent_live_sources[normalized_id] = doc

            if not recent_live_sources:
                return []

            candidate_ids: List[Any] = []
            for match_id in recent_live_sources:
                candidate_ids.append(match_id)
                if match_id.isdigit():
                    candidate_ids.append(int(match_id))

            docs = await self.matches_collection.find({'uID': {'$in': candidate_ids}}).to_list(length=None)
            docs_by_id: Dict[str, List[Dict[str, Any]]] = {}
            for doc in docs:
                normalized_id = str(doc.get('uID', '')).strip()
                if not normalized_id:
                    continue
                docs_by_id.setdefault(normalized_id, []).append(doc)

            matches = []
            for match_id, source_doc in recent_live_sources.items():
                try:
                    selected_docs = self._select_best_docs(docs_by_id.get(match_id, [source_doc]))
                    selected_doc = selected_docs[0] if selected_docs else source_doc

                    source_date = self._parse_match_datetime(self._extract_date_text(source_doc.get('date')))
                    selected_date = self._parse_match_datetime(self._extract_date_text(selected_doc.get('date')))

                    if source_date and selected_date:
                        diff_hours = abs((selected_date - source_date).total_seconds()) / 3600
                        if diff_hours > 24:
                            fallback_doc = self._normalize_match_doc(source_doc)
                            home_team_id = fallback_doc.get('homeTeamID')
                            away_team_id = fallback_doc.get('awayTeamID')
                            if home_team_id in (None, '', '0', 0) or away_team_id in (None, '', '0', 0):
                                continue
                            selected_doc = source_doc

                    normalized_doc = await self._enrich_match_team_names(self._normalize_match_doc(selected_doc))
                    normalized_doc['status'] = 'live'
                    matches.append(Match(**normalized_doc))
                except Exception as e:
                    logger.warning(f"Skipping invalid match doc: {e}")
                    continue

            return matches
        except Exception as e:
            logger.error(f"Error getting live matches: {e}")
            return []

    async def get_match_events(self, match_id: str) -> List[Dict[str, Any]]:
        """Get all events for a match"""
        try:
            query = self._build_event_match_query(match_id)

            cursor = self.events_collection.find(query).sort('timestamp', 1)
            docs = await cursor.to_list(length=None)

            events = []
            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')
                events.append(doc)

            return events
        except Exception as e:
            logger.error(f"Error getting events for match {match_id}: {e}")
            return []

    async def create(self, match: Match) -> str:
        """Create new match"""
        try:
            await self.matches_collection.insert_one(match.dict(by_alias=True))
            return str(match.id)
        except Exception as e:
            logger.error(f"Error creating match: {e}")
            raise

    async def update(self, match_id: str, match: Match) -> bool:
        """Update match"""
        try:
            result = await self.matches_collection.update_one(
                self._build_match_lookup_query(match_id),
                {'$set': match.dict()}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating match {match_id}: {e}")
            return False

    async def update_live_data(self, match_id: str, live_data: Dict[str, Any]) -> bool:
        """Update live match data"""
        try:
            result = await self.matches_collection.update_one(
                self._build_match_lookup_query(match_id),
                {'$set': live_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating live data for match {match_id}: {e}")
            return False

    @staticmethod
    def _normalize_match_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(doc)
        normalized.pop('_id', None)
        normalized.pop('f9_summary', None)  # strip heavy blob

        field_aliases = {
            'home_team': 'homeTeamName',
            'away_team': 'awayTeamName',
            'home_team_id': 'homeTeamID',
            'away_team_id': 'awayTeamID',
            'home_score': 'homeScore',
            'away_score': 'awayScore',
        }
        for source_field, target_field in field_aliases.items():
            if target_field not in normalized and normalized.get(source_field) is not None:
                normalized[target_field] = normalized[source_field]

        raw_home_score = normalized.get('homeScore')
        raw_away_score = normalized.get('awayScore')

        for field in ('uID', 'homeTeamID', 'awayTeamID'):
            if field in normalized and normalized[field] is not None:
                normalized[field] = str(normalized[field])

        # Ensure scores are always integers, never None
        for score_field in ('homeScore', 'awayScore'):
            val = normalized.get(score_field)
            try:
                normalized[score_field] = int(val) if val is not None else 0
            except (TypeError, ValueError):
                normalized[score_field] = 0

        date_text = MongoMatchRepository._extract_date_text(normalized.get('date'))
        if date_text is not None:
            normalized['date'] = date_text

        # Normalise status to frontend expected values
        raw_status = str(normalized.get('status', '')).lower()
        if raw_status in ('played', 'finished'):
            normalized['status'] = 'finished'
        elif raw_status in ('fixture', 'scheduled', ''):
            normalized['status'] = 'scheduled'
        else:
            normalized['status'] = MongoMatchRepository._normalize_live_status(
                raw_status,
                date_text,
                raw_home_score,
                raw_away_score,
            )

        # Ensure competitionID and seasonID are strings (stored as 'c115', not int)
        for field in ('competitionID', 'seasonID'):
            val = normalized.get(field)
            if val is not None:
                normalized[field] = str(val)

        return normalized
