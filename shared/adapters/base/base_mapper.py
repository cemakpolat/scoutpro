"""
Base Mapper Interface

Abstract base class for all provider mappers.
Mappers transform provider-specific data into ScoutPro canonical format.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from shared.domain.models import ScoutProEvent, ScoutProMatch, ScoutProPlayer, ScoutProTeam, EventQuality


class BaseMapper(ABC):
    """
    Abstract mapper interface all providers must implement

    This interface defines the contract for transforming provider-specific
    data into ScoutPro canonical format.

    Each provider (Opta, StatsBomb, Wyscout, etc.) implements this interface
    to provide a consistent way of accessing their data.
    """

    def __init__(self):
        """Initialize the mapper"""
        self.provider_name = self.get_provider_name()

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name (e.g., 'opta', 'statsbomb', 'wyscout')

        Returns:
            Provider identifier string
        """
        pass

    @abstractmethod
    def get_data_quality(self) -> EventQuality:
        """
        Get the typical data quality level this provider offers

        Returns:
            EventQuality enum value indicating data richness

        Example:
            EventQuality.COMPREHENSIVE for Opta F24 (very detailed)
            EventQuality.DETAILED for StatsBomb (good detail)
            EventQuality.BASIC for basic providers
        """
        pass

    # ========================================
    # PLAYER MAPPING
    # ========================================

    @abstractmethod
    def map_player(self, raw_data: Dict[str, Any]) -> ScoutProPlayer:
        """
        Convert provider player data → ScoutProPlayer

        Args:
            raw_data: Provider-specific player data dictionary

        Returns:
            ScoutProPlayer instance

        Example:
            Opta format:
            {
                "playerId": "p12345",
                "firstName": "Mohamed",
                "lastName": "Salah",
                "birthDate": "1992-06-15",
                ...
            }

            StatsBomb format:
            {
                "player_id": 3318,
                "player_name": "Mohamed Salah",
                ...
            }
        """
        pass

    def map_players(self, raw_data_list: List[Dict[str, Any]]) -> List[ScoutProPlayer]:
        """
        Convert multiple players (convenience method)

        Args:
            raw_data_list: List of provider-specific player data

        Returns:
            List of ScoutProPlayer instances
        """
        return [self.map_player(data) for data in raw_data_list]

    # ========================================
    # TEAM MAPPING
    # ========================================

    @abstractmethod
    def map_team(self, raw_data: Dict[str, Any]) -> ScoutProTeam:
        """
        Convert provider team data → ScoutProTeam

        Args:
            raw_data: Provider-specific team data dictionary

        Returns:
            ScoutProTeam instance
        """
        pass

    def map_teams(self, raw_data_list: List[Dict[str, Any]]) -> List[ScoutProTeam]:
        """
        Convert multiple teams (convenience method)

        Args:
            raw_data_list: List of provider-specific team data

        Returns:
            List of ScoutProTeam instances
        """
        return [self.map_team(data) for data in raw_data_list]

    # ========================================
    # MATCH MAPPING
    # ========================================

    @abstractmethod
    def map_match(self, raw_data: Dict[str, Any]) -> ScoutProMatch:
        """
        Convert provider match data → ScoutProMatch

        Args:
            raw_data: Provider-specific match data dictionary

        Returns:
            ScoutProMatch instance
        """
        pass

    def map_matches(self, raw_data_list: List[Dict[str, Any]]) -> List[ScoutProMatch]:
        """
        Convert multiple matches (convenience method)

        Args:
            raw_data_list: List of provider-specific match data

        Returns:
            List of ScoutProMatch instances
        """
        return [self.map_match(data) for data in raw_data_list]

    # ========================================
    # EVENT MAPPING
    # ========================================

    @abstractmethod
    def map_event(self, raw_data: Dict[str, Any]) -> Optional[ScoutProEvent]:
        """
        Convert provider event data → ScoutProEvent

        Args:
            raw_data: Provider-specific event data dictionary

        Returns:
            ScoutProEvent instance, or None if event type is unmapped

        Example:
            Opta F24 event:
            {
                "id": "evt123",
                "type_id": 1,  # Pass
                "outcome": 1,  # Successful
                "x": 65.2,
                "y": 48.7,
                "qualifiers": [...]
            }

            StatsBomb event:
            {
                "id": "sb789",
                "type": {"id": 30, "name": "Pass"},
                "location": [65.2, 48.7],
                "pass": {...}
            }
        """
        pass

    @abstractmethod
    def map_events(self, raw_data_list: List[Dict[str, Any]]) -> List[ScoutProEvent]:
        """
        Convert multiple events

        Args:
            raw_data_list: List of provider-specific event data

        Returns:
            List of ScoutProEvent instances (filters out unmapped events)
        """
        pass

    # ========================================
    # HELPER METHODS (optional to override)
    # ========================================

    def normalize_coordinates(
        self,
        x: float,
        y: float,
        provider_pitch_length: float = 100,
        provider_pitch_width: float = 100
    ) -> tuple:
        """
        Normalize coordinates to ScoutPro standard (0-100 scale)

        Different providers use different coordinate systems:
        - Opta: 0-100 (both X and Y)
        - StatsBomb: 0-120 (X) by 0-80 (Y)
        - Wyscout: 0-100 (both X and Y)

        Args:
            x: X coordinate in provider's system
            y: Y coordinate in provider's system
            provider_pitch_length: Provider's pitch length scale
            provider_pitch_width: Provider's pitch width scale

        Returns:
            Tuple of (normalized_x, normalized_y) in 0-100 scale
        """
        normalized_x = (x / provider_pitch_length) * 100.0
        normalized_y = (y / provider_pitch_width) * 100.0
        return (normalized_x, normalized_y)

    def standardize_position(self, provider_position: str) -> str:
        """
        Standardize position to ScoutPro format: GK, DF, MF, FW

        Args:
            provider_position: Provider's position string

        Returns:
            Standardized position string
        """
        position_map = {
            # Common variations
            'goalkeeper': 'GK',
            'defender': 'DF',
            'midfielder': 'MF',
            'forward': 'FW',
            'attacker': 'FW',
            # Opta specific
            'Goalkeeper': 'GK',
            'Defender': 'DF',
            'Midfielder': 'MF',
            'Forward': 'FW',
            # StatsBomb specific
            'Left Back': 'DF',
            'Right Back': 'DF',
            'Center Back': 'DF',
            'Left Wing Back': 'DF',
            'Right Wing Back': 'DF',
            'Defensive Midfield': 'MF',
            'Central Midfield': 'MF',
            'Left Midfield': 'MF',
            'Right Midfield': 'MF',
            'Left Wing': 'FW',
            'Right Wing': 'FW',
            'Center Forward': 'FW',
            'Secondary Striker': 'FW',
        }

        return position_map.get(provider_position, 'MF')  # Default to MF

    def generate_scoutpro_id(self, entity_type: str, external_id: str) -> str:
        """
        Generate ScoutPro canonical ID

        Args:
            entity_type: 'player', 'team', 'match', 'event'
            external_id: Provider's ID

        Returns:
            ScoutPro canonical ID

        Example:
            generate_scoutpro_id('player', 'p12345') → 'scoutpro_player_opta_p12345'
            generate_scoutpro_id('event', 'evt123') → 'scoutpro_event_opta_evt123'
        """
        return f"scoutpro_{entity_type}_{self.provider_name}_{external_id}"
