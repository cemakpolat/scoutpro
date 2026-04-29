"""
Player Syncer

Synchronizes player data from providers to canonical repository.
"""

from typing import List, Optional, Dict, Any

from shared.domain.models import ScoutProPlayer
from shared.repositories import PlayerRepository
from shared.resolution import PlayerResolver
from shared.merger import PlayerMerger
from sync.base_syncer import BaseSyncer


class PlayerSyncer(BaseSyncer[ScoutProPlayer]):
    """
    Synchronizes player data

    Usage:
        syncer = PlayerSyncer(
            provider='opta',
            config={'competition_id': '8', 'season_id': '2023'}
        )

        result = await syncer.sync()
        print(f"Synced {result.entities_created} players")
    """

    def __init__(
        self,
        provider: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize player syncer

        Args:
            provider: Provider name ('opta', 'statsbomb', etc.)
            config: Provider configuration
        """
        repository = PlayerRepository()
        resolver = PlayerResolver()
        merger = PlayerMerger()

        super().__init__(
            provider=provider,
            repository=repository,
            resolver=resolver,
            merger=merger,
            config=config
        )

    def get_entity_type(self) -> str:
        return "player"

    async def fetch_entities(self, **kwargs) -> List[ScoutProPlayer]:
        """
        Fetch players from provider

        Args:
            **kwargs: Provider-specific parameters
                - team_id: Team ID (optional)
                - competition_id: Competition ID (optional)

        Returns:
            List of ScoutProPlayer instances

        Example:
            # Fetch all players in competition
            players = await syncer.fetch_entities(competition_id='8')

            # Fetch players for specific team
            players = await syncer.fetch_entities(team_id='t14')
        """
        # Get connector and mapper
        connector = self.factory.get_connector(self.provider, self.config)
        mapper = self.factory.get_mapper(self.provider)

        # Fetch from provider
        team_id = kwargs.get('team_id')
        competition_id = kwargs.get('competition_id')

        raw_players = await connector.fetch_players(
            team_id=team_id,
            competition_id=competition_id
        )

        # Map to canonical format
        players = []
        for raw_player in raw_players:
            try:
                player = mapper.map_player(raw_player)
                players.append(player)
            except Exception as e:
                error_msg = f"Error mapping player: {str(e)}"
                self.stats['errors'].append(error_msg)
                print(f"[{self.provider}] {error_msg}")

        return players
