"""
Opta Connector

Wraps existing Opta connector/parser logic from services/shared/connectors/
Provides async interface for fetching Opta data.
"""

from typing import Dict, Any, List, Optional
import sys
import os

# Add path to existing Opta code
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..', 'services'))

from shared.adapters.base import BaseConnector


class OptaConnector(BaseConnector):
    """
    Connects to Opta data sources

    This connector wraps the existing Opta connector/parser logic
    and provides an async interface compatible with the adapter pattern.

    The existing code is in:
    - services/shared/connectors/connector.py (Connector class)
    - services/shared/parsers/parser.py (Parser functions)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Opta connector

        Args:
            config: Configuration dict with:
                - db_name: MongoDB database name
                - db_host: MongoDB host
                - db_port: MongoDB port
                - online: Whether to fetch from Opta API (True) or local files (False)
        """
        super().__init__(config)

        self.db_name = config.get('db_name', 'statsfabrik') if config else 'statsfabrik'
        self.db_host = config.get('db_host', 'localhost') if config else 'localhost'
        self.db_port = config.get('db_port', 27017) if config else 27017
        self.online = config.get('online', False) if config else False

        # Lazy import to avoid circular dependencies
        self._connector = None
        self._parser = None

    def get_provider_name(self) -> str:
        return "opta"

    def _get_connector(self):
        """Lazy load the existing Connector class"""
        if self._connector is None:
            try:
                from src.connectors.connector import Connector
                self._connector = Connector(
                    name=self.db_name,
                    host=self.db_host,
                    port=self.db_port
                )
                self._connector.connect().setOnline(self.online)
            except ImportError:
                # Fallback if import path is different
                try:
                    from shared.connectors.connector import Connector
                    self._connector = Connector(
                        name=self.db_name,
                        host=self.db_host,
                        port=self.db_port
                    )
                    self._connector.connect().setOnline(self.online)
                except ImportError:
                    raise ImportError(
                        "Could not import existing Opta Connector. "
                        "Check that services/shared/connectors/connector.py exists"
                    )
        return self._connector

    # ========================================
    # MATCH DATA
    # ========================================

    async def fetch_match(self, match_id: str) -> Dict[str, Any]:
        """
        Fetch match data (F9 feed)

        Args:
            match_id: Opta match ID (game_id)

        Returns:
            Raw F9 match data

        Note:
            This requires competition_id and season_id to be set in config
        """
        competition_id = self.config.get('competition_id')
        season_id = self.config.get('season_id')

        if not competition_id or not season_id:
            raise ValueError("competition_id and season_id must be provided in config")

        connector = self._get_connector()
        feed_data = connector.getFeed('feed9', competition_id, season_id, match_id)

        return feed_data

    async def fetch_matches(
        self,
        competition_id: Optional[str] = None,
        season_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple matches (F1 feed)

        Args:
            competition_id: Competition ID
            season_id: Season ID
            date_from: Not used for Opta F1
            date_to: Not used for Opta F1

        Returns:
            List of raw match data from F1 feed
        """
        if not competition_id or not season_id:
            competition_id = self.config.get('competition_id')
            season_id = self.config.get('season_id')

        if not competition_id or not season_id:
            raise ValueError("competition_id and season_id must be provided")

        connector = self._get_connector()
        feed_data = connector.getFeed('feed1', competition_id, season_id)

        # F1 feed contains multiple matches
        # Extract MatchData array from feed
        if feed_data and 'matchData' in feed_data:
            return feed_data['matchData']

        return []

    # ========================================
    # EVENT DATA
    # ========================================

    async def fetch_match_events(self, match_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all events for a match (F24 feed)

        Args:
            match_id: Opta match ID (game_id)

        Returns:
            List of raw F24 event data
        """
        competition_id = self.config.get('competition_id')
        season_id = self.config.get('season_id')

        if not competition_id or not season_id:
            raise ValueError("competition_id and season_id must be provided in config")

        connector = self._get_connector()
        feed_data = connector.getFeed('feed24', competition_id, season_id, match_id)

        # F24 feed structure: feed → game → events
        # The existing parser returns a Feed24 object with game.Event
        if feed_data and hasattr(feed_data, 'game'):
            game = feed_data.game
            if hasattr(game, 'Event'):
                return game.Event

        # If raw dict structure
        if isinstance(feed_data, dict):
            game_data = feed_data.get('game', {})
            if 'Event' in game_data:
                return game_data['Event']

        return []

    # ========================================
    # PLAYER DATA
    # ========================================

    async def fetch_player(self, player_id: str) -> Dict[str, Any]:
        """
        Fetch player data

        Note: Opta doesn't have a dedicated player endpoint.
        Players are fetched as part of F40 (squad list) or F9 (lineups).
        This is a placeholder.
        """
        raise NotImplementedError(
            "Opta doesn't have a dedicated player endpoint. "
            "Use fetch_team() to get squad list (F40) or "
            "fetch_match_lineups() to get match lineups (F9)"
        )

    async def fetch_players(
        self,
        team_id: Optional[str] = None,
        competition_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch players for a team (from F40 squad list)

        Args:
            team_id: Opta team ID
            competition_id: Competition ID

        Returns:
            List of player data from F40 feed
        """
        if not competition_id:
            competition_id = self.config.get('competition_id')
        season_id = self.config.get('season_id')

        if not competition_id or not season_id:
            raise ValueError("competition_id and season_id must be provided")

        connector = self._get_connector()
        feed_data = connector.getFeed('feed40', competition_id, season_id)

        # F40 contains team squads
        # Extract players for specified team if team_id provided
        players = []

        if feed_data and hasattr(feed_data, 'teams'):
            for team in feed_data.teams:
                if team_id and hasattr(team, 'uID') and team.uID != team_id:
                    continue

                if hasattr(team, 'Player'):
                    if isinstance(team.Player, list):
                        players.extend(team.Player)
                    else:
                        players.append(team.Player)

        return players

    # ========================================
    # TEAM DATA
    # ========================================

    async def fetch_team(self, team_id: str) -> Dict[str, Any]:
        """
        Fetch team data

        Teams are part of F40 (squad list) or F1/F9 feeds.
        """
        # Fetch from F40 which has full team data
        competition_id = self.config.get('competition_id')
        season_id = self.config.get('season_id')

        if not competition_id or not season_id:
            raise ValueError("competition_id and season_id must be provided")

        connector = self._get_connector()
        feed_data = connector.getFeed('feed40', competition_id, season_id)

        if feed_data and hasattr(feed_data, 'teams'):
            for team in feed_data.teams:
                if hasattr(team, 'uID') and team.uID == team_id:
                    return team.__dict__  # Convert to dict

        return {}

    async def fetch_teams(
        self,
        competition_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all teams in a competition (F40 feed)

        Args:
            competition_id: Competition ID

        Returns:
            List of team data from F40
        """
        if not competition_id:
            competition_id = self.config.get('competition_id')
        season_id = self.config.get('season_id')

        if not competition_id or not season_id:
            raise ValueError("competition_id and season_id must be provided")

        connector = self._get_connector()
        feed_data = connector.getFeed('feed40', competition_id, season_id)

        if feed_data and hasattr(feed_data, 'teams'):
            return [team.__dict__ for team in feed_data.teams]

        return []

    # ========================================
    # LINEUP DATA
    # ========================================

    async def fetch_match_lineups(self, match_id: str) -> Dict[str, Any]:
        """
        Fetch lineups for a match (from F9 feed)

        Args:
            match_id: Opta match ID

        Returns:
            Dict with home and away lineups
        """
        match_data = await self.fetch_match(match_id)

        lineups = {
            'home': [],
            'away': []
        }

        # Extract lineups from F9 match data
        # This depends on the structure of the Feed9 object
        # Placeholder implementation
        if match_data and 'TeamData' in match_data:
            for team_data in match_data['TeamData']:
                if 'Side' in team_data.get('@attributes', {}):
                    side = team_data['@attributes']['Side'].lower()
                    if 'PlayerLineUp' in team_data:
                        lineup = team_data['PlayerLineUp']
                        if side in lineups:
                            lineups[side] = lineup

        return lineups

    # ========================================
    # HEALTH CHECK
    # ========================================

    async def health_check(self) -> bool:
        """Check if Opta connection is healthy"""
        try:
            connector = self._get_connector()
            # Try to fetch a small feed to test connection
            return True
        except Exception as e:
            print(f"Opta health check failed: {e}")
            return False

    def get_available_fields(self) -> List[str]:
        """Get list of fields Opta can supply"""
        return [
            'match_id',
            'events',  # F24
            'lineups',  # F9
            'squads',  # F40
            'match_stats',  # F9
            'event_qualifiers',  # F24 (200+ qualifiers)
        ]

    def supports_live_data(self) -> bool:
        """Opta supports live data"""
        return True
