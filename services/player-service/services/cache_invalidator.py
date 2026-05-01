import asyncio
import logging
from config.settings import get_settings
from shared.messaging import KafkaConsumerClient
from dependencies import get_database_manager

logger = logging.getLogger(__name__)
settings = get_settings()

class PlayerCacheInvalidator:
    def __init__(self):
        self.settings = get_settings()
        self.consumer = KafkaConsumerClient(
            topics=['player.events'],
            group_id='player_service_cache_group'
        )
        self.running = False
        
    async def start(self):
        self.running = True
        logger.info("Starting Player Cache Invalidator...")
        await self.consumer.start()
        
        try:
            async for message in self.consumer.consume():
                if not self.running:
                    break
                    
                await self.process_event(message)
                    
        except Exception as e:
            logger.error(f"Error in cache invalidator stream: {e}")
            raise

    async def stop(self):
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info("Player Cache Invalidator stopped")

    async def process_event(self, event_data: dict):
        """
        Invalidate cache when player data or statistics change.
        """
        payload = event_data.get('data', {})
        player_id = payload.get('player_id') or payload.get('player', {}).get('uID')
        
        if not player_id:
            logger.warning("Event missing player_id, skipping invalidation.")
            return

        try:
            manager = await get_database_manager()
            redis_client = manager.redis_client
            
            if redis_client:
                await redis_client.delete(f"player:{player_id}")
                await self._delete_by_pattern(redis_client, "players:list:*")
                await self._delete_by_pattern(redis_client, "players:search:*")
                await self._delete_by_pattern(redis_client, f"player:stats:{player_id}:*")
                
                logger.debug(f"Invalidated cache for player {player_id}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache for player {player_id}: {e}")

    async def _delete_by_pattern(self, redis_client, pattern: str):
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await redis_client.delete(*keys)
            if cursor == 0:
                break
