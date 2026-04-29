"""
Match Syncer

Synchronizes match data from providers to canonical repository.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from shared.domain.models import ScoutProMatch
from shared.repositories import MatchRepository
from shared.resolution import MatchResolver
from shared.merger import MatchMerger
from sync.base_syncer import BaseSyncer


class MatchSyncer(BaseSyncer[ScoutProMatch]):
    """
    Synchronizes match data

    Usage:
        syncer = MatchSyncer(
            provider='opta',
            config={'competition_id': '8', 'season_id': '2023'}
        )

        result = await syncer.sync()
        print(f"Synced {result.entities_created} matches")
    """

    def __init__(
        self,
        provider: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize match syncer

        Args:
            provider: Provider name ('opta', 'statsbomb', etc.)
            config: Provider configuration
        """
        repository = MatchRepository()
        resolver = MatchResolver()
        merger = MatchMerger()

        super().__init__(
            provider=provider,
            repository=repository,
            resolver=resolver,
            merger=merger,
            config=config
        )

    def get_entity_type(self) -> str:
        return "match"

    async def fetch_entities(self, **kwargs) -> List[ScoutProMatch]:
        """
        Fetch matches from provider

        Args:
            **kwargs: Provider-specific parameters
                - competition_id: Competition ID
                - season_id: Season ID
                - date_from: Start date (optional)
                - date_to: End date (optional)

        Returns:
            List of ScoutProMatch instances

        Example:
            # Fetch all matches in competition/season
            matches = await syncer.fetch_entities(
                competition_id='8',
                season_id='2023'
            )

            # Fetch matches in date range
            matches = await syncer.fetch_entities(
                competition_id='8',
                season_id='2023',
                date_from='2023-10-01',
                date_to='2023-10-31'
            )
        """
        # Get connector and mapper
        connector = self.factory.get_connector(self.provider, self.config)
        mapper = self.factory.get_mapper(self.provider)

        # Fetch from provider
        competition_id = kwargs.get('competition_id')
        season_id = kwargs.get('season_id')
        date_from = kwargs.get('date_from')
        date_to = kwargs.get('date_to')

        raw_matches = await connector.fetch_matches(
            competition_id=competition_id,
            season_id=season_id,
            date_from=date_from,
            date_to=date_to
        )

        # Map to canonical format
        matches = []
        for raw_match in raw_matches:
            try:
                match = mapper.map_match(raw_match)
                matches.append(match)
            except Exception as e:
                error_msg = f"Error mapping match: {str(e)}"
                self.stats['errors'].append(error_msg)
                print(f"[{self.provider}] {error_msg}")

        return matches
