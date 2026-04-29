"""
Pass Attributes

Rich attributes for passing events, combining data from multiple providers.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Any


@dataclass
class PassAttributes:
    """
    Rich pass attributes - populated when available from providers

    This class stores detailed information about passing events.
    Different providers offer different levels of detail:
    - Opta: F24 qualifiers provide extensive detail
    - StatsBomb: Rich pass data including freeze frames
    - Basic providers: May only have pass_type
    """

    # ====== CORE PASS ATTRIBUTES ======
    pass_type: Optional[str] = None  # 'short', 'long', 'through', 'cross', 'switch'
    pass_height: Optional[str] = None  # 'ground', 'low', 'high', 'lofted'
    body_part: Optional[str] = None  # 'right_foot', 'left_foot', 'head', 'chest', 'other'
    technique: Optional[str] = None  # 'normal', 'lofted', 'flick', 'backheel', 'through'

    # ====== CONTEXT ======
    under_pressure: Optional[bool] = None  # Was passer under pressure?
    first_time: Optional[bool] = None  # One-touch pass?

    # ====== PASS OUTCOME ======
    assisted_goal: Optional[bool] = None  # Did this pass assist a goal?
    key_pass: Optional[bool] = None  # Did this lead to a shot?
    pass_into_box: Optional[bool] = None  # Pass into penalty area?
    progressive_pass: Optional[bool] = None  # Advanced play significantly?

    # ====== MEASUREMENTS ======
    pass_length_m: Optional[float] = None  # Length in meters
    pass_angle_deg: Optional[float] = None  # Angle in degrees
    pass_speed_kmh: Optional[float] = None  # Speed (if available)

    # ====== RECEIVER INFO ======
    receiver_id: Optional[str] = None  # Player who received the pass
    receiver_position: Optional[str] = None  # Receiver's position

    # ====== SET PIECE INFO ======
    corner_kick: Optional[bool] = None
    free_kick: Optional[bool] = None
    throw_in: Optional[bool] = None
    goal_kick: Optional[bool] = None

    # ====== PROVIDER-SPECIFIC DATA ======
    # Opta-specific (F24 qualifiers)
    opta_qualifiers: Optional[Dict[int, str]] = None
    # Example: {140: "82.1", 141: "52.3", 212: "1"}  # End X, End Y, Under pressure

    # StatsBomb-specific
    statsbomb_pass_type: Optional[Dict] = None  # StatsBomb's pass type object
    freeze_frame: Optional[List[Dict]] = None  # StatsBomb 360 freeze frame data
    # Example: [{"player_id": 123, "x": 65, "y": 40, "teammate": True}, ...]

    statsbomb_outcome: Optional[Dict] = None  # StatsBomb outcome object
    statsbomb_technique: Optional[Dict] = None  # StatsBomb technique details

    # ====== DERIVED METRICS ======
    expected_pass_completion: Optional[float] = None  # xPass value (if available)

    def is_forward_pass(self) -> bool:
        """Check if this is a forward pass (based on angle)"""
        if self.pass_angle_deg is not None:
            # Forward passes typically have angles between -45 and 45 degrees
            return -45 <= self.pass_angle_deg <= 45
        return False

    def is_long_pass(self) -> bool:
        """Check if this is a long pass (>30m)"""
        if self.pass_length_m is not None:
            return self.pass_length_m > 30
        return False

    def is_set_piece(self) -> bool:
        """Check if this pass was from a set piece"""
        return any([
            self.corner_kick,
            self.free_kick,
            self.throw_in,
            self.goal_kick
        ])
