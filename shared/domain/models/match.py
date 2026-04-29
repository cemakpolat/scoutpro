"""
Canonical Match Model

ScoutProMatch represents a football match in provider-agnostic format.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime


class MatchStatus(Enum):
    """Match status"""
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"
    ABANDONED = "abandoned"


@dataclass
class ScoutProMatch:
    """
    Canonical match model

    Represents a football match with data potentially merged from multiple providers.
    """

    # ====== IDENTITY ======
    id: str                           # ScoutPro canonical ID
    external_id: str                  # Primary provider's ID
    provider: str                     # Primary data source

    # ====== TEAMS ======
    home_team_id: str                 # Reference to canonical team
    away_team_id: str                 # Reference to canonical team

    # ====== COMPETITION ======
    competition_id: str               # Reference to canonical competition
    season_id: str                    # Reference to canonical season

    # ====== MATCH INFO ======
    date: datetime                    # Match date/time
    venue: Optional[str] = None       # Stadium name
    attendance: Optional[int] = None  # Number of spectators
    referee: Optional[str] = None     # Referee name

    # ====== MATCH RESULT ======
    status: MatchStatus = MatchStatus.SCHEDULED
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_ht_score: Optional[int] = None  # Half-time score
    away_ht_score: Optional[int] = None

    # ====== LIVE DATA (if match is live) ======
    current_minute: Optional[int] = None
    current_period: Optional[int] = None

    # ====== STATISTICS (Pre-aggregated) ======
    statistics: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "home": {"possession": 62.5, "shots": 18, "xG": 2.45},
    #   "away": {"possession": 37.5, "shots": 9, "xG": 0.89}
    # }

    # ====== PROVIDER MAPPINGS ======
    provider_ids: Dict[str, str] = field(default_factory=dict)
    # Example: {"opta": "g2187923", "statsbomb": "sb3895839"}

    # ====== PROVIDER-SPECIFIC DATA ======
    provider_data: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "opta": {"source": "opta", "last_updated": "...", "data": {...}},
    #   "statsbomb": {"source": "statsbomb", "last_updated": "...", "data": {...}}
    # }

    # ====== DATA QUALITY METADATA ======
    data_quality: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "completeness_score": 0.98,
    #   "confidence_score": 1.0,
    #   "data_sources": ["opta", "statsbomb"],
    #   "conflicting_fields": []
    # }

    # ====== SCOUTPRO METADATA ======
    scoutpro_metadata: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "highlights_generated": True,
    #   "report_generated": True,
    #   "internal_notes": "High-intensity match"
    # }

    # ====== CONFLICT TRACKING ======
    conflicts: Optional[list] = None

    # ====== MERGE METADATA ======
    merge_info: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "merged_from": ["opta", "statsbomb"],
    #   "last_merge": "2025-10-28T17:00:00Z",
    #   "conflicts_detected": 0
    # }

    # ====== TIMESTAMPS ======
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_live(self) -> bool:
        """Check if match is currently live"""
        return self.status == MatchStatus.LIVE

    def is_finished(self) -> bool:
        """Check if match is finished"""
        return self.status == MatchStatus.FINISHED

    def get_result(self) -> Optional[str]:
        """Get match result as string (e.g., '3-1')"""
        if self.home_score is not None and self.away_score is not None:
            return f"{self.home_score}-{self.away_score}"
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            "scoutpro_id": self.id,
            "external_id": self.external_id,
            "provider": self.provider,
            "home_team_id": self.home_team_id,
            "away_team_id": self.away_team_id,
            "competition_id": self.competition_id,
            "season_id": self.season_id,
            "date": self.date,
            "venue": self.venue,
            "attendance": self.attendance,
            "referee": self.referee,
            "status": self.status.value,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "home_ht_score": self.home_ht_score,
            "away_ht_score": self.away_ht_score,
            "current_minute": self.current_minute,
            "current_period": self.current_period,
            "statistics": self.statistics,
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
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoutProMatch':
        """Create from dictionary (e.g., from MongoDB)"""
        # Convert status string back to enum
        if isinstance(data.get('status'), str):
            data['status'] = MatchStatus(data['status'])

        # Map scoutpro_id to id
        if 'scoutpro_id' in data:
            data['id'] = data.pop('scoutpro_id')

        return cls(**data)
