"""
Statistics Service - Business Logic Layer
"""
from typing import Optional, List, Dict, Any
import json
import logging
from redis import Redis
from aiokafka import AIOKafkaProducer
import sys
sys.path.append('/app')
from shared.models.base import PlayerStatistics
from repository.interfaces import IStatisticsRepository

logger = logging.getLogger(__name__)


class StatisticsService:
    """Statistics service with caching and aggregation"""

    def __init__(
        self,
        repository: IStatisticsRepository,
        redis_client: Redis,
        kafka_producer: Optional[AIOKafkaProducer] = None,
        cache_ttl: int = 180
    ):
        self.repository = repository
        self.redis = redis_client
        self.kafka = kafka_producer
        self.cache_ttl = cache_ttl

    async def get_player_statistics(
        self,
        player_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
        per_90: bool = False
    ) -> Optional[PlayerStatistics]:
        """Get player statistics with caching"""
        try:
            cache_key = f"stats:player:{player_id}:{competition_id}:{season_id}:{per_90}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for player {player_id} statistics")
                return PlayerStatistics(**json.loads(cached))

            stats = await self.repository.get_player_statistics(
                player_id,
                competition_id,
                season_id,
                per_90
            )

            if stats:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    stats.json()
                )

            return stats
        except Exception as e:
            logger.error(f"Error in get_player_statistics: {e}")
            raise

    async def get_team_statistics(
        self,
        team_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get team statistics with caching"""
        try:
            cache_key = f"stats:team:{team_id}:{competition_id}:{season_id}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for team {team_id} statistics")
                return json.loads(cached)

            stats = await self.repository.get_team_statistics(
                team_id,
                competition_id,
                season_id
            )

            if stats:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(stats)
                )

            return stats
        except Exception as e:
            logger.error(f"Error in get_team_statistics: {e}")
            raise

    async def get_player_rankings(
        self,
        stat_name: str,
        position: Optional[str] = None,
        competition_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get player rankings with caching"""
        try:
            cache_key = f"stats:rankings:player:{stat_name}:{position}:{competition_id}:{limit}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for player rankings ({stat_name})")
                return json.loads(cached)

            rankings = await self.repository.get_player_rankings(
                stat_name,
                position,
                competition_id,
                limit
            )

            if rankings:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl * 2,  # Rankings change less frequently
                    json.dumps(rankings)
                )

            return rankings
        except Exception as e:
            logger.error(f"Error in get_player_rankings: {e}")
            raise

    async def get_team_rankings(
        self,
        stat_name: str,
        competition_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get team rankings with caching"""
        try:
            cache_key = f"stats:rankings:team:{stat_name}:{competition_id}:{limit}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for team rankings ({stat_name})")
                return json.loads(cached)

            rankings = await self.repository.get_team_rankings(
                stat_name,
                competition_id,
                limit
            )

            if rankings:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl * 2,
                    json.dumps(rankings)
                )

            return rankings
        except Exception as e:
            logger.error(f"Error in get_team_rankings: {e}")
            raise

    async def compare_players(
        self,
        player_ids: List[str],
        stat_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple players"""
        try:
            cache_key = f"stats:compare:{':'.join(sorted(player_ids))}:{stat_categories}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug("Cache hit for player comparison")
                return json.loads(cached)

            comparison = await self.repository.get_player_comparison(
                player_ids,
                stat_categories
            )

            if comparison:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(comparison)
                )

            return comparison
        except Exception as e:
            logger.error(f"Error in compare_players: {e}")
            raise

    async def aggregate_player_stats(
        self,
        player_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Aggregate player stats over time period"""
        try:
            aggregated = await self.repository.aggregate_player_stats(
                player_id,
                start_date,
                end_date
            )

            return aggregated
        except Exception as e:
            logger.error(f"Error in aggregate_player_stats: {e}")
            raise
