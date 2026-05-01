"""
Base Parser Interface

Abstract base class for all provider parsers.
Parsers transform raw data formats (XML, JSON, etc.) into structured dictionaries.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseParser(ABC):
    """
    Abstract parser interface all providers must implement

    This interface defines how to parse provider-specific data formats.
    Parsers are responsible for:
    - XML parsing (Opta F24, F7, F9, etc.)
    - JSON parsing (StatsBomb, Wyscout, etc.)
    - Data validation
    - Error handling
    """

    def __init__(self):
        """Initialize the parser"""
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
    # MATCH DATA PARSING
    # ========================================

    @abstractmethod
    def parse_match(self, raw_data: str) -> Dict[str, Any]:
        """
        Parse match data from raw format

        Args:
            raw_data: Raw data string (XML, JSON, etc.)

        Returns:
            Parsed match data as dictionary

        Raises:
            ValueError: If data format is invalid
            ParseError: If parsing fails

        Example:
            Opta: Parse F9 XML feed
            StatsBomb: Parse match JSON
        """
        pass

    def parse_matches(self, raw_data: str) -> List[Dict[str, Any]]:
        """
        Parse multiple matches from raw format

        Args:
            raw_data: Raw data string containing multiple matches

        Returns:
            List of parsed match dictionaries

        Note:
            Default implementation parses as single match.
            Override if provider supports batch format.
        """
        return [self.parse_match(raw_data)]

    # ========================================
    # EVENT DATA PARSING
    # ========================================

    @abstractmethod
    def parse_events(self, raw_data: str) -> List[Dict[str, Any]]:
        """
        Parse event data from raw format

        Args:
            raw_data: Raw data string (XML, JSON, etc.)

        Returns:
            List of parsed event dictionaries

        Example:
            Opta: Parse F24 XML feed (contains all events for a match)
            StatsBomb: Parse events JSON array
        """
        pass

    def parse_event(self, raw_data: str) -> Dict[str, Any]:
        """
        Parse single event from raw format

        Args:
            raw_data: Raw data string for single event

        Returns:
            Parsed event dictionary

        Note:
            Default implementation parses as event list and returns first.
            Override if provider has single-event format.
        """
        events = self.parse_events(raw_data)
        return events[0] if events else {}

    # ========================================
    # PLAYER DATA PARSING
    # ========================================

    def parse_player(self, raw_data: str) -> Dict[str, Any]:
        """
        Parse player data from raw format

        Args:
            raw_data: Raw data string

        Returns:
            Parsed player data dictionary

        Note:
            Optional - not all providers need separate player parsing
        """
        raise NotImplementedError(
            f"{self.provider_name} parser does not support player parsing"
        )

    def parse_players(self, raw_data: str) -> List[Dict[str, Any]]:
        """
        Parse multiple players from raw format

        Args:
            raw_data: Raw data string containing multiple players

        Returns:
            List of parsed player dictionaries
        """
        raise NotImplementedError(
            f"{self.provider_name} parser does not support player list parsing"
        )

    # ========================================
    # TEAM DATA PARSING
    # ========================================

    def parse_team(self, raw_data: str) -> Dict[str, Any]:
        """
        Parse team data from raw format

        Args:
            raw_data: Raw data string

        Returns:
            Parsed team data dictionary
        """
        raise NotImplementedError(
            f"{self.provider_name} parser does not support team parsing"
        )

    def parse_teams(self, raw_data: str) -> List[Dict[str, Any]]:
        """
        Parse multiple teams from raw format

        Args:
            raw_data: Raw data string containing multiple teams

        Returns:
            List of parsed team dictionaries
        """
        raise NotImplementedError(
            f"{self.provider_name} parser does not support team list parsing"
        )

    # ========================================
    # LINEUP DATA PARSING
    # ========================================

    def parse_lineups(self, raw_data: str) -> Dict[str, Any]:
        """
        Parse lineup data from raw format

        Args:
            raw_data: Raw data string

        Returns:
            Parsed lineup data dictionary
            Format: {
                "home": [{"player_id": "...", "position": "..."}, ...],
                "away": [...]
            }
        """
        raise NotImplementedError(
            f"{self.provider_name} parser does not support lineup parsing"
        )

    # ========================================
    # VALIDATION
    # ========================================

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate parsed data structure

        Args:
            data: Parsed data dictionary

        Returns:
            True if data is valid, False otherwise

        Note:
            Default implementation does basic checks.
            Override for provider-specific validation.
        """
        # Basic validation - check if dict is not empty
        return isinstance(data, dict) and len(data) > 0

    # ========================================
    # ERROR HANDLING
    # ========================================

    def handle_parse_error(self, error: Exception, raw_data: str) -> None:
        """
        Handle parsing errors

        Args:
            error: The exception that occurred
            raw_data: The raw data that failed to parse

        Raises:
            Re-raises the error after logging
        """
        # Default implementation - just re-raise
        # Override to add custom logging/error handling
        raise error
