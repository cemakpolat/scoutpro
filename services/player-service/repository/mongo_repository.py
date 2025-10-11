"""
MongoDB implementation of Player Repository
"""
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .interfaces import IPlayerRepository
import sys
sys.path.append('/app')
from shared.models.base import Player, PlayerStatistics
import logging

logger = logging.getLogger(__name__)


class MongoPlayerRepository(IPlayerRepository):
    """MongoDB implementation of player repository"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.players_collection = db['players']
        self.stats_collection = db['player_statistics']

    async def get_by_id(self, player_id: str) -> Optional[Player]:
        """Get player by ID from MongoDB"""
        try:
            # Try direct uID field
            doc = await self.players_collection.find_one({"uID": int(player_id)})

            if not doc:
                # Try string uID
                doc = await self.players_collection.find_one({"uID": player_id})

            if not doc:
                # Try _id field
                from bson import ObjectId
                if ObjectId.is_valid(player_id):
                    doc = await self.players_collection.find_one({"_id": ObjectId(player_id)})

            if doc:
                # Clean up the document
                if '_id' in doc:
                    doc.pop('_id')
                return Player(**doc)

            return None
        except Exception as e:
            logger.error(f"Error getting player {player_id}: {e}")
            return None

    async def find_by_filters(self, filters: Dict[str, Any], limit: int = 100) -> List[Player]:
        """Find players by filters"""
        try:
            query = {}

            if 'position' in filters and filters['position']:
                if isinstance(filters['position'], list):
                    query['position'] = {'$in': filters['position']}
                else:
                    query['position'] = filters['position']

            if 'club' in filters and filters['club']:
                if isinstance(filters['club'], list):
                    query['club'] = {'$in': filters['club']}
                else:
                    query['club'] = filters['club']

            if 'age_min' in filters and filters['age_min']:
                query.setdefault('age', {})['$gte'] = filters['age_min']

            if 'age_max' in filters and filters['age_max']:
                query.setdefault('age', {})['$lte'] = filters['age_max']

            cursor = self.players_collection.find(query).limit(limit)
            docs = await cursor.to_list(length=limit)

            players = []
            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')
                try:
                    players.append(Player(**doc))
                except Exception as e:
                    logger.warning(f"Skipping invalid player doc: {e}")
                    continue

            return players
        except Exception as e:
            logger.error(f"Error finding players: {e}")
            return []

    async def search(self, query: str, limit: int = 20) -> List[Player]:
        """Search players by name"""
        try:
            search_filter = {
                '$or': [
                    {'name': {'$regex': query, '$options': 'i'}},
                    {'first': {'$regex': query, '$options': 'i'}},
                    {'last': {'$regex': query, '$options': 'i'}}
                ]
            }

            cursor = self.players_collection.find(search_filter).limit(limit)
            docs = await cursor.to_list(length=limit)

            players = []
            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')
                try:
                    players.append(Player(**doc))
                except Exception as e:
                    logger.warning(f"Skipping invalid player doc: {e}")
                    continue

            return players
        except Exception as e:
            logger.error(f"Error searching players: {e}")
            return []

    async def get_statistics(
        self,
        player_id: str,
        stat_type: Optional[str] = None,
        per_90: bool = False
    ) -> Optional[PlayerStatistics]:
        """Get player statistics"""
        try:
            query = {'playerID': int(player_id)}

            collection_name = 'player_statistics'
            if per_90:
                collection_name = 'player_statistics_per90'

            doc = await self.db[collection_name].find_one(query)

            if doc:
                if '_id' in doc:
                    doc.pop('_id')

                # Extract stats based on type
                stats = {}
                if stat_type:
                    # Get specific stat type (e.g., 'shotEvent', 'passEvent')
                    if stat_type in doc:
                        stats_ref = doc[stat_type]
                        if stats_ref:
                            # Dereference if it's a DBRef
                            stat_doc = await self.db[stat_type.lower()].find_one({'_id': stats_ref.id})
                            if stat_doc:
                                if '_id' in stat_doc:
                                    stat_doc.pop('_id')
                                stats = stat_doc
                else:
                    # Get all stats
                    stats = doc

                return PlayerStatistics(
                    player_id=player_id,
                    player_name=doc.get('playerName'),
                    competition_id=doc.get('competitionID'),
                    season_id=doc.get('seasonID'),
                    stats=stats
                )

            return None
        except Exception as e:
            logger.error(f"Error getting statistics for player {player_id}: {e}")
            return None

    async def create(self, player: Player) -> str:
        """Create new player"""
        try:
            result = await self.players_collection.insert_one(player.dict())
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating player: {e}")
            raise

    async def update(self, player_id: str, player: Player) -> bool:
        """Update player"""
        try:
            result = await self.players_collection.update_one(
                {'uID': int(player_id)},
                {'$set': player.dict()}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating player {player_id}: {e}")
            return False
