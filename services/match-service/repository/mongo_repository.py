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

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.matches_collection = db['matches']
        self.events_collection = db['match_events']

    async def get_by_id(self, match_id: str) -> Optional[Match]:
        """Get match by ID from MongoDB"""
        try:
            doc = await self.matches_collection.find_one({"uID": int(match_id)})

            if not doc:
                doc = await self.matches_collection.find_one({"uID": match_id})

            if not doc:
                from bson import ObjectId
                if ObjectId.is_valid(match_id):
                    doc = await self.matches_collection.find_one({"_id": ObjectId(match_id)})

            if doc:
                if '_id' in doc:
                    doc.pop('_id')
                return Match(**doc)

            return None
        except Exception as e:
            logger.error(f"Error getting match {match_id}: {e}")
            return None

    async def find_by_filters(self, filters: Dict[str, Any], limit: int = 100) -> List[Match]:
        """Find matches by filters"""
        try:
            query = {}

            if 'competition_id' in filters and filters['competition_id']:
                query['competitionID'] = int(filters['competition_id'])

            if 'season_id' in filters and filters['season_id']:
                query['seasonID'] = int(filters['season_id'])

            if 'status' in filters and filters['status']:
                query['status'] = filters['status']

            if 'team_id' in filters and filters['team_id']:
                team_id = int(filters['team_id'])
                query['$or'] = [
                    {'homeTeamID': team_id},
                    {'awayTeamID': team_id}
                ]

            cursor = self.matches_collection.find(query).limit(limit).sort('date', -1)
            docs = await cursor.to_list(length=limit)

            matches = []
            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')
                try:
                    matches.append(Match(**doc))
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
            team_id_int = int(team_id)
            query = {
                '$or': [
                    {'homeTeamID': team_id_int},
                    {'awayTeamID': team_id_int}
                ]
            }

            cursor = self.matches_collection.find(query).limit(limit).sort('date', -1)
            docs = await cursor.to_list(length=limit)

            matches = []
            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')
                try:
                    matches.append(Match(**doc))
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

            matches = []
            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')
                try:
                    matches.append(Match(**doc))
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

            matches = []
            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')
                try:
                    matches.append(Match(**doc))
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
            query = {'matchID': int(match_id)}

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
            result = await self.matches_collection.insert_one(match.dict())
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating match: {e}")
            raise

    async def update(self, match_id: str, match: Match) -> bool:
        """Update match"""
        try:
            result = await self.matches_collection.update_one(
                {'uID': int(match_id)},
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
                {'uID': int(match_id)},
                {'$set': live_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating live data for match {match_id}: {e}")
            return False
