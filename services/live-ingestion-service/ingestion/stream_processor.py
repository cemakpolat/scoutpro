"""
Stream Processor for live data.
Refactored to utilize the shared Opta adapter for parsing. 
"""
import logging
import json
import time
from typing import Dict, Any
from aiokafka import AIOKafkaProducer

from shared.adapters.opta.opta_parser import OptaParser

logger = logging.getLogger(__name__)

class LiveDataProcessor:
    """Process and distribute parsed live match event data to Kafka"""

    def __init__(self, kafka_producer: AIOKafkaProducer):
        self.kafka = kafka_producer
        self.topic = "raw.events"
        # We will initialize parsers dynamically based on source if available, 
        # falling back to OptaParser for legacy compatibility.
        from shared.adapters.opta.opta_parser import OptaParser
        from shared.adapters.statsbomb.statsbomb_parser import StatsBombParser
        self.parsers = {
            'opta': OptaParser(),
            'statsbomb': StatsBombParser()
        }

    async def process_live_update(self, data: Dict[str, Any], source: str = 'opta'):
        """Parse incoming live data update and publish to Kafka"""
        try:
            match_id = data.get('match_id', 'unknown')
            
            # Select the appropriate parser
            parser = self.parsers.get(source, self.parsers['opta'])
            
            # Parse events cleanly to eliminate legacy dataRetreving cruft
            events = data.get('events', [])
            
            if isinstance(events, list) and len(events) > 0:
                parsed_events = parser.parse_events({"events": events})
            else:
                parsed_events = []

            # Ensure we still pass the entire parsed data properly
            parsed_payload = data.copy()
            if parsed_events:
                parsed_payload['events'] = parsed_events

            envelope = {
                "match_id": match_id,
                "timestamp": time.time(),
                "payload": parsed_payload
            }

            message = json.dumps(envelope).encode('utf-8')

            # Publish parsed structured events
            await self.kafka.send(
                self.topic,
                key=str(match_id).encode('utf-8'),
                value=message
            )

            logger.debug(f"Published parsed events for match {match_id} to {self.topic}")

        except Exception as e:
            logger.error(f"Error publishing to Kafka: {e}")
