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
            topics=['player.stats_updated'],
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
        Invalidate cache when a player's stats are updated
        """
        player_id = event_data.get('player_id')
        
        if not player_id:
            logger.warning("Event missing player_id, skipping invalidation.")
            return

        try:
            manager = await get_database_manager()
            redis_client = manager.redis
            
            if redis_client:
                # Invalidate specific player cache
                cache_key = f"{settings.service_name}:player:{player_id}"
                await redis_client.delete(cache_key)
                
                # Invalidate player list cache patterns (simple approach: clear query caches)
                # In production, use redis SCAN or specific keys
                cursor = '0'
                while cursor != 0:
                    cursor, keys = await redis_client.scan(cursor=cursor, match=f"{settings.service_name}:players:*", count=100)
                    if keys:
                        await redis_client.delete(*keys)
                
                logger.debug(f"Invalidated cache for player {player_id}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache for player {player_id}: {e}")
