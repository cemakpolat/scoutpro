import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from config.settings import get_settings
from shared.messaging import KafkaConsumerClient, EventType, create_event, get_kafka_producer
from shared.utils.database import DatabaseManager

logger = logging.getLogger(__name__)


class MatchStreamProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.db_manager = DatabaseManager()
        self.mongo_db = None
        self.matches_collection = None
        self.events_collection = None
        self.running = False
        self.consumer = KafkaConsumerClient(
            topics=['raw.events'],
            group_id='match.stream.processor',
        )

    async def start(self):
        self.mongo_db = await self.db_manager.connect_mongodb(
            self.settings.mongodb_url,
            self.settings.mongodb_database,
        )
        self.matches_collection = self.mongo_db['matches']
        self.events_collection = self.mongo_db['match_events']

        self.running = True
        await self.consumer.start()
        asyncio.create_task(self._process_loop())
        logger.info("MatchStreamProcessor started")

    async def stop(self):
        self.running = False
        await self.consumer.stop()
        await self.db_manager.close_all()
        logger.info("MatchStreamProcessor stopped")

    async def _process_loop(self):
        async for event in self.consumer.consume():
            if not self.running:
                break

            try:
                await self.process_event(event)
            except Exception as e:
                logger.error(f"Failed to process event: {e}", exc_info=True)

    async def process_event(self, event_data: Dict[str, Any]):
        match_id = str(event_data.get('match_id') or event_data.get('payload', {}).get('match_id') or '')
        payload = event_data.get('payload', {})
        events = payload.get('events', [])

        if not match_id or not isinstance(events, list) or not events:
            logger.debug("Skipping raw event envelope without match_id/events")
            return

        match_key = str(match_id)
        existing_match = await self.matches_collection.find_one({'uID': {'$in': [match_key, self._coerce_identifier(match_key)]}}) or {}
        team_ids = self._collect_team_ids(events)

        home_team_id = str(existing_match.get('homeTeamID') or (team_ids[0] if team_ids else '0'))
        away_team_id = str(existing_match.get('awayTeamID') or (team_ids[1] if len(team_ids) > 1 else '0'))
        home_score = int(existing_match.get('homeScore', 0) or 0)
        away_score = int(existing_match.get('awayScore', 0) or 0)

        new_events = 0
        for raw_event in events:
            event_doc = self._normalize_event_doc(match_key, raw_event)
            result = await self.events_collection.update_one(
                {'matchID': match_key, 'event_id': event_doc['event_id']},
                {'$set': event_doc},
                upsert=True,
            )

            if result.upserted_id:
                new_events += 1
                if event_doc.get('is_goal'):
                    if str(event_doc.get('team_id')) == home_team_id:
                        home_score += 1
                    elif str(event_doc.get('team_id')) == away_team_id:
                        away_score += 1

        if new_events == 0 and existing_match:
            return

        match_doc = {
            'uID': match_key,
            'homeTeamID': home_team_id,
            'awayTeamID': away_team_id,
            'homeScore': home_score,
            'awayScore': away_score,
            'date': existing_match.get('date') or datetime.now(timezone.utc).isoformat(),
            'status': 'live',
            'updatedAt': datetime.now(timezone.utc).isoformat(),
        }

        await self.matches_collection.update_one(
            {'uID': match_key},
            {'$set': match_doc},
            upsert=True,
        )

        producer = await get_kafka_producer()
        lifecycle_event = create_event(
            event_type=EventType.MATCH_CREATED if not existing_match else EventType.MATCH_UPDATED,
            data={
                'match_id': str(match_key),
                'match': match_doc,
                'new_events': new_events,
            },
            source_service='match-service',
        )
        await producer.send_event(
            topic='match.events',
            event=lifecycle_event.dict(),
            key=str(match_key),
        )

        logger.info("Persisted %s new match events for %s", new_events, match_id)

    @staticmethod
    def _coerce_identifier(value: Any) -> Any:
        text = str(value)
        return int(text) if text.isdigit() else text

    def _collect_team_ids(self, events: list[Dict[str, Any]]) -> list[int]:
        seen: list[int] = []
        for raw_event in events:
            team_id = self._optional_int(raw_event.get('team_id'))
            if team_id is not None and team_id not in seen:
                seen.append(team_id)
        return seen

    def _normalize_event_doc(self, match_key: Any, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        minute = self._optional_int(raw_event.get('minute')) or 0
        second = self._optional_int(raw_event.get('second')) or 0
        event_id = str(raw_event.get('event_id') or raw_event.get('id') or f"{match_key}-{minute}-{second}-{raw_event.get('type_name', 'event')}")

        preserved_fields = {
            key: value
            for key, value in raw_event.items()
            if key not in {
                'event_id',
                'matchID',
                'match_id',
                'player_id',
                'team_id',
                'minute',
                'second',
                'period',
                'type_name',
                'provider',
                'location',
                'end_location',
                'qualifiers',
                'is_goal',
                'is_successful',
                'timestamp_seconds',
                'timestamp',
                'ingested_at',
                'raw_event',
            }
        }

        return {
            **preserved_fields,
            'event_id': event_id,
            'matchID': str(match_key),
            'match_id': str(match_key),
            'player_id': self._optional_int(raw_event.get('player_id')),
            'team_id': self._optional_int(raw_event.get('team_id')),
            'minute': minute,
            'second': second,
            'period': self._optional_int(raw_event.get('period')) or 0,
            'type_name': raw_event.get('type_name'),
            'provider': raw_event.get('provider'),
            'location': raw_event.get('location'),
            'end_location': raw_event.get('end_location'),
            'qualifiers': raw_event.get('qualifiers', {}),
            'is_goal': bool(raw_event.get('is_goal', False)),
            'is_successful': raw_event.get('is_successful'),
            'timestamp_seconds': raw_event.get('timestamp_seconds', minute * 60 + second),
            'timestamp': minute * 60 + second,
            'ingested_at': datetime.now(timezone.utc).isoformat(),
            'raw_event': raw_event,
        }

    @staticmethod
    def _optional_int(value: Any) -> Optional[int]:
        if value in (None, '', 'None'):
            return None
        text = str(value)
        return int(text) if text.isdigit() else None

