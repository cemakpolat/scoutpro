"""
Team Syncer

Synchronizes team data from providers to canonical repository.
"""

from typing import List, Optional, Dict, Any

from shared.domain.models import ScoutProTeam
from shared.repositories import TeamRepository
from shared.resolution import TeamResolver
from shared.merger import TeamMerger
from sync.base_syncer import BaseSyncer


class TeamSyncer(BaseSyncer[ScoutProTeam]):
    """
    Synchronizes team data

    Usage:
        syncer = TeamSyncer(
            provider='opta',
            config={'competition_id': '8'}
        )

        result = await syncer.sync()
        print(f"Synced {result.entities_created} teams")
    """

    def __init__(
        self,
        provider: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize team syncer

        Args:
            provider: Provider name ('opta', 'statsbomb', etc.)
            config: Provider configuration
        """
        repository = TeamRepository()
        resolver = TeamResolver()
        merger = TeamMerger()

        super().__init__(
            provider=provider,
            repository=repository,
            resolver=resolver,
            merger=merger,
            config=config
        )

    def get_entity_type(self) -> str:
        return "team"

    async def fetch_entities(self, **kwargs) -> List[ScoutProTeam]:
        """
        Fetch teams from provider

        Args:
            **kwargs: Provider-specific parameters
                - competition_id: Competition ID (optional)

        Returns:
            List of ScoutProTeam instances

        Example:
            # Fetch all teams in competition
            teams = await syncer.fetch_entities(competition_id='8')
        """
        # Get connector and mapper
        connector = self.factory.get_connector(self.provider, self.config)
        mapper = self.factory.get_mapper(self.provider)

        # Fetch from provider
        competition_id = kwargs.get('competition_id')

        raw_teams = await connector.fetch_teams(competition_id=competition_id)

        # Map to canonical format
        teams = []
        for raw_team in raw_teams:
            try:
                team = mapper.map_team(raw_team)
                teams.append(team)
            except Exception as e:
                error_msg = f"Error mapping team: {str(e)}"
                self.stats['errors'].append(error_msg)
                print(f"[{self.provider}] {error_msg}")

        return teams
