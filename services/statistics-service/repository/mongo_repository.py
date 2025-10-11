"""
MongoDB implementation of Statistics Repository
"""
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from .interfaces import IStatisticsRepository
import sys
sys.path.append('/app')
from shared.models.base import PlayerStatistics
import logging

logger = logging.getLogger(__name__)


class MongoStatisticsRepository(IStatisticsRepository):
    """MongoDB implementation of statistics repository"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.player_stats_collection = db['player_statistics']
        self.player_stats_per90_collection = db['player_statistics_per90']
        self.team_stats_collection = db['team_statistics']

    async def get_player_statistics(
        self,
        player_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
        per_90: bool = False
    ) -> Optional[PlayerStatistics]:
        """Get player statistics"""
        try:
            query = {'playerID': int(player_id)}

            if competition_id:
                query['competitionID'] = competition_id
            if season_id:
                query['seasonID'] = season_id

            collection = self.player_stats_per90_collection if per_90 else self.player_stats_collection
            doc = await collection.find_one(query)

            if doc:
                if '_id' in doc:
                    doc.pop('_id')
                return PlayerStatistics(
                    player_id=player_id,
                    stats=doc
                )

            return None
        except Exception as e:
            logger.error(f"Error getting player statistics: {e}")
            return None

    async def get_team_statistics(
        self,
        team_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get team statistics"""
        try:
            query = {'teamID': int(team_id)}

            if competition_id:
                query['competitionID'] = competition_id
            if season_id:
                query['seasonID'] = season_id

            doc = await self.team_stats_collection.find_one(query)

            if doc:
                if '_id' in doc:
                    doc.pop('_id')
                return doc

            return None
        except Exception as e:
            logger.error(f"Error getting team statistics: {e}")
            return None

    async def get_player_rankings(
        self,
        stat_name: str,
        position: Optional[str] = None,
        competition_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get player rankings by statistic"""
        try:
            query = {}

            if position:
                # Need to join with players collection
                pass

            if competition_id:
                query['competitionID'] = competition_id

            # Sort by stat_name descending
            cursor = self.player_stats_collection.find(query).sort(stat_name, -1).limit(limit)
            docs = await cursor.to_list(length=limit)

            rankings = []
            for idx, doc in enumerate(docs, 1):
                if '_id' in doc:
                    doc.pop('_id')
                doc['rank'] = idx
                rankings.append(doc)

            return rankings
        except Exception as e:
            logger.error(f"Error getting player rankings: {e}")
            return []

    async def get_team_rankings(
        self,
        stat_name: str,
        competition_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get team rankings by statistic"""
        try:
            query = {}

            if competition_id:
                query['competitionID'] = competition_id

            cursor = self.team_stats_collection.find(query).sort(stat_name, -1).limit(limit)
            docs = await cursor.to_list(length=limit)

            rankings = []
            for idx, doc in enumerate(docs, 1):
                if '_id' in doc:
                    doc.pop('_id')
                doc['rank'] = idx
                rankings.append(doc)

            return rankings
        except Exception as e:
            logger.error(f"Error getting team rankings: {e}")
            return []

    async def get_player_comparison(
        self,
        player_ids: List[str],
        stat_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple players"""
        try:
            player_ids_int = [int(pid) for pid in player_ids]
            query = {'playerID': {'$in': player_ids_int}}

            cursor = self.player_stats_collection.find(query)
            docs = await cursor.to_list(length=len(player_ids))

            comparison = {
                'players': []
            }

            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')

                # Filter to specific categories if requested
                if stat_categories:
                    filtered_doc = {k: v for k, v in doc.items() if k in stat_categories or k == 'playerID'}
                    comparison['players'].append(filtered_doc)
                else:
                    comparison['players'].append(doc)

            return comparison
        except Exception as e:
            logger.error(f"Error comparing players: {e}")
            return {'players': []}

    async def aggregate_player_stats(
        self,
        player_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Aggregate player stats over time period"""
        try:
            # This would typically use TimescaleDB for time-series aggregation
            # For now, simple MongoDB query
            query = {
                'playerID': int(player_id),
                'date': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            }

            cursor = self.player_stats_collection.find(query)
            docs = await cursor.to_list(length=None)

            if not docs:
                return {}

            # Simple aggregation - sum numeric fields
            aggregated = {}
            for doc in docs:
                for key, value in doc.items():
                    if key in ['_id', 'playerID', 'date']:
                        continue
                    if isinstance(value, (int, float)):
                        aggregated[key] = aggregated.get(key, 0) + value

            return aggregated
        except Exception as e:
            logger.error(f"Error aggregating player stats: {e}")
            return {}
