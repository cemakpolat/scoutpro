"""
Search Service Event Consumer
Consumes events from Kafka and indexes them in Elasticsearch
"""
import asyncio
import logging
import sys

sys.path.append('/app')

from shared.messaging import EventSubscriber, EventType
from search.elasticsearch_client import ElasticsearchClient

logger = logging.getLogger(__name__)


class SearchEventConsumer:
    """
    Consumes events from Kafka and indexes them in Elasticsearch

    Listens to:
    - player.events: Index player data changes
    - team.events: Index team data changes
    - match.events: Index match data changes
    """

    def __init__(self):
        """Initialize search event consumer"""
        self.subscriber = EventSubscriber(
            group_id='search-service-consumer',
        )
        self.es_client = ElasticsearchClient()

    async def start(self):
        """Start consuming events"""
        # Register event handlers
        self.subscriber.on(EventType.PLAYER_CREATED)(self.handle_player_created)
        self.subscriber.on(EventType.PLAYER_UPDATED)(self.handle_player_updated)
        self.subscriber.on(EventType.TEAM_CREATED)(self.handle_team_created)
        self.subscriber.on(EventType.TEAM_UPDATED)(self.handle_team_updated)
        self.subscriber.on(EventType.MATCH_CREATED)(self.handle_match_created)
        self.subscriber.on(EventType.MATCH_UPDATED)(self.handle_match_updated)
        self.subscriber.on(EventType.MATCH_ENDED)(self.handle_match_ended)

        # Start consuming from topics
        await self.subscriber.start([
            'player.events',
            'team.events',
            'match.events'
        ])

        logger.info("Search event consumer started")

    async def stop(self):
        """Stop consuming events"""
        await self.subscriber.stop()
        logger.info("Search event consumer stopped")

    # ============ Player Event Handlers ============

    async def handle_player_created(self, event: dict):
        """Handle player created event"""
        try:
            player_data = event['data']
            player_id = player_data.get('player_id')

            logger.info(f"Indexing new player: {player_id}")

            # Index player in Elasticsearch
            await self.es_client.index_document(
                index='players',
                document_id=player_id,
                document={
                    'player_id': player_id,
                    'name': player_data.get('name'),
                    'team': player_data.get('team'),
                    'position': player_data.get('position'),
                    'nationality': player_data.get('nationality'),
                    'age': player_data.get('age'),
                    'indexed_at': event['timestamp']
                }
            )

            logger.info(f"Successfully indexed player: {player_id}")

        except Exception as e:
            logger.error(f"Error handling player created event: {e}", exc_info=True)

    async def handle_player_updated(self, event: dict):
        """Handle player updated event"""
        try:
            player_data = event['data']
            player_id = player_data.get('player_id')

            logger.info(f"Updating player index: {player_id}")

            # Update player in Elasticsearch
            await self.es_client.update_document(
                index='players',
                document_id=player_id,
                document={
                    'name': player_data.get('name'),
                    'team': player_data.get('team'),
                    'position': player_data.get('position'),
                    'nationality': player_data.get('nationality'),
                    'age': player_data.get('age'),
                    'updated_at': event['timestamp']
                }
            )

            logger.info(f"Successfully updated player: {player_id}")

        except Exception as e:
            logger.error(f"Error handling player updated event: {e}", exc_info=True)

    # ============ Team Event Handlers ============

    async def handle_team_created(self, event: dict):
        """Handle team created event"""
        try:
            team_data = event['data']
            team_id = team_data.get('team_id')

            logger.info(f"Indexing new team: {team_id}")

            # Index team in Elasticsearch
            await self.es_client.index_document(
                index='teams',
                document_id=team_id,
                document={
                    'team_id': team_id,
                    'name': team_data.get('name'),
                    'country': team_data.get('country'),
                    'league': team_data.get('league'),
                    'stadium': team_data.get('stadium'),
                    'indexed_at': event['timestamp']
                }
            )

            logger.info(f"Successfully indexed team: {team_id}")

        except Exception as e:
            logger.error(f"Error handling team created event: {e}", exc_info=True)

    async def handle_team_updated(self, event: dict):
        """Handle team updated event"""
        try:
            team_data = event['data']
            team_id = team_data.get('team_id')

            logger.info(f"Updating team index: {team_id}")

            # Update team in Elasticsearch
            await self.es_client.update_document(
                index='teams',
                document_id=team_id,
                document={
                    'name': team_data.get('name'),
                    'country': team_data.get('country'),
                    'league': team_data.get('league'),
                    'stadium': team_data.get('stadium'),
                    'updated_at': event['timestamp']
                }
            )

            logger.info(f"Successfully updated team: {team_id}")

        except Exception as e:
            logger.error(f"Error handling team updated event: {e}", exc_info=True)

    # ============ Match Event Handlers ============

    async def handle_match_created(self, event: dict):
        """Handle match created event"""
        try:
            match_data = event['data']
            match_id = match_data.get('match_id')

            logger.info(f"Indexing new match: {match_id}")

            # Index match in Elasticsearch
            await self.es_client.index_document(
                index='matches',
                document_id=match_id,
                document={
                    'match_id': match_id,
                    'home_team': match_data.get('home_team'),
                    'away_team': match_data.get('away_team'),
                    'competition': match_data.get('competition'),
                    'date': match_data.get('date'),
                    'venue': match_data.get('venue'),
                    'status': 'scheduled',
                    'indexed_at': event['timestamp']
                }
            )

            logger.info(f"Successfully indexed match: {match_id}")

        except Exception as e:
            logger.error(f"Error handling match created event: {e}", exc_info=True)

    async def handle_match_updated(self, event: dict):
        """Handle match updated event"""
        try:
            match_data = event['data']
            match_id = match_data.get('match_id')

            logger.info(f"Updating match index: {match_id}")

            # Update match in Elasticsearch
            await self.es_client.update_document(
                index='matches',
                document_id=match_id,
                document={
                    'home_score': match_data.get('home_score'),
                    'away_score': match_data.get('away_score'),
                    'status': match_data.get('status'),
                    'minute': match_data.get('minute'),
                    'updated_at': event['timestamp']
                }
            )

            logger.info(f"Successfully updated match: {match_id}")

        except Exception as e:
            logger.error(f"Error handling match updated event: {e}", exc_info=True)

    async def handle_match_ended(self, event: dict):
        """Handle match ended event"""
        try:
            match_data = event['data']
            match_id = match_data.get('match_id')

            logger.info(f"Finalizing match index: {match_id}")

            # Update match status to completed
            await self.es_client.update_document(
                index='matches',
                document_id=match_id,
                document={
                    'home_score': match_data.get('home_score'),
                    'away_score': match_data.get('away_score'),
                    'status': 'completed',
                    'completed_at': event['timestamp']
                }
            )

            logger.info(f"Successfully finalized match: {match_id}")

        except Exception as e:
            logger.error(f"Error handling match ended event: {e}", exc_info=True)


# Global consumer instance
_consumer: SearchEventConsumer = None


async def start_consumer():
    """Start the search event consumer"""
    global _consumer
    _consumer = SearchEventConsumer()
    await _consumer.start()
    logger.info("Search service event consumer is running")


async def stop_consumer():
    """Stop the search event consumer"""
    global _consumer
    if _consumer:
        await _consumer.stop()
