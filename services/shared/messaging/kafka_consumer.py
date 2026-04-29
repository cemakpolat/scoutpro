"""
Kafka Consumer Client for Event Consumption
"""
from aiokafka import AIOKafkaConsumer
import json
import logging
from typing import Any, Dict, List, Optional, Callable, Awaitable
import os
import asyncio

from .events import Event, EventType

logger = logging.getLogger(__name__)


class KafkaConsumerClient:
    """
    Async Kafka consumer for subscribing to events

    Usage:
        async with KafkaConsumerClient(topics=['player.events']) as consumer:
            async for event in consumer.consume():
                await process_event(event)
    """

    def __init__(
        self,
        topics: List[str],
        group_id: str,
        bootstrap_servers: Optional[str] = None,
        auto_offset_reset: str = "earliest"
    ):
        """
        Initialize Kafka consumer

        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID
            bootstrap_servers: Kafka bootstrap servers (default: from env)
            auto_offset_reset: Where to start consuming ('earliest' or 'latest')
        """
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            'KAFKA_BOOTSTRAP_SERVERS',
            'kafka:9092'
        )
        self.auto_offset_reset = auto_offset_reset
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._started = False
        self._running = False

    async def start(self):
        """Start Kafka consumer"""
        if self._started:
            return

        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset,
                enable_auto_commit=False,  # Disabled auto-commit
                value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
            )
            await self.consumer.start()
            self._started = True
            self._running = True
            logger.info(
                f"Kafka consumer started: topics={self.topics}, "
                f"group={self.group_id}, bootstrap={self.bootstrap_servers}"
            )

        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise

    async def stop(self):
        """Stop Kafka consumer"""
        self._running = False
        if self.consumer and self._started:
            try:
                await self.consumer.stop()
                self._started = False
                logger.info("Kafka consumer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka consumer: {e}")

    async def consume(self):
        """
        Consume events from Kafka topics

        Yields:
            Event dictionaries

        Usage:
            async for event in consumer.consume():
                print(event)
        """
        try:
            if not self._started:
                await self.start()

            async for message in self.consumer:
                if not self._running:
                    break

                try:
                    # Parse event
                    event_data = message.value

                    logger.debug(
                        f"Consumed event: topic={message.topic}, "
                        f"partition={message.partition}, "
                        f"offset={message.offset}, "
                        f"key={message.key}"
                    )

                    yield event_data
                    
                    # Manually commit offset after processing
                    try:
                        from aiokafka import TopicPartition
                        from aiokafka.structs import OffsetAndMetadata
                        tp = TopicPartition(message.topic, message.partition)
                        await self.consumer.commit({tp: OffsetAndMetadata(message.offset + 1, "")})
                    except Exception as commit_err:
                        logger.error(f"Failed to commit offset: {commit_err}")

                except Exception as e:
                    logger.error(
                        f"Error processing message from {message.topic}: {e}",
                        exc_info=True
                    )
                    # DLQ logic would go here
                    continue

        except Exception as e:
            logger.error(f"Error in consume loop: {e}", exc_info=True)
            raise

    async def consume_with_handler(
        self,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
        error_handler: Optional[Callable[[Exception, Dict[str, Any]], Awaitable[None]]] = None
    ):
        """
        Consume events and process with handler

        Args:
            handler: Async function to process each event
            error_handler: Optional async function to handle errors

        Usage:
            async def process_event(event):
                print(f"Processing: {event['event_type']}")

            async def handle_error(error, event):
                logger.error(f"Failed to process {event}: {error}")

            await consumer.consume_with_handler(process_event, handle_error)
        """
        try:
            async for event in self.consume():
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Handler error for event {event.get('event_id')}: {e}")
                    if error_handler:
                        try:
                            await error_handler(e, event)
                        except Exception as eh_error:
                            logger.error(f"Error handler failed: {eh_error}")

        except Exception as e:
            logger.error(f"Fatal error in consume_with_handler: {e}", exc_info=True)
            raise

    async def consume_filtered(
        self,
        event_types: Optional[List[EventType]] = None,
        filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None
    ):
        """
        Consume events with filtering

        Args:
            event_types: List of event types to filter by
            filter_func: Custom filter function

        Yields:
            Filtered events

        Usage:
            async for event in consumer.consume_filtered(
                event_types=[EventType.PLAYER_CREATED, EventType.PLAYER_UPDATED]
            ):
                print(event)
        """
        async for event in self.consume():
            # Filter by event type
            if event_types:
                event_type = event.get('event_type')
                if event_type not in [et.value for et in event_types]:
                    continue

            # Filter by custom function
            if filter_func and not filter_func(event):
                continue

            yield event

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()


class EventSubscriber:
    """
    Higher-level event subscriber with handler registration

    Usage:
        subscriber = EventSubscriber(group_id='player-service-consumer')

        @subscriber.on(EventType.MATCH_STARTED)
        async def handle_match_start(event):
            print(f"Match started: {event['data']['match_id']}")

        await subscriber.start(['match.events'])
    """

    def __init__(
        self,
        group_id: str,
        bootstrap_servers: Optional[str] = None
    ):
        """
        Initialize event subscriber

        Args:
            group_id: Consumer group ID
            bootstrap_servers: Kafka bootstrap servers
        """
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
        self.handlers: Dict[EventType, List[Callable]] = {}
        self.consumer: Optional[KafkaConsumerClient] = None
        self._task: Optional[asyncio.Task] = None

    def on(self, event_type: EventType):
        """
        Decorator to register event handler

        Usage:
            @subscriber.on(EventType.PLAYER_CREATED)
            async def handle_player_created(event):
                print(event)
        """
        def decorator(func: Callable[[Dict[str, Any]], Awaitable[None]]):
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(func)
            logger.info(f"Registered handler for {event_type.value}: {func.__name__}")
            return func
        return decorator

    async def start(self, topics: List[str]):
        """
        Start consuming events

        Args:
            topics: List of Kafka topics to subscribe to
        """
        self.consumer = KafkaConsumerClient(
            topics=topics,
            group_id=self.group_id,
            bootstrap_servers=self.bootstrap_servers
        )

        await self.consumer.start()

        # Start background task for consuming
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(f"EventSubscriber started: topics={topics}, group={self.group_id}")

    async def stop(self):
        """Stop consuming events"""
        if self.consumer:
            await self.consumer.stop()

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("EventSubscriber stopped")

    async def _consume_loop(self):
        """Background task for consuming and routing events"""
        try:
            async for event in self.consumer.consume():
                event_type_str = event.get('event_type')
                if not event_type_str:
                    logger.warning(f"Event missing event_type: {event}")
                    continue

                try:
                    event_type = EventType(event_type_str)
                except ValueError:
                    logger.warning(f"Unknown event type: {event_type_str}")
                    continue

                # Call all registered handlers for this event type
                handlers = self.handlers.get(event_type, [])
                for handler in handlers:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(
                            f"Handler {handler.__name__} failed for "
                            f"{event_type.value}: {e}",
                            exc_info=True
                        )

        except asyncio.CancelledError:
            logger.info("Consume loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Fatal error in consume loop: {e}", exc_info=True)
            raise

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
