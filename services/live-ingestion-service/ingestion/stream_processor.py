"""
Stream Processor for live data
"""
import logging
import json
from typing import Dict, Any
from aiokafka import AIOKafkaProducer
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class LiveDataProcessor:
    """Process and distribute live match data"""

    def __init__(
        self,
        kafka_producer: AIOKafkaProducer,
        mongo_db: AsyncIOMotorDatabase
    ):
        self.kafka = kafka_producer
        self.db = mongo_db
        self.matches_collection = mongo_db['matches']
        self.events_collection = mongo_db['match_events']

    async def process_live_update(self, data: Dict[str, Any]):
        """Process incoming live data update"""
        try:
            match_id = data.get('match_id')
            events = data.get('events', [])
            stats = data.get('stats', {})

            # Update match in database
            if stats:
                await self._update_match_stats(match_id, stats)

            # Store events
            if events:
                await self._store_events(match_id, events)

            # Publish to Kafka
            await self._publish_to_kafka(data)

            logger.debug(f"Processed live update for match {match_id}")

        except Exception as e:
            logger.error(f"Error processing live update: {e}")

    async def _update_match_stats(self, match_id: str, stats: Dict[str, Any]):
        """Update match statistics in database"""
        try:
            await self.matches_collection.update_one(
                {'uID': int(match_id)},
                {
                    '$set': {
                        'liveStats': stats,
                        'lastUpdated': stats.get('timestamp')
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error updating match stats: {e}")

    async def _store_events(self, match_id: str, events: list):
        """Store match events"""
        try:
            for event in events:
                event['matchID'] = int(match_id)

                # Upsert event
                await self.events_collection.update_one(
                    {
                        'matchID': event['matchID'],
                        'eventID': event.get('eventID')
                    },
                    {'$set': event},
                    upsert=True
                )
        except Exception as e:
            logger.error(f"Error storing events: {e}")

    async def _publish_to_kafka(self, data: Dict[str, Any]):
        """Publish live update to Kafka"""
        try:
            message = json.dumps(data).encode('utf-8')

            await self.kafka.send(
                'live.events',
                value=message
            )

            logger.debug("Published to Kafka")

        except Exception as e:
            logger.error(f"Error publishing to Kafka: {e}")
