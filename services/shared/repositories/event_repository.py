"""
Event Repository

Repository for storing and retrieving event data from MongoDB.
Events are the highest volume data type, so this repository includes
optimizations for bulk operations and efficient querying.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
from dataclasses import asdict

from shared.domain.models import ScoutProEvent, EventType, EventQuality
from shared.domain.models.attributes import PassAttributes, ShotAttributes, DefensiveAttributes
from shared.repositories.base_repository import BaseRepository


class EventRepository(BaseRepository[ScoutProEvent]):
    """
    Repository for event entities

    Provides:
    - CRUD operations for events
    - Filter by match, player, team, event type
    - Time-based queries
    - Aggregation queries for analytics

    Usage:
        repo = EventRepository()

        # Create event
        event = ScoutProEvent(...)
        repo.create(event)

        # Find by match
        events = repo.find_by_match('match_123')

        # Find by player
        events = repo.find_by_player('player_123')

        # Find passes
        passes = repo.find_by_event_type(EventType.PASS_COMPLETED)
    """

    def get_collection_name(self) -> str:
        return "events"

    def create_indexes(self):
        """Create MongoDB indexes for event collection"""
        if self._collection is None:
            return

        # Match index (CRITICAL - most common query)
        self._collection.create_index([('match_id', ASCENDING)])

        # Player index (for player analysis)
        self._collection.create_index([('player_id', ASCENDING)])

        # Team index (for team analysis)
        self._collection.create_index([('team_id', ASCENDING)])

        # Event type index (for filtering by type)
        self._collection.create_index([('event_type', ASCENDING)])

        # Time index (for temporal queries)
        self._collection.create_index([('timestamp_seconds', ASCENDING)])
        self._collection.create_index([('period', ASCENDING), ('minute', ASCENDING)])

        # Compound indexes for common queries
        self._collection.create_index([('match_id', ASCENDING), ('period', ASCENDING), ('timestamp_seconds', ASCENDING)])
        self._collection.create_index([('match_id', ASCENDING), ('event_type', ASCENDING)])
        self._collection.create_index([('player_id', ASCENDING), ('event_type', ASCENDING)])

        # Provider IDs (for lookups)
        self._collection.create_index([('provider_ids.opta', ASCENDING)])
        self._collection.create_index([('provider_ids.statsbomb', ASCENDING)])

        # Quality index
        self._collection.create_index([('quality_level', ASCENDING)])

        # Updated timestamp (for sync)
        self._collection.create_index([('updated_at', ASCENDING)])

    def to_document(self, event: ScoutProEvent) -> Dict[str, Any]:
        """
        Convert ScoutProEvent to MongoDB document

        Args:
            event: Event to convert

        Returns:
            MongoDB document
        """
        doc = {
            '_id': event.id,
            'match_id': event.match_id,
            'event_type': event.event_type.name if isinstance(event.event_type, EventType) else event.event_type,
            'minute': event.minute,
            'second': event.second,
            'period': event.period,
            'timestamp_seconds': event.timestamp_seconds,
            'player_id': event.player_id,
            'team_id': event.team_id,
            'x': event.x,
            'y': event.y,
            'end_x': event.end_x,
            'end_y': event.end_y,
            'successful': event.successful,
            'quality_level': event.quality_level.name if isinstance(event.quality_level, EventQuality) else event.quality_level,
            'provider': event.provider,
            'external_id': event.external_id,
            'provider_ids': event.provider_ids or {},
            'provider_data': event.provider_data or {},
            'data_quality': event.data_quality or {},
            'created_at': event.created_at,
            'updated_at': event.updated_at
        }

        # Rich attributes (stored as nested documents)
        if event.pass_attrs:
            doc['pass_attrs'] = asdict(event.pass_attrs)
        if event.shot_attrs:
            doc['shot_attrs'] = asdict(event.shot_attrs)
        if event.defensive_attrs:
            doc['defensive_attrs'] = asdict(event.defensive_attrs)

        return doc

    def from_document(self, doc: Dict[str, Any]) -> ScoutProEvent:
        """
        Convert MongoDB document to ScoutProEvent

        Args:
            doc: MongoDB document

        Returns:
            ScoutProEvent instance
        """
        # Parse event type
        event_type_val = doc.get('event_type')
        if isinstance(event_type_val, str):
            try:
                event_type = EventType[event_type_val]
            except KeyError:
                event_type = EventType.OTHER
        else:
            event_type = event_type_val

        # Parse quality level
        quality_level_val = doc.get('quality_level', EventQuality.BASIC.name)
        if isinstance(quality_level_val, str):
            try:
                quality_level = EventQuality[quality_level_val]
            except KeyError:
                quality_level = EventQuality.BASIC
        else:
            quality_level = quality_level_val

        # Parse rich attributes
        pass_attrs = None
        if 'pass_attrs' in doc and doc['pass_attrs']:
            pass_attrs = PassAttributes(**doc['pass_attrs'])

        shot_attrs = None
        if 'shot_attrs' in doc and doc['shot_attrs']:
            shot_attrs = ShotAttributes(**doc['shot_attrs'])

        defensive_attrs = None
        if 'defensive_attrs' in doc and doc['defensive_attrs']:
            defensive_attrs = DefensiveAttributes(**doc['defensive_attrs'])

        event = ScoutProEvent(
            id=doc['_id'],
            match_id=doc.get('match_id', 0),
            event_type=event_type,
            minute=doc.get('minute', 0),
            second=doc.get('second', 0),
            period=doc.get('period', 1),
            timestamp_seconds=doc.get('timestamp_seconds', 0),
            player_id=doc.get('player_id'),
            team_id=doc.get('team_id'),
            x=doc.get('x'),
            y=doc.get('y'),
            end_x=doc.get('end_x'),
            end_y=doc.get('end_y'),
            successful=doc.get('successful', True),
            quality_level=quality_level,
            pass_attrs=pass_attrs,
            shot_attrs=shot_attrs,
            defensive_attrs=defensive_attrs,
            provider=doc.get('provider', 'canonical'),
            external_id=doc.get('external_id'),
            provider_ids=doc.get('provider_ids', {}),
            provider_data=doc.get('provider_data', {}),
            data_quality=doc.get('data_quality', {}),
            created_at=doc.get('created_at', datetime.now()),
            updated_at=doc.get('updated_at', datetime.now())
        )

        return event

    # ========================================
    # EVENT-SPECIFIC QUERIES
    # ========================================

    def find_by_match(
        self,
        match_id: str,
        limit: Optional[int] = None
    ) -> List[ScoutProEvent]:
        """
        Find all events for a match

        Args:
            match_id: Match ID
            limit: Max results

        Returns:
            List of events sorted by timestamp

        Example:
            events = repo.find_by_match('match_123')
        """
        return self.find(
            {'match_id': match_id},
            limit=limit,
            sort=[('period', ASCENDING), ('timestamp_seconds', ASCENDING)]
        )

    def find_by_player(
        self,
        player_id: str,
        limit: Optional[int] = None
    ) -> List[ScoutProEvent]:
        """
        Find all events for a player

        Args:
            player_id: Player ID
            limit: Max results

        Returns:
            List of events

        Example:
            events = repo.find_by_player('player_123', limit=100)
        """
        return self.find({'player_id': player_id}, limit=limit)

    def find_by_team(
        self,
        team_id: str,
        limit: Optional[int] = None
    ) -> List[ScoutProEvent]:
        """
        Find all events for a team

        Args:
            team_id: Team ID
            limit: Max results

        Returns:
            List of events

        Example:
            events = repo.find_by_team('team_123', limit=100)
        """
        return self.find({'team_id': team_id}, limit=limit)

    def find_by_event_type(
        self,
        event_type: EventType,
        limit: Optional[int] = None
    ) -> List[ScoutProEvent]:
        """
        Find events by type

        Args:
            event_type: Event type
            limit: Max results

        Returns:
            List of events

        Example:
            passes = repo.find_by_event_type(EventType.PASS_COMPLETED)
        """
        query = {'event_type': event_type.name}
        return self.find(query, limit=limit)

    def find_by_match_and_type(
        self,
        match_id: str,
        event_type: EventType,
        limit: Optional[int] = None
    ) -> List[ScoutProEvent]:
        """
        Find events by match and type

        Args:
            match_id: Match ID
            event_type: Event type
            limit: Max results

        Returns:
            List of events

        Example:
            # Get all passes in match
            passes = repo.find_by_match_and_type('match_123', EventType.PASS_COMPLETED)
        """
        query = {
            'match_id': match_id,
            'event_type': event_type.name
        }
        return self.find(query, limit=limit, sort=[('timestamp_seconds', ASCENDING)])

    def find_by_player_and_type(
        self,
        player_id: str,
        event_type: EventType,
        limit: Optional[int] = None
    ) -> List[ScoutProEvent]:
        """
        Find events by player and type

        Args:
            player_id: Player ID
            event_type: Event type
            limit: Max results

        Returns:
            List of events

        Example:
            # Get all shots by player
            shots = repo.find_by_player_and_type('player_123', EventType.SHOT_ON_TARGET)
        """
        query = {
            'player_id': player_id,
            'event_type': event_type.name
        }
        return self.find(query, limit=limit)

    def find_by_time_range(
        self,
        match_id: str,
        start_time: int,
        end_time: int
    ) -> List[ScoutProEvent]:
        """
        Find events in a time range (seconds)

        Args:
            match_id: Match ID
            start_time: Start time in seconds
            end_time: End time in seconds

        Returns:
            List of events

        Example:
            # Get events from minute 10 to 20
            events = repo.find_by_time_range('match_123', 600, 1200)
        """
        query = {
            'match_id': match_id,
            'timestamp_seconds': {
                '$gte': start_time,
                '$lte': end_time
            }
        }
        return self.find(query, sort=[('timestamp_seconds', ASCENDING)])

    def find_passes_with_attrs(
        self,
        match_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ScoutProEvent]:
        """
        Find pass events that have pass attributes

        Args:
            match_id: Match ID (optional)
            limit: Max results

        Returns:
            List of pass events with attributes

        Example:
            passes = repo.find_passes_with_attrs('match_123')
        """
        query = {'pass_attrs': {'$exists': True, '$ne': None}}

        if match_id:
            query['match_id'] = match_id

        return self.find(query, limit=limit)

    def find_shots_with_attrs(
        self,
        match_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ScoutProEvent]:
        """
        Find shot events that have shot attributes

        Args:
            match_id: Match ID (optional)
            limit: Max results

        Returns:
            List of shot events with attributes

        Example:
            shots = repo.find_shots_with_attrs('match_123')
        """
        query = {'shot_attrs': {'$exists': True, '$ne': None}}

        if match_id:
            query['match_id'] = match_id

        return self.find(query, limit=limit)

    # ========================================
    # BULK OPERATIONS
    # ========================================

    def bulk_create_match_events(self, match_id: str, events: List[ScoutProEvent]) -> int:
        """
        Bulk create events for a match (optimized)

        Args:
            match_id: Match ID
            events: List of events

        Returns:
            Number of events created

        Example:
            events = [ScoutProEvent(...), ScoutProEvent(...), ...]
            count = repo.bulk_create_match_events('match_123', events)
        """
        if not events:
            return 0

        # Ensure all events have correct match_id
        for event in events:
            event.match_id = match_id

        return len(self.create_many(events))

    def delete_match_events(self, match_id: str) -> int:
        """
        Delete all events for a match

        Args:
            match_id: Match ID

        Returns:
            Number of events deleted

        Example:
            count = repo.delete_match_events('match_123')
        """
        return self.delete_many({'match_id': match_id})

    # ========================================
    # AGGREGATION QUERIES
    # ========================================

    def get_event_type_distribution(self, match_id: str) -> Dict[str, int]:
        """
        Get distribution of event types in a match

        Args:
            match_id: Match ID

        Returns:
            Dict of event_type → count

        Example:
            dist = repo.get_event_type_distribution('match_123')
            → {'PASS_COMPLETED': 523, 'PASS_INCOMPLETE': 87, ...}
        """
        self._connect()

        pipeline = [
            {'$match': {'match_id': match_id}},
            {'$group': {'_id': '$event_type', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]

        results = self._collection.aggregate(pipeline)

        return {r['_id']: r['count'] for r in results if r['_id']}

    def get_player_event_counts(self, match_id: str) -> List[Dict[str, Any]]:
        """
        Get event counts per player in a match

        Args:
            match_id: Match ID

        Returns:
            List of {player_id, count} dicts

        Example:
            counts = repo.get_player_event_counts('match_123')
            → [{'player_id': 'player_123', 'count': 89}, ...]
        """
        self._connect()

        pipeline = [
            {'$match': {'match_id': match_id, 'player_id': {'$ne': None}}},
            {'$group': {'_id': '$player_id', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$project': {'player_id': '$_id', 'count': 1, '_id': 0}}
        ]

        return list(self._collection.aggregate(pipeline))

    def get_pass_completion_rate(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        match_id: Optional[str] = None
    ) -> float:
        """
        Calculate pass completion rate

        Args:
            player_id: Player ID (optional)
            team_id: Team ID (optional)
            match_id: Match ID (optional)

        Returns:
            Pass completion rate (0.0 to 1.0)

        Example:
            rate = repo.get_pass_completion_rate(player_id='player_123')
            → 0.87 (87% pass completion)
        """
        self._connect()

        query: Dict[str, Any] = {
            'event_type': {'$in': [EventType.PASS_COMPLETED.name, EventType.PASS_INCOMPLETE.name]}
        }

        if player_id:
            query['player_id'] = player_id
        if team_id:
            query['team_id'] = team_id
        if match_id:
            query['match_id'] = match_id

        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': None,
                'total': {'$sum': 1},
                'completed': {
                    '$sum': {
                        '$cond': [{'$eq': ['$event_type', EventType.PASS_COMPLETED.name]}, 1, 0]
                    }
                }
            }}
        ]

        results = list(self._collection.aggregate(pipeline))

        if results and results[0]['total'] > 0:
            return results[0]['completed'] / results[0]['total']

        return 0.0

    def count_by_match(self, match_id: str) -> int:
        """
        Count events in a match

        Args:
            match_id: Match ID

        Returns:
            Event count

        Example:
            count = repo.count_by_match('match_123')
            → 1523
        """
        return self.count({'match_id': match_id})
