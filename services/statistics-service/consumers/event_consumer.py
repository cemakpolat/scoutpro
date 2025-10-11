"""
Statistics Service Event Consumer
Consumes events from Kafka and calculates/aggregates statistics
"""
import asyncio
import logging
import sys
from typing import Dict, Any

sys.path.append('/app')

from shared.messaging import EventSubscriber, EventType, get_kafka_producer, create_event

logger = logging.getLogger(__name__)


class StatisticsEventConsumer:
    """
    Consumes events from Kafka and calculates statistics

    Listens to:
    - match.events: Calculate match statistics
    - player.events: Aggregate player statistics
    - team.events: Aggregate team statistics
    """

    def __init__(self):
        """Initialize statistics event consumer"""
        self.subscriber = EventSubscriber(
            group_id='statistics-service-consumer',
        )
        # In-memory cache for aggregations (in production, use Redis or TimescaleDB)
        self.player_stats_cache: Dict[str, Dict[str, Any]] = {}
        self.team_stats_cache: Dict[str, Dict[str, Any]] = {}

    async def start(self):
        """Start consuming events"""
        # Register event handlers
        self.subscriber.on(EventType.MATCH_ENDED)(self.handle_match_ended)
        self.subscriber.on(EventType.GOAL_SCORED)(self.handle_goal_scored)
        self.subscriber.on(EventType.ASSIST_MADE)(self.handle_assist_made)
        self.subscriber.on(EventType.CARD_ISSUED)(self.handle_card_issued)
        self.subscriber.on(EventType.SHOT_TAKEN)(self.handle_shot_taken)
        self.subscriber.on(EventType.PASS_COMPLETED)(self.handle_pass_completed)
        self.subscriber.on(EventType.PLAYER_STATS_UPDATED)(self.handle_player_stats_updated)
        self.subscriber.on(EventType.TEAM_STATS_UPDATED)(self.handle_team_stats_updated)

        # Start consuming from topics
        await self.subscriber.start([
            'match.events',
            'player.events',
            'team.events'
        ])

        logger.info("Statistics event consumer started")

    async def stop(self):
        """Stop consuming events"""
        await self.subscriber.stop()
        logger.info("Statistics event consumer stopped")

    # ============ Match Event Handlers ============

    async def handle_match_ended(self, event: dict):
        """
        Handle match ended event - trigger statistics aggregation

        When a match ends, aggregate all statistics for:
        - Players in the match
        - Teams in the match
        - Overall competition statistics
        """
        try:
            match_data = event['data']
            match_id = match_data.get('match_id')
            home_team_id = match_data.get('home_team_id')
            away_team_id = match_data.get('away_team_id')

            logger.info(f"Processing match statistics: {match_id}")

            # Aggregate player statistics
            players = match_data.get('players', [])
            for player_id in players:
                await self._aggregate_player_stats(player_id, match_id)

            # Aggregate team statistics
            await self._aggregate_team_stats(home_team_id, match_id)
            await self._aggregate_team_stats(away_team_id, match_id)

            # Publish aggregated statistics event
            producer = await get_kafka_producer()
            stats_event = create_event(
                event_type=EventType.STATS_AGGREGATED,
                data={
                    'match_id': match_id,
                    'home_team_id': home_team_id,
                    'away_team_id': away_team_id,
                    'aggregated_at': event['timestamp']
                },
                source_service='statistics-service'
            )
            await producer.send_event(
                topic='statistics.events',
                event=stats_event.dict(),
                key=match_id
            )

            logger.info(f"Successfully processed match statistics: {match_id}")

        except Exception as e:
            logger.error(f"Error handling match ended event: {e}", exc_info=True)

    # ============ Live Event Handlers ============

    async def handle_goal_scored(self, event: dict):
        """Handle goal scored event - update real-time statistics"""
        try:
            event_data = event['data']
            player_id = event_data.get('player_id')
            team_id = event_data.get('team_id')
            match_id = event_data.get('match_id')

            logger.info(f"Goal scored: player={player_id}, match={match_id}")

            # Update player goal count
            await self._increment_player_stat(player_id, 'goals', 1)

            # Update team goal count
            await self._increment_team_stat(team_id, 'goals', 1)

            logger.debug(f"Updated goal statistics for player {player_id}")

        except Exception as e:
            logger.error(f"Error handling goal scored event: {e}", exc_info=True)

    async def handle_assist_made(self, event: dict):
        """Handle assist made event - update real-time statistics"""
        try:
            event_data = event['data']
            player_id = event_data.get('player_id')

            logger.info(f"Assist made: player={player_id}")

            # Update player assist count
            await self._increment_player_stat(player_id, 'assists', 1)

            logger.debug(f"Updated assist statistics for player {player_id}")

        except Exception as e:
            logger.error(f"Error handling assist made event: {e}", exc_info=True)

    async def handle_card_issued(self, event: dict):
        """Handle card issued event - update real-time statistics"""
        try:
            event_data = event['data']
            player_id = event_data.get('player_id')
            card_type = event_data.get('card_type')  # 'yellow' or 'red'

            logger.info(f"Card issued: player={player_id}, type={card_type}")

            # Update player card count
            stat_key = 'yellow_cards' if card_type == 'yellow' else 'red_cards'
            await self._increment_player_stat(player_id, stat_key, 1)

            logger.debug(f"Updated card statistics for player {player_id}")

        except Exception as e:
            logger.error(f"Error handling card issued event: {e}", exc_info=True)

    async def handle_shot_taken(self, event: dict):
        """Handle shot taken event - update real-time statistics"""
        try:
            event_data = event['data']
            player_id = event_data.get('player_id')
            team_id = event_data.get('team_id')
            on_target = event_data.get('on_target', False)

            logger.debug(f"Shot taken: player={player_id}, on_target={on_target}")

            # Update player shot statistics
            await self._increment_player_stat(player_id, 'shots', 1)
            if on_target:
                await self._increment_player_stat(player_id, 'shots_on_target', 1)

            # Update team shot statistics
            await self._increment_team_stat(team_id, 'shots', 1)
            if on_target:
                await self._increment_team_stat(team_id, 'shots_on_target', 1)

        except Exception as e:
            logger.error(f"Error handling shot taken event: {e}", exc_info=True)

    async def handle_pass_completed(self, event: dict):
        """Handle pass completed event - update real-time statistics"""
        try:
            event_data = event['data']
            player_id = event_data.get('player_id')
            successful = event_data.get('successful', True)

            # Update player pass statistics
            await self._increment_player_stat(player_id, 'passes_attempted', 1)
            if successful:
                await self._increment_player_stat(player_id, 'passes_completed', 1)

        except Exception as e:
            logger.error(f"Error handling pass completed event: {e}", exc_info=True)

    # ============ Statistics Update Handlers ============

    async def handle_player_stats_updated(self, event: dict):
        """Handle player stats updated event"""
        try:
            player_data = event['data']
            player_id = player_data.get('player_id')

            logger.info(f"Player statistics updated: {player_id}")

            # Update cache
            self.player_stats_cache[player_id] = player_data

        except Exception as e:
            logger.error(f"Error handling player stats updated event: {e}", exc_info=True)

    async def handle_team_stats_updated(self, event: dict):
        """Handle team stats updated event"""
        try:
            team_data = event['data']
            team_id = team_data.get('team_id')

            logger.info(f"Team statistics updated: {team_id}")

            # Update cache
            self.team_stats_cache[team_id] = team_data

        except Exception as e:
            logger.error(f"Error handling team stats updated event: {e}", exc_info=True)

    # ============ Helper Methods ============

    async def _increment_player_stat(self, player_id: str, stat_key: str, value: int):
        """Increment a player statistic"""
        if player_id not in self.player_stats_cache:
            self.player_stats_cache[player_id] = {}

        current_value = self.player_stats_cache[player_id].get(stat_key, 0)
        self.player_stats_cache[player_id][stat_key] = current_value + value

        # In production, persist to TimescaleDB or Redis

    async def _increment_team_stat(self, team_id: str, stat_key: str, value: int):
        """Increment a team statistic"""
        if team_id not in self.team_stats_cache:
            self.team_stats_cache[team_id] = {}

        current_value = self.team_stats_cache[team_id].get(stat_key, 0)
        self.team_stats_cache[team_id][stat_key] = current_value + value

        # In production, persist to TimescaleDB or Redis

    async def _aggregate_player_stats(self, player_id: str, match_id: str):
        """Aggregate all statistics for a player in a match"""
        # In production, query TimescaleDB for all player events in match
        # and calculate comprehensive statistics
        logger.info(f"Aggregating stats for player {player_id} in match {match_id}")

        # Publish player stats updated event
        producer = await get_kafka_producer()
        stats_event = create_event(
            event_type=EventType.PLAYER_STATS_UPDATED,
            data={
                'player_id': player_id,
                'match_id': match_id,
                'stats': self.player_stats_cache.get(player_id, {})
            },
            source_service='statistics-service'
        )
        await producer.send_event(
            topic='player.events',
            event=stats_event.dict(),
            key=player_id
        )

    async def _aggregate_team_stats(self, team_id: str, match_id: str):
        """Aggregate all statistics for a team in a match"""
        # In production, query TimescaleDB for all team events in match
        # and calculate comprehensive statistics
        logger.info(f"Aggregating stats for team {team_id} in match {match_id}")

        # Publish team stats updated event
        producer = await get_kafka_producer()
        stats_event = create_event(
            event_type=EventType.TEAM_STATS_UPDATED,
            data={
                'team_id': team_id,
                'match_id': match_id,
                'stats': self.team_stats_cache.get(team_id, {})
            },
            source_service='statistics-service'
        )
        await producer.send_event(
            topic='team.events',
            event=stats_event.dict(),
            key=team_id
        )


# Global consumer instance
_consumer: StatisticsEventConsumer = None


async def start_consumer():
    """Start the statistics event consumer"""
    global _consumer
    _consumer = StatisticsEventConsumer()
    await _consumer.start()
    logger.info("Statistics service event consumer is running")


async def stop_consumer():
    """Stop the statistics event consumer"""
    global _consumer
    if _consumer:
        await _consumer.stop()
