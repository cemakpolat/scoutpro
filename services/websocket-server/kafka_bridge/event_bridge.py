"""
Kafka-WebSocket Event Bridge
Consumes events from Kafka and broadcasts them to WebSocket clients
"""
import asyncio
import logging
import sys
from typing import Dict, Any

sys.path.append('/app')

from shared.messaging import EventSubscriber, EventType
from websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)


class KafkaWebSocketBridge:
    """
    Bridges Kafka events to WebSocket clients

    Consumes events from Kafka topics and broadcasts them to
    subscribed WebSocket clients based on topic subscriptions.

    Topic Mappings:
    - match.events -> live.match.{match_id}
    - player.events -> live.player.{player_id}
    - team.events -> live.team.{team_id}
    - statistics.events -> live.statistics
    """

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize Kafka-WebSocket bridge

        Args:
            connection_manager: WebSocket connection manager
        """
        self.connection_manager = connection_manager
        self.subscriber = EventSubscriber(
            group_id='websocket-bridge-consumer'
        )
        self._running = False

    async def start(self):
        """Start the bridge"""
        # Register event handlers
        # Match events
        self.subscriber.on(EventType.MATCH_STARTED)(self.handle_match_event)
        self.subscriber.on(EventType.MATCH_UPDATED)(self.handle_match_event)
        self.subscriber.on(EventType.MATCH_ENDED)(self.handle_match_event)
        self.subscriber.on(EventType.GOAL_SCORED)(self.handle_live_event)
        self.subscriber.on(EventType.ASSIST_MADE)(self.handle_live_event)
        self.subscriber.on(EventType.CARD_ISSUED)(self.handle_live_event)
        self.subscriber.on(EventType.SUBSTITUTION_MADE)(self.handle_live_event)
        self.subscriber.on(EventType.SHOT_TAKEN)(self.handle_live_event)
        self.subscriber.on(EventType.PASS_COMPLETED)(self.handle_live_event)

        # Player events
        self.subscriber.on(EventType.PLAYER_CREATED)(self.handle_player_event)
        self.subscriber.on(EventType.PLAYER_UPDATED)(self.handle_player_event)
        self.subscriber.on(EventType.PLAYER_STATS_UPDATED)(self.handle_player_event)

        # Team events
        self.subscriber.on(EventType.TEAM_CREATED)(self.handle_team_event)
        self.subscriber.on(EventType.TEAM_UPDATED)(self.handle_team_event)
        self.subscriber.on(EventType.TEAM_STATS_UPDATED)(self.handle_team_event)
        self.subscriber.on(EventType.TEAM_STANDINGS_UPDATED)(self.handle_team_event)

        # Statistics events
        self.subscriber.on(EventType.STATS_AGGREGATED)(self.handle_stats_event)
        self.subscriber.on(EventType.STATS_CALCULATED)(self.handle_stats_event)

        # ML events
        self.subscriber.on(EventType.ML_PREDICTION_COMPLETED)(self.handle_ml_event)

        # Start consuming from all topics
        await self.subscriber.start([
            'match.events',
            'player.events',
            'team.events',
            'statistics.events',
            'ml.events'
        ])

        self._running = True
        logger.info("Kafka-WebSocket bridge started")

    async def stop(self):
        """Stop the bridge"""
        self._running = False
        await self.subscriber.stop()
        logger.info("Kafka-WebSocket bridge stopped")

    # ============ Event Handlers ============

    async def handle_match_event(self, event: Dict[str, Any]):
        """
        Handle match events and broadcast to subscribers

        Routes events to:
        - live.match.{match_id} - specific match subscribers
        - live.matches - all matches subscribers
        """
        try:
            event_type = event['event_type']
            match_id = event['data'].get('match_id')

            logger.info(f"Broadcasting match event: {event_type} for match {match_id}")

            # Broadcast to specific match subscribers
            if match_id:
                await self.connection_manager.broadcast_to_topic(
                    f"live.match.{match_id}",
                    {
                        'type': 'match_event',
                        'event_type': event_type,
                        'data': event['data'],
                        'timestamp': event['timestamp']
                    }
                )

            # Broadcast to all matches subscribers
            await self.connection_manager.broadcast_to_topic(
                "live.matches",
                {
                    'type': 'match_event',
                    'event_type': event_type,
                    'data': event['data'],
                    'timestamp': event['timestamp']
                }
            )

        except Exception as e:
            logger.error(f"Error handling match event: {e}", exc_info=True)

    async def handle_live_event(self, event: Dict[str, Any]):
        """
        Handle live match events (goals, cards, etc.)

        Routes events to:
        - live.match.{match_id} - specific match subscribers
        - live.events - all live events subscribers
        """
        try:
            event_type = event['event_type']
            match_id = event['data'].get('match_id')
            player_id = event['data'].get('player_id')

            logger.info(f"Broadcasting live event: {event_type} in match {match_id}")

            # Broadcast to specific match subscribers
            if match_id:
                await self.connection_manager.broadcast_to_topic(
                    f"live.match.{match_id}",
                    {
                        'type': 'live_event',
                        'event_type': event_type,
                        'data': event['data'],
                        'timestamp': event['timestamp']
                    }
                )

            # Broadcast to all live events subscribers
            await self.connection_manager.broadcast_to_topic(
                "live.events",
                {
                    'type': 'live_event',
                    'event_type': event_type,
                    'data': event['data'],
                    'timestamp': event['timestamp']
                }
            )

            # Also broadcast to player subscribers if applicable
            if player_id:
                await self.connection_manager.broadcast_to_topic(
                    f"live.player.{player_id}",
                    {
                        'type': 'player_event',
                        'event_type': event_type,
                        'data': event['data'],
                        'timestamp': event['timestamp']
                    }
                )

        except Exception as e:
            logger.error(f"Error handling live event: {e}", exc_info=True)

    async def handle_player_event(self, event: Dict[str, Any]):
        """
        Handle player events and broadcast to subscribers

        Routes events to:
        - live.player.{player_id} - specific player subscribers
        - live.players - all players subscribers
        """
        try:
            event_type = event['event_type']
            player_id = event['data'].get('player_id')

            logger.info(f"Broadcasting player event: {event_type} for player {player_id}")

            # Broadcast to specific player subscribers
            if player_id:
                await self.connection_manager.broadcast_to_topic(
                    f"live.player.{player_id}",
                    {
                        'type': 'player_event',
                        'event_type': event_type,
                        'data': event['data'],
                        'timestamp': event['timestamp']
                    }
                )

            # Broadcast to all players subscribers
            await self.connection_manager.broadcast_to_topic(
                "live.players",
                {
                    'type': 'player_event',
                    'event_type': event_type,
                    'data': event['data'],
                    'timestamp': event['timestamp']
                }
            )

        except Exception as e:
            logger.error(f"Error handling player event: {e}", exc_info=True)

    async def handle_team_event(self, event: Dict[str, Any]):
        """
        Handle team events and broadcast to subscribers

        Routes events to:
        - live.team.{team_id} - specific team subscribers
        - live.teams - all teams subscribers
        """
        try:
            event_type = event['event_type']
            team_id = event['data'].get('team_id')

            logger.info(f"Broadcasting team event: {event_type} for team {team_id}")

            # Broadcast to specific team subscribers
            if team_id:
                await self.connection_manager.broadcast_to_topic(
                    f"live.team.{team_id}",
                    {
                        'type': 'team_event',
                        'event_type': event_type,
                        'data': event['data'],
                        'timestamp': event['timestamp']
                    }
                )

            # Broadcast to all teams subscribers
            await self.connection_manager.broadcast_to_topic(
                "live.teams",
                {
                    'type': 'team_event',
                    'event_type': event_type,
                    'data': event['data'],
                    'timestamp': event['timestamp']
                }
            )

        except Exception as e:
            logger.error(f"Error handling team event: {e}", exc_info=True)

    async def handle_stats_event(self, event: Dict[str, Any]):
        """
        Handle statistics events and broadcast to subscribers

        Routes events to:
        - live.statistics - all statistics subscribers
        """
        try:
            event_type = event['event_type']

            logger.info(f"Broadcasting statistics event: {event_type}")

            # Broadcast to statistics subscribers
            await self.connection_manager.broadcast_to_topic(
                "live.statistics",
                {
                    'type': 'statistics_event',
                    'event_type': event_type,
                    'data': event['data'],
                    'timestamp': event['timestamp']
                }
            )

        except Exception as e:
            logger.error(f"Error handling statistics event: {e}", exc_info=True)

    async def handle_ml_event(self, event: Dict[str, Any]):
        """
        Handle ML events and broadcast to subscribers

        Routes events to:
        - live.ml - all ML subscribers
        """
        try:
            event_type = event['event_type']

            logger.info(f"Broadcasting ML event: {event_type}")

            # Broadcast to ML subscribers
            await self.connection_manager.broadcast_to_topic(
                "live.ml",
                {
                    'type': 'ml_event',
                    'event_type': event_type,
                    'data': event['data'],
                    'timestamp': event['timestamp']
                }
            )

        except Exception as e:
            logger.error(f"Error handling ML event: {e}", exc_info=True)


# Global bridge instance
_bridge: KafkaWebSocketBridge = None


async def start_bridge(connection_manager: ConnectionManager):
    """Start the Kafka-WebSocket bridge"""
    global _bridge
    _bridge = KafkaWebSocketBridge(connection_manager)
    await _bridge.start()
    logger.info("Kafka-WebSocket bridge is running")


async def stop_bridge():
    """Stop the Kafka-WebSocket bridge"""
    global _bridge
    if _bridge:
        await _bridge.stop()
