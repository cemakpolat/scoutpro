"""
Kafka Producer Client for Event Publishing
"""
from aiokafka import AIOKafkaProducer
import json
import logging
from typing import Any, Dict, Optional
import os
from datetime import datetime, date
import uuid


class _DatetimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime, date and UUID objects."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

logger = logging.getLogger(__name__)


class KafkaProducerClient:
    """
    Async Kafka producer for publishing events

    Usage:
        async with KafkaProducerClient() as producer:
            await producer.send_event('player.events', event_data)
    """

    def __init__(self, bootstrap_servers: Optional[str] = None):
        """
        Initialize Kafka producer

        Args:
            bootstrap_servers: Kafka bootstrap servers (default: from env)
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            'KAFKA_BOOTSTRAP_SERVERS',
            'kafka:9092'
        )
        self.producer: Optional[AIOKafkaProducer] = None
        self._started = False

    async def start(self):
        """Start Kafka producer"""
        if self._started:
            return

        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, cls=_DatetimeEncoder).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                compression_type='gzip',
                acks='all',  # Wait for all replicas
            )
            await self.producer.start()
            self._started = True
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")

        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop(self):
        """Stop Kafka producer"""
        if self.producer and self._started:
            try:
                await self.producer.stop()
                self._started = False
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")

    async def send_event(
        self,
        topic: str,
        event: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send event to Kafka topic

        Args:
            topic: Kafka topic name
            event: Event data (dict)
            key: Optional partition key
            headers: Optional message headers

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self._started:
                await self.start()

            # Enrich event with metadata
            enriched_event = {
                **event,
                'timestamp': event.get('timestamp', datetime.utcnow().isoformat()),
                'event_id': event.get('event_id', str(uuid.uuid4())),
                'version': event.get('version', '1.0')
            }

            # Convert headers to bytes
            kafka_headers = None
            if headers:
                kafka_headers = [(k, v.encode('utf-8')) for k, v in headers.items()]

            # Enforce partitioning on match_id if key is not already provided
            if key is None and isinstance(enriched_event, dict):
                if "match_id" in enriched_event:
                    key = str(enriched_event["match_id"])
                elif "matchID" in enriched_event:
                    key = str(enriched_event["matchID"])

            # Send to Kafka
            future = await self.producer.send(
                topic,
                value=enriched_event,
                key=key,
                headers=kafka_headers
            )

            # Wait for acknowledgment
            record_metadata = await future

            logger.debug(
                f"Event sent to {topic}: "
                f"partition={record_metadata.partition}, "
                f"offset={record_metadata.offset}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to send event to {topic}: {e}")
            return False

    async def send_events_batch(
        self,
        topic: str,
        events: list[Dict[str, Any]],
        key_extractor: Optional[callable] = None
    ) -> int:
        """
        Send multiple events in batch

        Args:
            topic: Kafka topic name
            events: List of event dicts
            key_extractor: Optional function to extract key from event

        Returns:
            Number of successfully sent events
        """
        if not self._started:
            await self.start()

        success_count = 0

        for event in events:
            key = key_extractor(event) if key_extractor else None
            
            # Use raw message partitioning
            if key is None and isinstance(event, dict):
                if "match_id" in event:
                    key = str(event["match_id"])
                elif "matchID" in event:
                    key = str(event["matchID"])

            if await self.send_event(topic, event, key=key):
                success_count += 1

        logger.info(f"Batch sent: {success_count}/{len(events)} events to {topic}")
        return success_count

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()


# Global producer instance (singleton pattern)
_global_producer: Optional[KafkaProducerClient] = None


async def get_kafka_producer() -> KafkaProducerClient:
    """
    Get global Kafka producer instance

    Usage:
        producer = await get_kafka_producer()
        await producer.send_event('topic', event)
    """
    global _global_producer

    if _global_producer is None:
        _global_producer = KafkaProducerClient()
        await _global_producer.start()

    return _global_producer
