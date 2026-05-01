"""
Shot Attributes

Rich attributes for shooting events, combining data from multiple providers.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Any


@dataclass
class ShotAttributes:
    """
    Rich shot attributes - populated when available from providers

    This class stores detailed information about shooting events.
    Different providers offer different xG models and shot details.
    """

    # ====== CORE SHOT ATTRIBUTES ======
    body_part: Optional[str] = None  # 'right_foot', 'left_foot', 'head', 'other'
    shot_type: Optional[str] = None  # 'open_play', 'free_kick', 'penalty', 'corner'
    shot_technique: Optional[str] = None  # 'normal', 'volley', 'half_volley', 'overhead', 'diving_header'

    # ====== SHOT OUTCOME ======
    shot_outcome: Optional[str] = None  # 'goal', 'saved', 'missed', 'blocked', 'post'
    blocked: Optional[bool] = None  # Was shot blocked?
    deflected: Optional[bool] = None  # Was shot deflected?

    # ====== CONTEXT ======
    one_on_one: Optional[bool] = None  # 1v1 with goalkeeper?
    big_chance: Optional[bool] = None  # Clear goal-scoring opportunity?
    first_time: Optional[bool] = None  # Shot without controlling ball first?
    under_pressure: Optional[bool] = None  # Was shooter under pressure?

    # ====== MEASUREMENTS ======
    distance_to_goal_m: Optional[float] = None  # Distance to goal in meters
    angle_to_goal_deg: Optional[float] = None  # Angle to goal in degrees
    shot_speed_kmh: Optional[float] = None  # Shot speed (if available)

    # ====== GOALKEEPER INFO ======
    goalkeeper_position: Optional[Dict] = None  # GK position at shot
    # Example: {"x": 100, "y": 50}

    # ====== DEFENSIVE PRESSURE ======
    defenders_in_way: Optional[int] = None  # Number of defenders between shooter and goal
    defenders_blocking: Optional[int] = None  # Number of defenders actively blocking

    # ====== EXPECTED GOALS (xG) ======
    xG: Optional[float] = None  # Merged/averaged xG from all providers
    xG_opta: Optional[float] = None  # Opta's xG model
    xG_statsbomb: Optional[float] = None  # StatsBomb's xG model
    xG_wyscout: Optional[float] = None  # Wyscout's xG model

    # ====== SET PIECE INFO ======
    penalty: Optional[bool] = None
    free_kick: Optional[bool] = None
    corner: Optional[bool] = None

    # ====== ASSIST INFO (if goal) ======
    assisted: Optional[bool] = None
    assist_player_id: Optional[str] = None
    assist_type: Optional[str] = None  # 'pass', 'cross', 'through_ball', etc.

    # ====== PROVIDER-SPECIFIC DATA ======
    # Opta-specific (F24 qualifiers)
    opta_qualifiers: Optional[Dict[int, str]] = None
    # Example: {20: "1", 82: "1"}  # Shot from penalty area, blocked

    # StatsBomb-specific
    statsbomb_shot_data: Optional[Dict] = None  # Full StatsBomb shot object
    # Example: {
    #   "type": {"id": 87, "name": "Open Play"},
    #   "body_part": {"id": 40, "name": "Right Foot"},
    #   "outcome": {"id": 97, "name": "Goal"},
    #   "technique": {"id": 93, "name": "Normal"}
    # }

    freeze_frame: Optional[List[Dict]] = None  # StatsBomb 360 freeze frame
    # Positions of all players at moment of shot

    # ====== GOAL-SPECIFIC (if shot resulted in goal) ======
    goal_mouth_coordinates: Optional[Dict] = None  # Where shot crossed line
    # Example: {"y": 45.2, "z": 1.8}  # Y = horizontal, Z = vertical

    def is_goal(self) -> bool:
        """Check if shot resulted in a goal"""
        return self.shot_outcome == 'goal'

    def is_on_target(self) -> bool:
        """Check if shot was on target"""
        return self.shot_outcome in ['goal', 'saved']

    def is_big_chance(self) -> bool:
        """Check if this was a big chance"""
        if self.big_chance is not None:
            return self.big_chance
        # Heuristic: high xG shots are big chances
        if self.xG is not None and self.xG > 0.3:
            return True
        return False

    def get_best_xg(self) -> Optional[float]:
        """Get the best available xG value"""
        # Prefer merged xG, fallback to provider-specific
        if self.xG is not None:
            return self.xG
        if self.xG_statsbomb is not None:
            return self.xG_statsbomb
        if self.xG_opta is not None:
            return self.xG_opta
        if self.xG_wyscout is not None:
            return self.xG_wyscout
        return None
