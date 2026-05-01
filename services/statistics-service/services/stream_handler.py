import asyncio
import logging
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from config.settings import get_settings
from shared.messaging import KafkaConsumerClient, EventType, create_event, get_kafka_producer
from shared.utils.database import DatabaseManager

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
        event_type = str(raw_event.get('type_name', '')).strip().lower()
        increments: Dict[str, Any] = {'total_events': 1}

        if event_type == 'pass':
            increments['passes'] = 1
            if raw_event.get('is_successful'):
                increments['passes_completed'] = 1
            if self._is_truthy(raw_event.get('progressive_pass')):
                increments['progressive_passes'] = 1
            if self._is_truthy(raw_event.get('entered_final_third')):
                increments['final_third_entries'] = 1
            if self._is_truthy(raw_event.get('entered_box')):
                increments['passes_into_box'] = 1
            if self._is_truthy(raw_event.get('is_cross')) or str(raw_event.get('pass_type', '')).lower() == 'cross':
                increments['crosses'] = 1
            if self._is_truthy(raw_event.get('is_through_ball')) or str(raw_event.get('pass_type', '')).lower() == 'through_ball':
                increments['through_balls'] = 1
            if self._is_truthy(raw_event.get('is_long_ball')) or str(raw_event.get('pass_type', '')).lower() == 'long_ball':
                increments['long_balls'] = 1
            if self._is_truthy(raw_event.get('is_switch')):
                increments['switches_of_play'] = 1
            if self._is_truthy(raw_event.get('is_key_pass')) or self._is_truthy(raw_event.get('assist_potential')):
                increments['key_passes'] = 1
            if self._is_truthy(raw_event.get('is_assist')):
                increments['assists'] = 1
            if self._is_truthy(raw_event.get('is_second_assist')):
                increments['second_assists'] = 1
            if self._is_truthy(raw_event.get('is_set_piece')):
                increments['set_piece_passes'] = 1
            pass_length = self._optional_float(raw_event.get('pass_length'))
            if pass_length is not None:
                increments['pass_length_total'] = pass_length
        elif event_type == 'shot':
            increments['shots'] = 1
            if self._is_truthy(raw_event.get('is_on_target')):
                increments['shots_on_target'] = 1
            if raw_event.get('is_goal'):
                increments['goals'] = 1
            if self._is_truthy(raw_event.get('is_big_chance')):
                increments['big_chances'] = 1
            if raw_event.get('is_goal') and self._is_truthy(raw_event.get('is_big_chance')):
                increments['big_chances_scored'] = 1
            if self._is_truthy(raw_event.get('is_set_piece')):
                increments['set_piece_shots'] = 1
            xg_val = self._optional_float(raw_event.get('xg_value'))
            if xg_val is None:
                xg_val = self._optional_float(raw_event.get('analytical_xg'))
            if xg_val is None:
                xg_val = self._compute_analytical_xg(raw_event)
            increments['xG'] = xg_val
            increments['xg_total'] = xg_val
            shot_distance = self._optional_float(raw_event.get('shot_distance'))
            if shot_distance is not None:
                increments['shot_distance_total'] = shot_distance
            body_part = str(raw_event.get('body_part', '')).lower()
            if 'head' in body_part:
                increments['headed_shots'] = 1
        elif event_type == 'foul':
            increments['fouls'] = 1
        elif event_type == 'card':
            increments['cards'] = 1
            card_type = str(raw_event.get('card_type', '')).lower()
            if card_type == 'yellow':
                increments['yellow_cards'] = 1
            elif card_type == 'red':
                increments['red_cards'] = 1
        elif event_type == 'duel':
            increments['duels'] = 1
            if raw_event.get('is_successful'):
                increments['duels_won'] = 1
        elif event_type == 'take_on':
            increments['take_ons'] = 1
            if raw_event.get('is_successful'):
                increments['take_ons_won'] = 1
        elif event_type == 'interception':
            increments['interceptions'] = 1
            if self._is_high_regain(raw_event):
                increments['high_regains'] = 1
        elif event_type == 'tackle':
            increments['tackles'] = 1
            if raw_event.get('is_successful'):
                increments['tackles_won'] = 1
            if self._is_high_regain(raw_event):
                increments['high_regains'] = 1
        elif event_type == 'clearance':
            increments['clearances'] = 1
            if self._is_high_regain(raw_event):
                increments['high_regains'] = 1
        elif event_type == 'goalkeeper':
            increments['goalkeeper_actions'] = 1
            if raw_event.get('action_type') == 'save' and raw_event.get('is_successful'):
                increments['saves'] = 1
        elif event_type == 'ball_control':
            increments['ball_controls'] = 1
            action_type = str(raw_event.get('action_type', '')).lower()
            if action_type == 'recovery':
                increments['recoveries'] = 1
                if self._is_high_regain(raw_event):
                    increments['high_regains'] = 1
            elif action_type == 'dispossessed':
                increments['dispossessions'] = 1
        else:
            safe_event_name = re.sub(r'[^a-z0-9]+', '_', event_type).strip('_')
            if safe_event_name:
                increments[f'event_{safe_event_name}'] = 1

        return increments

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
