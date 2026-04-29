"""
Event Syncer

Synchronizes event data from providers to canonical repository.
Events are high-volume data, so this syncer includes optimizations for bulk operations.
"""

from typing import List, Optional, Dict, Any

from shared.domain.models import ScoutProEvent
from shared.repositories import EventRepository
from shared.merger import EventMerger
from sync.base_syncer import BaseSyncer


class EventSyncer(BaseSyncer[ScoutProEvent]):
    """
    Synchronizes event data

    Note: Events are not resolved across providers (too many to fuzzy match).
    Instead, events are correlated during merge if multiple providers are synced.

    Usage:
        syncer = EventSyncer(
            provider='opta',
            config={'competition_id': '8', 'season_id': '2023'}
        )

        # Sync events for a specific match
        result = await syncer.sync(match_id='g2187923')
        print(f"Synced {result.entities_created} events")
    """

    def __init__(
        self,
        provider: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize event syncer

        Args:
            provider: Provider name ('opta', 'statsbomb', etc.)
            config: Provider configuration
        """
        repository = EventRepository()
        merger = EventMerger()

        # Note: No resolver for events (too many to fuzzy match)
        super().__init__(
            provider=provider,
            repository=repository,
            resolver=None,
            merger=merger,
            config=config
        )

    def get_entity_type(self) -> str:
        return "event"

    async def fetch_entities(self, **kwargs) -> List[ScoutProEvent]:
        """
        Fetch events from provider

        Args:
            **kwargs: Provider-specific parameters
                - match_id: Match ID (required)

        Returns:
            List of ScoutProEvent instances

        Example:
            # Fetch all events for a match
            events = await syncer.fetch_entities(match_id='g2187923')
        """
        # Get connector and mapper
        connector = self.factory.get_connector(self.provider, self.config)
        mapper = self.factory.get_mapper(self.provider)

        # Fetch from provider
        match_id = kwargs.get('match_id')

        if not match_id:
            raise ValueError("match_id is required for event sync")

        raw_events = await connector.fetch_match_events(match_id)

        # Map to canonical format
        events = mapper.map_events(raw_events)

        # Set match_id for all events
        for event in events:
            if event:
                # Generate canonical match ID
                event.match_id = self.generate_canonical_match_id(match_id)

        # Filter out None events (unmapped)
        events = [e for e in events if e is not None]

        return events

    def generate_canonical_match_id(self, provider_match_id: str) -> str:
        """
        Generate canonical match ID from provider-specific ID

        This should match the ID used in MatchRepository.

        Args:
            provider_match_id: Provider-specific match ID

        Returns:
            Canonical match ID

        Example:
            canonical_id = self.generate_canonical_match_id('g2187923')
            → 'match_opta_g2187923' or existing canonical ID
        """
        # Try to find existing canonical match
        from shared.repositories import MatchRepository
        match_repo = MatchRepository()

        existing_match = match_repo.find_by_provider_id(self.provider, provider_match_id)

        if existing_match:
            return existing_match.id

        # Generate new canonical ID
        return f"match_{self.provider}_{provider_match_id}"

    async def store_entities(self, entities: List[ScoutProEvent]) -> int:
        """
        Store events in repository (optimized for bulk)

        Args:
            entities: List of events to store

        Returns:
            Number of events stored

        Example:
            count = await self.store_entities(enriched_events)
        """
        if not entities:
            return 0

        try:
            # Group events by match
            events_by_match: Dict[str, List[ScoutProEvent]] = {}

            for event in entities:
                match_id = event.match_id
                if match_id not in events_by_match:
                    events_by_match[match_id] = []
                events_by_match[match_id].append(event)

            # Bulk insert per match
            total_stored = 0

            for match_id, match_events in events_by_match.items():
                # Delete existing events for this match/provider to avoid duplicates
                # (This is a replace strategy - could be configurable)
                existing_events = self.repository.find_by_match(match_id)
                provider_events = [e for e in existing_events if e.provider == self.provider]

                if provider_events:
                    print(f"[{self.provider}] Deleting {len(provider_events)} existing events for match {match_id}")
                    self.repository.delete_many({
                        'match_id': match_id,
                        'provider': self.provider
                    })

                # Bulk create new events
                count = self.repository.bulk_upsert(match_events)
                total_stored += count

            return total_stored

        except Exception as e:
            error_msg = f"Error storing events: {str(e)}"
            self.stats['errors'].append(error_msg)
            print(f"[{self.provider}] {error_msg}")
            return 0

    async def resolve_and_merge(self, entities: List[ScoutProEvent]) -> List[Optional[ScoutProEvent]]:
        """
        Events are not resolved individually (too many).
        Instead, we replace all events for the match.

        If merging with another provider is needed, use EventMerger.merge_event_lists()
        in a separate workflow.

        Args:
            entities: List of events from provider

        Returns:
            Same list of entities (no resolution)
        """
        # For events, we don't do individual resolution
        # Just return the entities as-is
        return entities
