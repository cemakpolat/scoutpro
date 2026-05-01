"""
Base Connector Interface

Abstract base class for all provider connectors.
Connectors handle fetching data from external sources (APIs, databases, files).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseConnector(ABC):
    """
    Abstract connector interface all providers must implement

    This interface defines how to fetch raw data from provider sources.
    Connectors are responsible for:
    - API authentication
    - HTTP requests
    - Database queries
    - File reading
    - Error handling and retries
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the connector

        Args:
            config: Configuration dictionary (API keys, URLs, etc.)
        """
        self.config = config or {}
        self.provider_name = self.get_provider_name()

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name (e.g., 'opta', 'statsbomb', 'wyscout')

        Returns:
            Provider identifier string
        """
        pass

    # ========================================
    # MATCH DATA
    # ========================================

    @abstractmethod
    async def fetch_match(self, match_id: str) -> Dict[str, Any]:
        """
        Fetch match data by ID

        Args:
            match_id: Provider's match ID

        Returns:
            Raw match data dictionary

        Raises:
            ConnectionError: If unable to connect to provider
            ValueError: If match_id is invalid
        """
        pass

    @abstractmethod
    async def fetch_matches(
        self,
        competition_id: Optional[str] = None,
        season_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple matches with filters

        Args:
            competition_id: Filter by competition
            season_id: Filter by season
            date_from: Filter by start date (YYYY-MM-DD)
            date_to: Filter by end date (YYYY-MM-DD)

        Returns:
            List of raw match data dictionaries
        """
        pass

    # ========================================
    # EVENT DATA
    # ========================================

    @abstractmethod
    async def fetch_match_events(self, match_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all events for a match

        Args:
            match_id: Provider's match ID

        Returns:
            List of raw event data dictionaries

        Example:
            Opta: Returns F24 feed events
            StatsBomb: Returns events from JSON file/API
        """
        pass

    # ========================================
    # PLAYER DATA
    # ========================================

    @abstractmethod
    async def fetch_player(self, player_id: str) -> Dict[str, Any]:
        """
        Fetch player data by ID

        Args:
            player_id: Provider's player ID

        Returns:
            Raw player data dictionary
        """
        pass

    async def fetch_players(
        self,
        team_id: Optional[str] = None,
        competition_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple players

        Args:
            team_id: Filter by team
            competition_id: Filter by competition

        Returns:
            List of raw player data dictionaries

        Note:
            This is optional - not all providers may support it efficiently
        """
        raise NotImplementedError(
            f"{self.provider_name} connector does not support batch player fetching"
        )

    # ========================================
    # TEAM DATA
    # ========================================

    @abstractmethod
    async def fetch_team(self, team_id: str) -> Dict[str, Any]:
        """
        Fetch team data by ID

        Args:
            team_id: Provider's team ID

        Returns:
            Raw team data dictionary
        """
        pass

    async def fetch_teams(
        self,
        competition_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple teams

        Args:
            competition_id: Filter by competition

        Returns:
            List of raw team data dictionaries
        """
        raise NotImplementedError(
            f"{self.provider_name} connector does not support batch team fetching"
        )

    # ========================================
    # LINEUP DATA
    # ========================================

    async def fetch_match_lineups(self, match_id: str) -> Dict[str, Any]:
        """
        Fetch lineups for a match

        Args:
            match_id: Provider's match ID

        Returns:
            Raw lineup data dictionary

        Note:
            Optional - not all providers may have separate lineup endpoints
        """
        raise NotImplementedError(
            f"{self.provider_name} connector does not support lineup fetching"
        )

    # ========================================
    # HEALTH CHECK
    # ========================================

    async def health_check(self) -> bool:
        """
        Check if provider connection is healthy

        Returns:
            True if connection is working, False otherwise

        Example:
            For API: Try a simple GET request
            For database: Try a simple query
            For files: Check if directory exists
        """
        try:
            # Default implementation - override if needed
            return True
        except Exception:
            return False

    # ========================================
    # HELPER METHODS
    # ========================================

    def get_available_fields(self) -> List[str]:
        """
        Get list of fields this provider can supply

        Returns:
            List of field names

        Example:
            ['match_id', 'events', 'lineups', 'xG', 'freeze_frames']
        """
        return []

    def supports_live_data(self) -> bool:
        """
        Check if provider supports live/real-time data

        Returns:
            True if provider can stream live data
        """
        return False
