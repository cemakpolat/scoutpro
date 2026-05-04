"""
Canonical Team Model

ScoutProTeam represents a football team in provider-agnostic format.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class ScoutProTeam:
    """
    Canonical team model - provider-agnostic

    Represents a football team with data potentially merged from multiple providers.
    """

    # ====== IDENTITY ======
    id: int                           # ScoutPro canonical numeric ID
    external_id: str                  # Primary provider's ID
    provider: str                     # Primary data source ('opta', 'statsbomb', etc.)

    # ====== BASIC INFO ======
    name: str                         # Official team name
    short_name: Optional[str] = None  # Abbreviated name
    common_name: Optional[str] = None # Commonly used name
    abbreviation: Optional[str] = None # 3-letter code (e.g., "LIV", "MCI")

    # ====== LOCATION ======
    city: Optional[str] = None
    country: str = ""
    stadium: Optional[str] = None
    stadium_capacity: Optional[int] = None

    # ====== CLUB INFO ======
    founded: Optional[int] = None     # Year founded
    colors: List[str] = field(default_factory=list)  # Team colors
    badge_url: Optional[str] = None   # URL to team badge/logo

    # ====== CURRENT STATUS ======
    current_competition_ids: List[int] = field(default_factory=list)  # Competitions they're in
    current_league: Optional[str] = None
    manager: Optional[str] = None     # Current manager/coach

    # ====== PROVIDER MAPPINGS ======
    provider_ids: Dict[str, str] = field(default_factory=dict)
    # Example: {"opta": "t14", "statsbomb": "sb18", "wyscout": None}

    # ====== PROVIDER-SPECIFIC DATA ======
    provider_data: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "opta": {
    #     "source": "opta",
    #     "last_updated": "2025-10-28T10:00:00Z",
    #     "data": {full Opta team object}
    #   },
    #   "statsbomb": {
    #     "source": "statsbomb",
    #     "last_updated": "2025-10-28T09:30:00Z",
    #     "data": {full StatsBomb team object}
    #   }
    # }

    # ====== DATA QUALITY METADATA ======
    data_quality: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "completeness_score": 0.92,
    #   "confidence_score": 0.99,
    #   "data_sources": ["opta", "statsbomb"],
    #   "missing_fields": ["stadium_capacity"],
    #   "conflicting_fields": []
    # }

    # ====== SCOUTPRO METADATA ======
    scoutpro_metadata: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "internal_rating": 88,
    #   "notes": "Strong defensive record",
    #   "tags": ["top_tier", "defensive"]
    # }

    # ====== CONFLICT TRACKING ======
    conflicts: Optional[list] = None

    # ====== MERGE METADATA ======
    merge_info: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "merged_from": ["opta", "statsbomb"],
    #   "last_merge": "2025-10-28T10:00:00Z",
    #   "merge_strategy_version": "v1.2"
    # }

    # ====== TIMESTAMPS ======
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def get_display_name(self) -> str:
        """Get best display name"""
        return self.short_name or self.common_name or self.name

    @property
    def code(self) -> Optional[str]:
        """Backward-compatible alias for legacy code paths."""
        return self.abbreviation

    @code.setter
    def code(self, value: Optional[str]) -> None:
        self.abbreviation = value

    @property
    def league(self) -> Optional[str]:
        """Backward-compatible alias for legacy code paths."""
        return self.current_league

    @league.setter
    def league(self, value: Optional[str]) -> None:
        self.current_league = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            "scoutpro_id": self.id,
            "external_id": self.external_id,
            "provider": self.provider,
            "name": self.name,
            "short_name": self.short_name,
            "common_name": self.common_name,
            "abbreviation": self.abbreviation,
            "city": self.city,
            "country": self.country,
            "stadium": self.stadium,
            "stadium_capacity": self.stadium_capacity,
            "founded": self.founded,
            "colors": self.colors,
            "badge_url": self.badge_url,
            "current_competition_ids": self.current_competition_ids,
            "current_league": self.current_league,
            "manager": self.manager,
            "provider_ids": self.provider_ids,
            "provider_data": self.provider_data,
            "data_quality": self.data_quality,
            "scoutpro_metadata": self.scoutpro_metadata,
            "conflicts": self.conflicts,
            "merge_info": self.merge_info,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoutProTeam':
        """Create from dictionary (e.g., from MongoDB)"""
        # Map scoutpro_id to id
        if 'scoutpro_id' in data:
            data['id'] = data.pop('scoutpro_id')

        return cls(**data)
