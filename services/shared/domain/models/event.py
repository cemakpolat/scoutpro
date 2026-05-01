"""
Canonical Event Model

ScoutProEvent is the provider-agnostic event format used throughout the system.
All provider data (Opta, StatsBomb, etc.) is mapped to this canonical format.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime


class EventType(Enum):
    """
    Standardized event taxonomy

    This enum defines all event types recognized by ScoutPro.
    Provider-specific event types are mapped to these canonical types.
    """

    # ========== PASSING ==========
    PASS_COMPLETED = "pass_completed"
    PASS_INCOMPLETE = "pass_incomplete"
    PASS_ASSIST = "pass_assist"
    PASS_KEY = "pass_key"

    # ========== SHOOTING ==========
    SHOT_ON_TARGET = "shot_on_target"
    SHOT_OFF_TARGET = "shot_off_target"
    SHOT_BLOCKED = "shot_blocked"
    GOAL = "goal"
    PENALTY = "penalty"

    # ========== DEFENSIVE ==========
    TACKLE_WON = "tackle_won"
    TACKLE_LOST = "tackle_lost"
    INTERCEPTION = "interception"
    CLEARANCE = "clearance"
    BLOCK = "block"

    # ========== POSSESSION ==========
    DRIBBLE_COMPLETED = "dribble_completed"
    DRIBBLE_INCOMPLETE = "dribble_incomplete"
    CARRY = "carry"
    TOUCH = "touch"

    # ========== FOULS & CARDS ==========
    FOUL_COMMITTED = "foul_committed"
    FOUL_SUFFERED = "foul_suffered"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"

    # ========== SET PIECES ==========
    CORNER = "corner"
    FREE_KICK = "free_kick"
    THROW_IN = "throw_in"
    GOAL_KICK = "goal_kick"

    # ========== DUELS ==========
    AERIAL_DUEL_WON = "aerial_duel_won"
    AERIAL_DUEL_LOST = "aerial_duel_lost"
    GROUND_DUEL_WON = "ground_duel_won"
    GROUND_DUEL_LOST = "ground_duel_lost"

    # ========== GOALKEEPER ==========
    SAVE = "save"
    PUNCH = "punch"
    CLAIM = "claim"
    SMOTHER = "smother"

    # ========== OTHER ==========
    OFFSIDE = "offside"
    SUBSTITUTION = "substitution"
    ERROR = "error"
    PRESSURE = "pressure"

    def get_category(self) -> str:
        """Get the category this event belongs to"""
        if self.value.startswith('pass'):
            return 'passing'
        elif self.value.startswith('shot') or self == EventType.GOAL:
            return 'shooting'
        elif self.value.startswith('tackle') or self in [EventType.INTERCEPTION, EventType.CLEARANCE, EventType.BLOCK]:
            return 'defensive'
        elif self.value.startswith('dribble') or self == EventType.CARRY:
            return 'possession'
        elif self.value.startswith('foul') or 'card' in self.value:
            return 'discipline'
        elif self in [EventType.CORNER, EventType.FREE_KICK, EventType.THROW_IN, EventType.GOAL_KICK]:
            return 'set_piece'
        elif 'duel' in self.value:
            return 'duel'
        elif self in [EventType.SAVE, EventType.PUNCH, EventType.CLAIM, EventType.SMOTHER]:
            return 'goalkeeper'
        else:
            return 'other'


class EventQuality(Enum):
    """
    Data richness/quality level

    Different providers offer different levels of detail.
    This enum tracks how much information is available for an event.
    """
    MINIMAL = 1       # Just event type + time
    BASIC = 2         # + player, location
    STANDARD = 3      # + outcome, end location
    DETAILED = 4      # + specific attributes (pass type, shot xG, etc.)
    COMPREHENSIVE = 5  # + everything (Opta F24 full qualifiers)

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented


@dataclass
class ScoutProEvent:
    """
    Canonical event model - handles varying data richness from different providers

    This is the single source of truth for event data in ScoutPro.
    All provider data is transformed into this format.

    Attributes are organized in tiers:
    - Tier 1: Minimum required (all providers must have)
    - Tier 2: Standard (most providers have)
    - Tier 3: Detailed (advanced providers)
    - Tier 4: Rich attributes (provider-specific)
    - Tier 5: Raw provider data (full preservation)
    """

    # ====== TIER 1: MINIMUM REQUIRED (ALL providers) ======
    id: str                           # ScoutPro canonical ID
    match_id: str                     # Reference to canonical match
    event_type: EventType             # Standardized event type
    minute: int                       # Match minute
    successful: bool                  # Event outcome (pass completed, shot scored, etc.)

    # ====== TIER 2: STANDARD (MOST providers) ======
    player_id: Optional[str] = None   # Reference to canonical player
    team_id: Optional[str] = None     # Reference to canonical team
    second: int = 0                   # Second within minute
    period: int = 1                   # Match period (1, 2, 3=ET, 4=penalties)
    timestamp_seconds: Optional[float] = None  # Absolute timestamp in match
    x: Optional[float] = None         # Start X coordinate (0-100, left to right)
    y: Optional[float] = None         # Start Y coordinate (0-100, bottom to top)

    # ====== TIER 3: DETAILED (ADVANCED providers) ======
    end_x: Optional[float] = None     # End X coordinate
    end_y: Optional[float] = None     # End Y coordinate
    quality_level: EventQuality = EventQuality.BASIC

    # ====== TIER 4: RICH ATTRIBUTES (Provider-specific) ======
    # These are populated from shared/domain/models/attributes/
    pass_attrs: Optional[Any] = None        # PassAttributes object
    shot_attrs: Optional[Any] = None        # ShotAttributes object
    defensive_attrs: Optional[Any] = None   # DefensiveAttributes object

    # Derived metrics (merged from multiple providers)
    derived_metrics: Dict[str, Any] = field(default_factory=dict)
    # Example: {"xg": 0.165, "xg_opta": 0.15, "xg_statsbomb": 0.18}

    # ====== TIER 5: RAW PROVIDER DATA (Full preservation) ======
    provider: str = "unknown"         # Which provider this came from
    external_id: str = ""             # Provider's ID for this event
    provider_ids: Dict[str, str] = field(default_factory=dict)  # {"opta": "evt123", "statsbomb": "sb456"}
    provider_data: Dict[str, Any] = field(default_factory=dict)  # Full raw data from each provider

    # ====== DATA QUALITY METADATA ======
    data_quality: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "completeness_score": 0.95,
    #   "confidence_score": 0.98,
    #   "data_sources": ["opta", "statsbomb"],
    #   "missing_fields": [],
    #   "conflicting_fields": []
    # }

    # ====== CORRELATION (If merged from multiple providers) ======
    correlation: Optional[Dict[str, Any]] = None
    # Example: {
    #   "is_correlated": True,
    #   "confidence": 0.95,
    #   "method": "time_location_fuzzy_match",
    #   "time_diff_seconds": 0.5,
    #   "location_diff_meters": 1.2
    # }

    # ====== CONFLICT TRACKING ======
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    # Tracks any data conflicts detected during merge

    # ====== MERGE METADATA ======
    merge_info: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "merged_from": ["opta", "statsbomb"],
    #   "last_merge": "2025-10-28T17:05:00Z",
    #   "merge_strategy_version": "v1.2"
    # }

    # ====== TIMESTAMPS ======
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def has_detailed_data(self) -> bool:
        """Check if event has rich attributes"""
        return self.quality_level >= EventQuality.DETAILED

    def get_attribute(self, key: str, default=None):
        """Safely get any attribute from rich attrs or derived metrics"""
        # Check specific attribute objects first
        if self.pass_attrs and hasattr(self.pass_attrs, key):
            return getattr(self.pass_attrs, key)
        if self.shot_attrs and hasattr(self.shot_attrs, key):
            return getattr(self.shot_attrs, key)
        if self.defensive_attrs and hasattr(self.defensive_attrs, key):
            return getattr(self.defensive_attrs, key)

        # Fall back to derived metrics
        if key in self.derived_metrics:
            return self.derived_metrics[key]

        return default

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            "scoutpro_id": self.id,
            "match_id": self.match_id,
            "event_type": self.event_type.value,
            "minute": self.minute,
            "second": self.second,
            "period": self.period,
            "timestamp_seconds": self.timestamp_seconds,
            "player_id": self.player_id,
            "team_id": self.team_id,
            "x": self.x,
            "y": self.y,
            "end_x": self.end_x,
            "end_y": self.end_y,
            "successful": self.successful,
            "quality_level": self.quality_level.value,
            "pass_attrs": self.pass_attrs.__dict__ if self.pass_attrs else None,
            "shot_attrs": self.shot_attrs.__dict__ if self.shot_attrs else None,
            "defensive_attrs": self.defensive_attrs.__dict__ if self.defensive_attrs else None,
            "derived_metrics": self.derived_metrics,
            "provider": self.provider,
            "external_id": self.external_id,
            "provider_ids": self.provider_ids,
            "provider_data": self.provider_data,
            "data_quality": self.data_quality,
            "correlation": self.correlation,
            "conflicts": self.conflicts,
            "merge_info": self.merge_info,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoutProEvent':
        """Create from dictionary (e.g., from MongoDB)"""
        # Convert event_type string back to enum
        if isinstance(data.get('event_type'), str):
            data['event_type'] = EventType(data['event_type'])

        # Convert quality_level back to enum
        if isinstance(data.get('quality_level'), int):
            data['quality_level'] = EventQuality(data['quality_level'])

        # Map scoutpro_id to id
        if 'scoutpro_id' in data:
            data['id'] = data.pop('scoutpro_id')

        return cls(**data)
