"""
Stream Processor for live data.
Refactored to utilize the shared provider adapters and lazily connect to Kafka.
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

from aiokafka import AIOKafkaProducer
from config.settings import get_settings
from ingestion.metadata_materializer import MetadataMaterializer

logger = logging.getLogger(__name__)


class LiveDataProcessor:
    """Process and distribute parsed live match event data to Kafka"""

    def __init__(self, kafka_producer: Optional[AIOKafkaProducer], bootstrap_servers: str):
        self.kafka = kafka_producer
        self.bootstrap_servers = bootstrap_servers
        self.topic = "raw.events"
        settings = get_settings()
        from shared.adapters.opta.opta_parser import OptaParser
        from shared.adapters.statsbomb.statsbomb_parser import StatsbombParser
        self.parsers = {
            'opta': OptaParser(),
            'statsbomb': StatsbombParser(),
        }
        self.metadata_materializer = MetadataMaterializer(
            mongodb_url=settings.mongodb_url,
            mongodb_database=settings.mongodb_database,
        )
        self._opta_metadata_dir = Path(__file__).resolve().parents[1] / 'fixtures' / 'opta_metadata'
        self._metadata_sidecar_cache: Dict[str, list[Dict[str, Any]]] = {}

    async def _ensure_kafka(self) -> bool:
        if self.kafka is not None:
            return True

        try:
            self.kafka = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers
            )
            await self.kafka.start()
            logger.info("Live ingestion Kafka producer initialized lazily")
            return True
        except Exception as exc:
            logger.error(f"Unable to initialize Kafka producer on demand: {exc}")
            self.kafka = None
            return False

    async def close(self):
        if self.kafka is not None:
            await self.kafka.stop()
            self.kafka = None
        await self.metadata_materializer.close()

    async def process_live_update(self, data: Dict[str, Any], source: str = 'opta'):
        """Parse incoming live data update and publish to Kafka"""
        try:
            source = str(data.get('source') or source or 'opta').lower()
            match_id = data.get('match_id', 'unknown')
            parser = self.parsers.get(source, self.parsers['opta'])
            events = data.get('events', [])
            metadata_documents, live_event_documents = self._split_documents(events, source)

            if source == 'opta' and not metadata_documents:
                metadata_documents = self._load_local_metadata_documents(str(match_id))

            if source == 'statsbomb' and isinstance(events, list) and events:
                await self.metadata_materializer.materialize(
                    provider=source,
                    match_id=str(match_id),
                    documents=events,
                )
                live_event_documents = events

            if metadata_documents:
                await self.metadata_materializer.materialize(
                    provider=source,
                    match_id=str(match_id),
                    documents=metadata_documents,
                )

            if not live_event_documents:
                return

            if not await self._ensure_kafka():
                return

            if isinstance(live_event_documents, list) and len(live_event_documents) > 0:
                if source == 'statsbomb':
                    parsed_events = parser.parse_events(live_event_documents)
                else:
                    parsed_events = parser.parse_events({
                        "match_id": str(match_id),
                        "events": live_event_documents,
                    })
            else:
                parsed_events = []

            parsed_payload = data.copy()
            parsed_payload['source'] = source
            if parsed_events:
                parsed_payload['events'] = parsed_events

            envelope = {
                "match_id": match_id,
                "timestamp": time.time(),
                "payload": parsed_payload
            }

            message = json.dumps(envelope).encode('utf-8')

            await self.kafka.send(
                self.topic,
                key=str(match_id).encode('utf-8'),
                value=message
            )

            logger.debug(f"Published parsed events for match {match_id} to {self.topic}")

        except Exception as e:
            logger.error(f"Error publishing to Kafka: {e}")

    @staticmethod
    def _split_documents(events: Any, source: str) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
        if source != 'opta' or not isinstance(events, list):
            return [], events if isinstance(events, list) else []

        metadata_documents = []
        live_event_documents = []

        for item in events:
            if isinstance(item, dict) and 'SoccerFeed' in item:
                metadata_documents.append(item)
            else:
                live_event_documents.append(item)

        return metadata_documents, live_event_documents

    def _load_local_metadata_documents(self, match_id: str) -> list[Dict[str, Any]]:
        normalized_match_id = str(match_id or '').strip()
        if not normalized_match_id:
            return []

        cached_documents = self._metadata_sidecar_cache.get(normalized_match_id)
        if cached_documents is not None:
            return cached_documents

        sidecar_path = self._opta_metadata_dir / f'{normalized_match_id}.json'
        if not sidecar_path.exists():
            self._metadata_sidecar_cache[normalized_match_id] = []
            return []

        try:
            raw_payload = json.loads(sidecar_path.read_text(encoding='utf-8'))
        except Exception as exc:
            logger.warning('Unable to load Opta metadata sidecar for match %s: %s', normalized_match_id, exc)
            self._metadata_sidecar_cache[normalized_match_id] = []
            return []

        candidate_documents = raw_payload if isinstance(raw_payload, list) else [raw_payload]
        metadata_documents = [
            document
            for document in candidate_documents
            if isinstance(document, dict) and 'SoccerFeed' in document
        ]

        if metadata_documents:
            logger.info(
                'Loaded %s local Opta metadata sidecar document(s) for match %s',
                len(metadata_documents),
                normalized_match_id,
            )

        self._metadata_sidecar_cache[normalized_match_id] = metadata_documents
        return metadata_documents
