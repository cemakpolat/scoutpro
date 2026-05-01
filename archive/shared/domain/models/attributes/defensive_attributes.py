"""
Defensive Attributes

Rich attributes for defensive events (tackles, interceptions, clearances, etc.).
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class DefensiveAttributes:
    """
    Rich defensive action attributes - populated when available from providers

    This class stores detailed information about defensive events.
    """

    # ====== CORE DEFENSIVE ATTRIBUTES ======
    action_type: Optional[str] = None  # 'tackle', 'interception', 'clearance', 'block'
    tackle_type: Optional[str] = None  # 'standing', 'sliding', 'aerial'
    challenge_type: Optional[str] = None  # 'ground', 'aerial'

    # ====== OUTCOME ======
    won_possession: Optional[bool] = None  # Did defender win the ball?
    successful: Optional[bool] = None  # Was action successful?
    clean_tackle: Optional[bool] = None  # Tackle without foul?

    # ====== CONTEXT ======
    zone: Optional[str] = None  # 'defensive_third', 'middle_third', 'attacking_third'
    in_penalty_area: Optional[bool] = None  # Action in own penalty area?
    last_man: Optional[bool] = None  # Last defender?

    # ====== STYLE ======
    aggressive: Optional[bool] = None  # Aggressive/risky action?
    foul_committed: Optional[bool] = None  # Did action result in foul?
    card_received: Optional[str] = None  # 'yellow', 'red', None

    # ====== OPPONENT INFO ======
    opponent_player_id: Optional[str] = None  # Player being tackled/challenged
    opponent_dribble_stopped: Optional[bool] = None  # Stopped a dribble?

    # ====== CLEARANCE-SPECIFIC ======
    clearance_head: Optional[bool] = None  # Headed clearance?
    clearance_distance_m: Optional[float] = None  # How far ball was cleared

    # ====== INTERCEPTION-SPECIFIC ======
    interception_type: Optional[str] = None  # 'pass', 'cross', 'through_ball'
    intercepted_player_id: Optional[str] = None  # Player whose pass was intercepted

    # ====== BLOCK-SPECIFIC ======
    blocked_shot: Optional[bool] = None  # Blocked a shot?
    blocked_pass: Optional[bool] = None  # Blocked a pass?
    blocked_cross: Optional[bool] = None  # Blocked a cross?
    deflection: Optional[bool] = None  # Block resulted in deflection?

    # ====== RECOVERY ======
    recovery: Optional[bool] = None  # Ball recovery (not from tackle/interception)
    recovery_type: Optional[str] = None  # 'loose_ball', 'opponent_error', etc.

    # ====== PRESSURE ======
    pressure_applied: Optional[bool] = None  # Applied pressure to opponent?
    pressure_regain: Optional[bool] = None  # Pressure led to ball recovery?
    counterpressure: Optional[bool] = None  # Immediate pressure after losing ball?

    # ====== PROVIDER-SPECIFIC DATA ======
    # Opta-specific (F24 qualifiers)
    opta_qualifiers: Optional[Dict[int, str]] = None

    # StatsBomb-specific
    statsbomb_duel_data: Optional[Dict] = None  # Full StatsBomb duel object
    # Example: {
    #   "type": {"id": 10, "name": "Aerial Lost"},
    #   "outcome": {"id": 13, "name": "Lost In Air"}
    # }

    counterpress: Optional[bool] = None  # StatsBomb counterpress indicator

    def is_successful_tackle(self) -> bool:
        """Check if this was a successful tackle"""
        return self.action_type == 'tackle' and self.won_possession is True

    def is_dangerous_area(self) -> bool:
        """Check if action was in dangerous defensive area"""
        return self.in_penalty_area or self.zone == 'defensive_third'

    def resulted_in_foul(self) -> bool:
        """Check if action resulted in a foul"""
        return self.foul_committed is True
