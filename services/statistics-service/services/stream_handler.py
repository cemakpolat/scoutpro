import asyncio
import json
import logging
from config.settings import get_settings
from shared.messaging import KafkaConsumerClient

logger = logging.getLogger(__name__)
settings = get_settings()

class StatisticsStreamProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.consumer = KafkaConsumerClient(
            topics=['raw.events'],
            group_id='statistics_service_group'
        )
        self.running = False
        
    async def start(self):
        self.running = True
        logger.info("Starting Statistics Stream Processor...")
        await self.consumer.start()
        
        try:
            async for message in self.consumer.consume():
                if not self.running:
                    break
                    
                await self.process_event(message)
                    
        except Exception as e:
            logger.error(f"Error in stream processing: {e}")
            raise

    async def stop(self):
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info("Statistics Stream Processor stopped")

    async def process_event(self, event_data: dict):
        """
        Process incoming live event data, compute stats, and push to TimescaleDB
        """
        match_id = event_data.get('match_id')
        event_type = event_data.get('type')
        
        if not match_id or not event_type:
            logger.warning("Event missing match_id or type, discarding.")
            return

        try:
            logger.debug(f"Processing stat for event: {event_type} in match {match_id}")
            # Insert statistics logic to write to TimescaleDB
            pass
        except Exception as e:
            logger.error(f"Failed to process event for match {match_id}: {e}")
