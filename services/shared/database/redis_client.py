"""
Redis Client for Caching and Real-Time State
Used for caching API responses, session data, and real-time match state
"""
import redis.asyncio as aioredis
import json
import logging
import os
from typing import Any, Optional, List, Dict
from datetime import timedelta

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client for caching and real-time state

    Used for:
    - API response caching
    - Session management
    - Real-time match state
    - Rate limiting counters
    - Pub/Sub messaging
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: int = 0,
        password: Optional[str] = None
    ):
        """
        Initialize Redis client

        Args:
            host: Redis host (default: from REDIS_HOST env)
            port: Redis port (default: from REDIS_PORT env or 6379)
            db: Redis database number (default: 0)
            password: Redis password (default: from REDIS_PASSWORD env)
        """
        self.host = host or os.getenv('REDIS_HOST', 'redis')
        self.port = port or int(os.getenv('REDIS_PORT', '6379'))
        self.db = db
        self.password = password or os.getenv('REDIS_PASSWORD')

        self.client: Optional[aioredis.Redis] = None

    async def connect(self):
        """Create Redis connection"""
        if self.client is not None:
            return

        try:
            self.client = await aioredis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                password=self.password,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.client.ping()
            logger.info(f"Connected to Redis: {self.host}:{self.port}/{self.db}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Redis")

    # ============ Basic Operations ============

    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set key-value pair

        Args:
            key: Cache key
            value: Cache value
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful
        """
        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for key"""
        try:
            await self.client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Error setting TTL for key {key}: {e}")
            return False

    # ============ JSON Operations ============

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value by key"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in key {key}")
                return None
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set JSON value"""
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, ttl)
        except Exception as e:
            logger.error(f"Error setting JSON key {key}: {e}")
            return False

    # ============ Hash Operations ============

    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value"""
        try:
            return await self.client.hget(name, key)
        except Exception as e:
            logger.error(f"Error getting hash field {name}:{key}: {e}")
            return None

    async def hset(self, name: str, key: str, value: str) -> bool:
        """Set hash field"""
        try:
            await self.client.hset(name, key, value)
            return True
        except Exception as e:
            logger.error(f"Error setting hash field {name}:{key}: {e}")
            return False

    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields"""
        try:
            return await self.client.hgetall(name)
        except Exception as e:
            logger.error(f"Error getting hash {name}: {e}")
            return {}

    async def hdel(self, name: str, *keys: str) -> bool:
        """Delete hash fields"""
        try:
            await self.client.hdel(name, *keys)
            return True
        except Exception as e:
            logger.error(f"Error deleting hash fields {name}: {e}")
            return False

    # ============ List Operations ============

    async def lpush(self, key: str, *values: str) -> bool:
        """Push values to list (left)"""
        try:
            await self.client.lpush(key, *values)
            return True
        except Exception as e:
            logger.error(f"Error lpush to {key}: {e}")
            return False

    async def rpush(self, key: str, *values: str) -> bool:
        """Push values to list (right)"""
        try:
            await self.client.rpush(key, *values)
            return True
        except Exception as e:
            logger.error(f"Error rpush to {key}: {e}")
            return False

    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get range of list elements"""
        try:
            return await self.client.lrange(key, start, end)
        except Exception as e:
            logger.error(f"Error getting list range {key}: {e}")
            return []

    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to specified range"""
        try:
            await self.client.ltrim(key, start, end)
            return True
        except Exception as e:
            logger.error(f"Error trimming list {key}: {e}")
            return False

    # ============ Set Operations ============

    async def sadd(self, key: str, *members: str) -> bool:
        """Add members to set"""
        try:
            await self.client.sadd(key, *members)
            return True
        except Exception as e:
            logger.error(f"Error adding to set {key}: {e}")
            return False

    async def srem(self, key: str, *members: str) -> bool:
        """Remove members from set"""
        try:
            await self.client.srem(key, *members)
            return True
        except Exception as e:
            logger.error(f"Error removing from set {key}: {e}")
            return False

    async def smembers(self, key: str) -> set:
        """Get all set members"""
        try:
            return await self.client.smembers(key)
        except Exception as e:
            logger.error(f"Error getting set members {key}: {e}")
            return set()

    async def sismember(self, key: str, member: str) -> bool:
        """Check if member exists in set"""
        try:
            return await self.client.sismember(key, member)
        except Exception as e:
            logger.error(f"Error checking set member {key}: {e}")
            return False

    # ============ Caching Helpers ============

    async def cache_player_data(
        self,
        player_id: str,
        data: Dict[str, Any],
        ttl: int = 300  # 5 minutes
    ) -> bool:
        """Cache player data"""
        key = f"player:{player_id}"
        return await self.set_json(key, data, ttl)

    async def get_cached_player_data(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get cached player data"""
        key = f"player:{player_id}"
        return await self.get_json(key)

    async def cache_team_data(
        self,
        team_id: str,
        data: Dict[str, Any],
        ttl: int = 300
    ) -> bool:
        """Cache team data"""
        key = f"team:{team_id}"
        return await self.set_json(key, data, ttl)

    async def get_cached_team_data(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get cached team data"""
        key = f"team:{team_id}"
        return await self.get_json(key)

    async def cache_match_data(
        self,
        match_id: str,
        data: Dict[str, Any],
        ttl: int = 60  # 1 minute for live matches
    ) -> bool:
        """Cache match data"""
        key = f"match:{match_id}"
        return await self.set_json(key, data, ttl)

    async def get_cached_match_data(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get cached match data"""
        key = f"match:{match_id}"
        return await self.get_json(key)

    # ============ Real-Time Match State ============

    async def set_live_match_state(
        self,
        match_id: str,
        state: Dict[str, Any]
    ) -> bool:
        """Set live match state (no TTL, cleared when match ends)"""
        key = f"live:match:{match_id}"
        return await self.set_json(key, state)

    async def get_live_match_state(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get live match state"""
        key = f"live:match:{match_id}"
        return await self.get_json(key)

    async def delete_live_match_state(self, match_id: str) -> bool:
        """Delete live match state (when match ends)"""
        key = f"live:match:{match_id}"
        return await self.delete(key)

    async def add_live_match(self, match_id: str) -> bool:
        """Add match to live matches set"""
        return await self.sadd("live:matches", match_id)

    async def remove_live_match(self, match_id: str) -> bool:
        """Remove match from live matches set"""
        return await self.srem("live:matches", match_id)

    async def get_live_matches(self) -> List[str]:
        """Get all live match IDs"""
        matches = await self.smembers("live:matches")
        return list(matches)

    # ============ Rate Limiting ============

    async def increment_rate_limit(
        self,
        key: str,
        window_seconds: int = 60
    ) -> int:
        """
        Increment rate limit counter

        Args:
            key: Rate limit key (e.g., "ratelimit:ip:192.168.1.1")
            window_seconds: Time window in seconds

        Returns:
            Current count
        """
        try:
            count = await self.client.incr(key)
            if count == 1:
                await self.client.expire(key, window_seconds)
            return count
        except Exception as e:
            logger.error(f"Error incrementing rate limit {key}: {e}")
            return 0

    # ============ Pub/Sub ============

    async def publish(self, channel: str, message: str) -> bool:
        """Publish message to channel"""
        try:
            await self.client.publish(channel, message)
            return True
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")
            return False

    async def publish_json(self, channel: str, data: Any) -> bool:
        """Publish JSON message to channel"""
        try:
            message = json.dumps(data)
            return await self.publish(channel, message)
        except Exception as e:
            logger.error(f"Error publishing JSON to {channel}: {e}")
            return False

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


# Global client instance
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """Get global Redis client instance"""
    global _redis_client

    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()

    return _redis_client
