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
            topics=['team.stats_updated'],
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
        Invalidate cache when a team's stats are updated
        """
        team_id = event_data.get('team_id')
        match_id = event_data.get('match_id') # often provided if it's match-specific
        
        # sometimes the event could be match.completed
        if not team_id and event_data.get('type') == 'match.completed':
            # This is a generic match update, clear entire team cache patterns
            team_id = event_data.get('home_team_id')
            away_team_id = event_data.get('away_team_id')
            await self._clear_team_caches([team_id, away_team_id])
            return

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
                    # Invalidate specific team cache
                    keys_to_delete.append(f"{settings.service_name}:team:{tid}")
                
                if keys_to_delete:
                    await redis_client.delete(*keys_to_delete)
                
                # Invalidate team list cache patterns
                cursor = '0'
                while cursor != 0:
                    cursor, keys = await redis_client.scan(cursor=cursor, match=f"{settings.service_name}:teams:*", count=100)
                    if keys:
                        await redis_client.delete(*keys)
                
                logger.debug(f"Invalidated cache for teams {team_ids}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache for teams {team_ids}: {e}")
