import asyncio
import logging
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from config.settings import get_settings
from shared.messaging import KafkaConsumerClient, EventType, create_event, get_kafka_producer
from shared.utils.database import DatabaseManager
from services.event_metric_utils import EventMetricAccumulator

logger = logging.getLogger(__name__)
settings = get_settings()


class StatisticsStreamProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.db_manager = DatabaseManager()
        self.mongo_db = None
        self.player_stats_collection = None
        self.team_stats_collection = None
        self.consumer = KafkaConsumerClient(
            topics=['raw.events'],
            group_id='statistics_service_group'
        )
        self.running = False

    async def start(self):
        try:
            self.mongo_db = await self.db_manager.connect_mongodb(
                self.settings.mongodb_url,
                self.settings.mongodb_database,
            )
            self.player_stats_collection = self.mongo_db['player_statistics']
            self.team_stats_collection = self.mongo_db['team_statistics']

            self.running = True
            logger.info("Starting Statistics Stream Processor...")
            await self.consumer.start()

            async for message in self.consumer.consume():
                if not self.running:
                    break

                await self.process_event(message)

        except asyncio.CancelledError:
            logger.info("Statistics Stream Processor cancellation received")
            raise

        except Exception as e:
            if not self.running:
                logger.info(f"Statistics Stream Processor stopped while closing dependencies: {e}")
                return
            logger.error(f"Error in stream processing: {e}")
            raise

    async def stop(self):
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        await self.db_manager.close_all()
        logger.info("Statistics Stream Processor stopped")

    async def process_event(self, event_data: dict):
        """
        Consume parsed live events from Kafka and persist Mongo-backed read models.
        """
        match_id = str(event_data.get('match_id') or event_data.get('payload', {}).get('match_id') or '')
        payload = event_data.get('payload', {})
        events = payload.get('events', [])

        if not match_id or not isinstance(events, list) or not events:
            logger.debug("Skipping statistics batch without match_id/events")
            return

        updated_players = set()
        updated_teams = set()
        processed_events = 0

        for raw_event in events:
            increments = self._build_increments(raw_event)
            if not increments:
                continue

            # Extract float xG increment separately, merge back into a unified inc dict
            xg_val = increments.pop('xG', None)
            inc_dict = dict(increments)
            if xg_val is not None:
                inc_dict['xG'] = xg_val

            processed_events += 1
            player_id = self._optional_int(raw_event.get('player_id'))
            team_id = self._optional_int(raw_event.get('team_id'))

            if player_id is not None:
                await self.player_stats_collection.update_one(
                    {'playerID': player_id},
                    {
                        '$inc': inc_dict,
                        '$set': {
                            'updatedAt': datetime.now(timezone.utc).isoformat(),
                            'lastMatchID': self._coerce_identifier(match_id),
                        },
                        '$addToSet': {'matchIDs': self._coerce_identifier(match_id)},
                    },
                    upsert=True,
                )
                updated_players.add(player_id)

            if team_id is not None:
                await self.team_stats_collection.update_one(
                    {'teamID': team_id},
                    {
                        '$inc': inc_dict,
                        '$set': {
                            'updatedAt': datetime.now(timezone.utc).isoformat(),
                            'lastMatchID': self._coerce_identifier(match_id),
                        },
                        '$addToSet': {'matchIDs': self._coerce_identifier(match_id)},
                    },
                    upsert=True,
                )
                updated_teams.add(team_id)

        if processed_events == 0:
            return

        producer = await get_kafka_producer()
        stats_event = create_event(
            event_type=EventType.STATS_AGGREGATED,
            data={
                'match_id': match_id,
                'events_processed': processed_events,
                'players_updated': len(updated_players),
                'teams_updated': len(updated_teams),
            },
            source_service='statistics-service',
        )
        await producer.send_event(
            topic='statistics.events',
            event=stats_event.dict(),
            key=match_id,
        )

        logger.info(
            "Updated statistics for match %s from %s events (%s players, %s teams)",
            match_id,
            processed_events,
            len(updated_players),
            len(updated_teams),
        )

    def _build_increments(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        return EventMetricAccumulator.build_increments(raw_event)

    @staticmethod
    def _compute_analytical_xg(event: Dict[str, Any]) -> float:
        """Distance-based analytical xG fallback (no ML dependency)."""
        import math
        loc = event.get('location') or {}
        try:
            x = float(loc.get('x', 50))
            y = float(loc.get('y', 50))
            dx = (100.0 - x) / 100.0 * 105.0
            dy = (50.0 - y) / 100.0 * 68.0
            distance = math.sqrt(dx ** 2 + dy ** 2)
            raw = event.get('raw_event') or {}
            body_part = str(event.get('body_part') or raw.get('body_part', '')).lower()
            shot_type = str(event.get('shot_type') or raw.get('shot_type', '')).lower()
            base_xg = 0.35 * math.exp(-0.1 * max(distance, 1.0))
            if 'head' in body_part:
                base_xg *= 0.6
            if shot_type == 'penalty':
                base_xg = 0.76
            return round(base_xg, 4)
        except Exception:
            return 0.05

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes'}
        return False

    @staticmethod
    def _optional_float(value: Any) -> Optional[float]:
        if value in (None, '', 'None'):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _is_high_regain(cls, raw_event: Dict[str, Any]) -> bool:
        if cls._is_truthy(raw_event.get('high_regain')):
            return True

        location = raw_event.get('location') or {}
        if not isinstance(location, Mapping):
            return False

        x_value = cls._optional_float(location.get('x'))
        return x_value is not None and x_value >= 66.7

    @staticmethod
    def _coerce_identifier(value: Any) -> Any:
        text = str(value)
        return int(text) if text.isdigit() else text

    @staticmethod
    def _optional_int(value: Any) -> Optional[int]:
        if value in (None, '', 'None'):
            return None
        text = str(value)
        return int(text) if text.isdigit() else None
