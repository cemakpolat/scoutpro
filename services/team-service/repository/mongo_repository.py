"""
MongoDB implementation of Team Repository
"""
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .interfaces import ITeamRepository
import sys
sys.path.append('/app')
from shared.models.base import Team
import logging

logger = logging.getLogger(__name__)


class MongoTeamRepository(ITeamRepository):
    """MongoDB implementation of team repository"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.teams_collection = db['teams']
        self.players_collection = db['players']

    @staticmethod
    def _collect_identifier_variants(value: Any, prefix: str = 't') -> tuple[list[str], list[int]]:
        string_values: list[str] = []
        numeric_values: list[int] = []

        if value in (None, ''):
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
    def _build_team_lookup_query(cls, team_id: str) -> Dict[str, Any]:
        string_values, numeric_values = cls._collect_identifier_variants(team_id)
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

    async def _resolve_team_doc(self, team_id: str) -> Optional[Dict[str, Any]]:
        return await self.teams_collection.find_one(self._build_team_lookup_query(team_id))

    @classmethod
    def _expand_team_variants_from_doc(
        cls,
        team_id: str,
        team_doc: Optional[Dict[str, Any]],
    ) -> tuple[list[str], list[int]]:
        string_values: list[str] = []
        numeric_values: list[int] = []

        def extend(candidate: Any) -> None:
            strings, numbers = cls._collect_identifier_variants(candidate)
            for value in strings:
                if value not in string_values:
                    string_values.append(value)
            for value in numbers:
                if value not in numeric_values:
                    numeric_values.append(value)

        extend(team_id)
        if team_doc:
            extend(team_doc.get('uID'))
            extend(team_doc.get('id'))
            extend(team_doc.get('scoutpro_id'))
            extend((team_doc.get('provider_ids') or {}).get('opta'))

        return string_values, numeric_values

    async def get_by_id(self, team_id: str) -> Optional[Team]:
        """Get team by ID from MongoDB"""
        try:
            doc = await self._resolve_team_doc(team_id)

            if not doc:
                # Try _id field
                from bson import ObjectId
                if ObjectId.is_valid(team_id):
                    doc = await self.teams_collection.find_one({"_id": ObjectId(team_id)})

            if doc:
                if '_id' in doc:
                    doc.pop('_id')
                return Team(**doc)

            return None
        except Exception as e:
            logger.error(f"Error getting team {team_id}: {e}")
            return None

    async def find_by_filters(self, filters: Dict[str, Any], limit: int = 100) -> List[Team]:
        """Find teams by filters"""
        try:
            query = {}

            if 'country' in filters and filters['country']:
                query['country'] = filters['country']

            if 'league' in filters and filters['league']:
                query['league'] = filters['league']

            if 'competition_id' in filters and filters['competition_id']:
                query['competitionID'] = int(filters['competition_id'])

            cursor = self.teams_collection.find(query).limit(limit)
            docs = await cursor.to_list(length=limit)

            teams = []
            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')
                try:
                    teams.append(Team(**doc))
                except Exception as e:
                    logger.warning(f"Skipping invalid team doc: {e}")
                    continue

            return teams
        except Exception as e:
            logger.error(f"Error finding teams: {e}")
            return []

    async def search(self, query: str, limit: int = 20) -> List[Team]:
        """Search teams by name"""
        try:
            search_filter = {
                '$or': [
                    {'name': {'$regex': query, '$options': 'i'}},
                    {'shortName': {'$regex': query, '$options': 'i'}}
                ]
            }

            cursor = self.teams_collection.find(search_filter).limit(limit)
            docs = await cursor.to_list(length=limit)

            teams = []
            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')
                try:
                    teams.append(Team(**doc))
                except Exception as e:
                    logger.warning(f"Skipping invalid team doc: {e}")
                    continue

            return teams
        except Exception as e:
            logger.error(f"Error searching teams: {e}")
            return []

    async def get_squad(self, team_id: str) -> List[Dict[str, Any]]:
        """Get team squad (list of players)"""
        try:
            team_doc = await self._resolve_team_doc(team_id)
            string_values, numeric_values = self._expand_team_variants_from_doc(team_id, team_doc)

            or_clauses: List[Dict[str, Any]] = []
            for field in ('team_id', 'current_team_id', 'teamID'):
                if string_values:
                    or_clauses.append({field: {'$in': string_values}})
                if numeric_values:
                    or_clauses.append({field: {'$in': numeric_values}})

            query = {'$or': or_clauses} if or_clauses else {'teamID': team_id}
            cursor = self.players_collection.find(query)
            docs = await cursor.to_list(length=None)

            squad = []
            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')
                squad.append(doc)

            return squad
        except Exception as e:
            logger.error(f"Error getting squad for team {team_id}: {e}")
            return []

    async def create(self, team: Team) -> str:
        """Create new team"""
        try:
            await self.teams_collection.insert_one(team.dict(by_alias=True))
            return str(team.id)
        except Exception as e:
            logger.error(f"Error creating team: {e}")
            raise

    async def update(self, team_id: str, team: Team) -> bool:
        """Update team"""
        try:
            team_doc = await self._resolve_team_doc(team_id)
            if not team_doc or '_id' not in team_doc:
                return False

            result = await self.teams_collection.update_one(
                {'_id': team_doc['_id']},
                {'$set': team.dict()}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating team {team_id}: {e}")
            return False
