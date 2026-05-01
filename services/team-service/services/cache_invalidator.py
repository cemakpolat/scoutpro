import asyncio
import logging
from config.settings import get_settings
from shared.messaging import KafkaConsumerClient
from dependencies import get_database_manager

logger = logging.getLogger(__name__)
settings = get_settings()

class TeamCacheInvalidator:
    def __init__(self):
        self.settings = get_settings()
        self.consumer = KafkaConsumerClient(
            topics=['team.events'],
            group_id='team_service_cache_group'
        )
        self.running = False
        
    async def start(self):
        self.running = True
        logger.info("Starting Team Cache Invalidator...")
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
        logger.info("Team Cache Invalidator stopped")

    async def process_event(self, event_data: dict):
        """
        Invalidate cache when team data or statistics change.
        """
        payload = event_data.get('data', {})
        team_id = payload.get('team_id') or payload.get('team', {}).get('uID')

        if not team_id:
            logger.warning("Event missing team_id, skipping invalidation.")
            return

        await self._clear_team_caches([team_id])

    async def _clear_team_caches(self, team_ids: list):
        try:
            manager = await get_database_manager()
            redis_client = manager.redis
            
            if redis_client:
                keys_to_delete = []
                for tid in team_ids:
                    if not tid:
                        continue
                    keys_to_delete.append(f"team:{tid}")
                    keys_to_delete.append(f"team:squad:{tid}")
                
                if keys_to_delete:
                    await redis_client.delete(*keys_to_delete)
                
                await self._delete_by_pattern(redis_client, "teams:list:*")
                await self._delete_by_pattern(redis_client, "teams:search:*")
                
                logger.debug(f"Invalidated cache for teams {team_ids}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache for teams {team_ids}: {e}")

    async def _delete_by_pattern(self, redis_client, pattern: str):
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await redis_client.delete(*keys)
            if cursor == 0:
                break
