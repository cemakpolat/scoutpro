"""
Player Service - Business Logic Layer
"""
from typing import Optional, List, Dict, Any
import json
import logging
from redis import Redis
from aiokafka import AIOKafkaProducer
import sys
sys.path.append('/app')
from shared.models.base import Player, PlayerStatistics
from repository.interfaces import IPlayerRepository

logger = logging.getLogger(__name__)


class PlayerService:
    """Player service with caching and event publishing"""

    LIST_CACHE_VERSION = "v2"
    SEARCH_CACHE_VERSION = "v2"

    def __init__(
        self,
        repository: IPlayerRepository,
        redis_client: Redis,
        kafka_producer: Optional[AIOKafkaProducer] = None,
        cache_ttl: int = 300
    ):
        self.repository = repository
        self.redis = redis_client
        self.kafka = kafka_producer
        self.cache_ttl = cache_ttl

    async def get_player(self, player_id: str) -> Optional[Player]:
        """Get player by ID with caching"""
        try:
            # Check cache first
            cache_key = f"player:{player_id}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for player {player_id}")
                return Player(**json.loads(cached))

            # Fetch from repository
            player = await self.repository.get_by_id(player_id)

            if player:
                # Cache the result
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    player.json()
                )
                logger.debug(f"Cached player {player_id}")

            return player
        except Exception as e:
            logger.error(f"Error in get_player({player_id}): {e}")
            raise

    async def list_players(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Player]:
        """List players with filters"""
        try:
            filters = filters or {}

            # Create cache key from filters
            cache_key = (
                f"players:list:{self.LIST_CACHE_VERSION}:"
                f"{json.dumps(filters, sort_keys=True)}:{limit}"
            )
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug("Cache hit for player list")
                return [Player(**p) for p in json.loads(cached)]

            # Fetch from repository
            players = await self.repository.find_by_filters(filters, limit)

            # Cache the result
            if players:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps([p.dict() for p in players])
                )

            return players
        except Exception as e:
            logger.error(f"Error in list_players: {e}")
            raise

    async def search_players(self, query: str, limit: int = 20) -> List[Player]:
        """Search players by name"""
        try:
            # Cache search results
            cache_key = f"players:search:{self.SEARCH_CACHE_VERSION}:{query}:{limit}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for search '{query}'")
                return [Player(**p) for p in json.loads(cached)]

            # Search in repository
            players = await self.repository.search(query, limit)

            # Cache results
            if players:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl // 2,  # Shorter TTL for searches
                    json.dumps([p.dict() for p in players])
                )

            return players
        except Exception as e:
            logger.error(f"Error in search_players('{query}'): {e}")
            raise

    async def get_player_statistics(
        self,
        player_id: str,
        stat_type: Optional[str] = None,
        per_90: bool = False
    ) -> Optional[PlayerStatistics]:
        """Get player statistics with caching"""
        try:
            # Cache key includes all parameters
            cache_key = f"player:stats:{player_id}:{stat_type}:{per_90}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for player {player_id} statistics")
                return PlayerStatistics(**json.loads(cached))

            # Fetch from repository
            stats = await self.repository.get_statistics(player_id, stat_type, per_90)

            if stats:
                # Cache with shorter TTL (stats change more frequently)
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl // 2,
                    stats.json()
                )

            return stats
        except Exception as e:
            logger.error(f"Error in get_player_statistics({player_id}): {e}")
            raise

    async def create_player(self, player: Player) -> str:
        """Create new player and publish event"""
        try:
            # Create in repository
            player_id = await self.repository.create(player)

            # Invalidate list cache
            await self._invalidate_list_cache()

            # Publish event
            if self.kafka:
                await self._publish_event('player.created', {
                    'player_id': player_id,
                    'player': player.dict()
                })

            logger.info(f"Created player {player_id}")
            return player_id
        except Exception as e:
            logger.error(f"Error in create_player: {e}")
            raise

    async def update_player(self, player_id: str, player: Player) -> bool:
        """Update player and publish event"""
        try:
            # Update in repository
            success = await self.repository.update(player_id, player)

            if success:
                # Invalidate cache
                await self.redis.delete(f"player:{player_id}")
                await self._invalidate_list_cache()

                # Publish event
                if self.kafka:
                    await self._publish_event('player.updated', {
                        'player_id': player_id,
                        'player': player.dict()
                    })

                logger.info(f"Updated player {player_id}")

            return success
        except Exception as e:
            logger.error(f"Error in update_player({player_id}): {e}")
            raise

    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to Kafka"""
        try:
            if not self.kafka:
                return

            event = {
                'type': event_type,
                'data': data
            }

            await self.kafka.send(
                'player.events',
                value=json.dumps(event).encode('utf-8')
            )
            logger.debug(f"Published event: {event_type}")
        except Exception as e:
            logger.error(f"Error publishing event {event_type}: {e}")
            # Don't raise - event publishing is non-critical

    async def _invalidate_list_cache(self):
        """Invalidate all list caches"""
        try:
            # Delete all keys matching players:list:*
            cursor = 0
            pattern = "players:list:*"

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break

            logger.debug("Invalidated player list cache")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
