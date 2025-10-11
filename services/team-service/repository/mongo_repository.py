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

    async def get_by_id(self, team_id: str) -> Optional[Team]:
        """Get team by ID from MongoDB"""
        try:
            # Try uID as int
            doc = await self.teams_collection.find_one({"uID": int(team_id)})

            if not doc:
                # Try string uID
                doc = await self.teams_collection.find_one({"uID": team_id})

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
            # Find all players for this team
            cursor = self.players_collection.find({"teamID": int(team_id)})
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
            result = await self.teams_collection.insert_one(team.dict())
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating team: {e}")
            raise

    async def update(self, team_id: str, team: Team) -> bool:
        """Update team"""
        try:
            result = await self.teams_collection.update_one(
                {'uID': int(team_id)},
                {'$set': team.dict()}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating team {team_id}: {e}")
            return False
