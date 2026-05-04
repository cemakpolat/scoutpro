"""
Canonical Player Model

ScoutProPlayer represents a football player in provider-agnostic format.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import date, datetime


@dataclass
class ScoutProPlayer:
    """
    Canonical player model - provider-agnostic

    Represents a football player with data potentially merged from multiple providers.
    """

    # ====== IDENTITY ======
    id: int                           # ScoutPro canonical numeric ID
    external_id: str                  # Primary provider's ID
    provider: str                     # Primary data source ('opta', 'statsbomb', etc.)

    # ====== BASIC INFO ======
    name: str                         # Full name
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    known_name: Optional[str] = None  # Nickname/common name (e.g., "Cristiano" for Ronaldo)

    birth_date: Optional[date] = None
    nationality: str = ""             # Primary nationality
    nationalities: List[str] = field(default_factory=list)  # All nationalities

    # ====== POSITION ======
    position: str = ""                # Standardized: GK, DF, MF, FW
    detailed_position: Optional[str] = None  # More specific: RW, LB, CDM, etc.

    # ====== PHYSICAL ATTRIBUTES ======
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    foot: Optional[str] = None        # 'left', 'right', 'both'

    # ====== CURRENT TEAM ======
    current_team_id: Optional[int] = None  # Reference to canonical team
    jersey_number: Optional[int] = None
    contract_until: Optional[date] = None
    market_value: Optional[int] = None  # In euros

    # ====== PROVIDER MAPPINGS ======
    provider_ids: Dict[str, str] = field(default_factory=dict)
    # Example: {"opta": "p123456", "statsbomb": "sb3318", "wyscout": None}

    # ====== PROVIDER-SPECIFIC DATA (Full Fidelity) ======
    provider_data: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "opta": {
    #     "source": "opta",
    #     "last_updated": "2025-10-28T10:00:00Z",
    #     "data": {full Opta player object}
    #   },
    #   "statsbomb": {
    #     "source": "statsbomb",
    #     "last_updated": "2025-10-28T09:30:00Z",
    #     "data": {full StatsBomb player object}
    #   }
    # }

    # ====== DATA QUALITY METADATA ======
    data_quality: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "completeness_score": 0.95,
    #   "confidence_score": 0.98,
    #   "last_verified": "2025-10-28T10:00:00Z",
    #   "data_sources": ["opta", "statsbomb"],
    #   "missing_fields": [],
    #   "conflicting_fields": []
    # }

    # ====== SCOUTPRO-SPECIFIC EXTENSIONS ======
    scoutpro_metadata: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "internal_rating": 92,
    #   "scout_notes": "Exceptional finisher",
    #   "tags": ["elite", "goal_threat", "fast"],
    #   "watchlist": True
    # }

    # ====== CONFLICT TRACKING ======
    conflicts: Optional[list] = None

    # ====== MERGE METADATA ======
    merge_info: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "merged_from": ["opta", "statsbomb"],
    #   "last_merge": "2025-10-28T10:00:00Z",
    #   "merge_strategy_version": "v1.2",
    #   "conflicts_detected": 0
    # }

    # ====== TIMESTAMPS ======
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def get_age(self) -> Optional[int]:
        """Calculate current age"""
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None

    def get_display_name(self) -> str:
        """Get best display name"""
        return self.known_name or self.name

    @property
    def preferred_foot(self) -> Optional[str]:
        """Backward-compatible alias for legacy code paths."""
        return self.foot

    @preferred_foot.setter
    def preferred_foot(self, value: Optional[str]) -> None:
        self.foot = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            "scoutpro_id": self.id,
            "external_id": self.external_id,
            "provider": self.provider,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "known_name": self.known_name,
            "birth_date": self.birth_date,
            "nationality": self.nationality,
            "nationalities": self.nationalities,
            "position": self.position,
            "detailed_position": self.detailed_position,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "foot": self.foot,
            "current_team_id": self.current_team_id,
            "jersey_number": self.jersey_number,
            "contract_until": self.contract_until,
            "market_value": self.market_value,
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
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoutProPlayer':
        """Create from dictionary (e.g., from MongoDB)"""
        # Map scoutpro_id to id
        if 'scoutpro_id' in data:
            data['id'] = data.pop('scoutpro_id')

        return cls(**data)
