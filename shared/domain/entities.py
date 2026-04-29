from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List

class Coordinate(BaseModel):
    x: float
    y: float

class BaseEventInfo(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    event_id: str
    match_id: str
    player_id: Optional[str] = None
    team_id: Optional[str] = None
    minute: int
    second: int
    period: int
    type_name: str
    provider: str  # e.g., 'opta', 'statsbomb'
    location: Optional[Coordinate] = None
    
    # Raw qualifiers for fallback
    qualifiers: Dict[str, Any] = {}

class PassEvent(BaseEventInfo):
    type_name: str = "pass"
    recipient_id: Optional[str] = None
    end_location: Optional[Coordinate] = None
    is_successful: bool = False
    pass_type: Optional[str] = None # e.g., 'cross', 'long_ball', 'short'
    assist_potential: bool = False

class ShotEvent(BaseEventInfo):
    type_name: str = "shot"
    is_goal: bool = False
    shot_type: Optional[str] = None # e.g., 'header', 'left_foot', 'right_foot'
    xg_value: Optional[float] = None
    body_part: Optional[str] = None
    situation: Optional[str] = None # e.g., 'open_play', 'free_kick', 'penalty'

class FoulEvent(BaseEventInfo):
    type_name: str = "foul"
    card_type: Optional[str] = None # 'yellow', 'red', None
    is_foul_won: bool = False

class CardEvent(BaseEventInfo):
    type_name: str = "card"
    card_type: str  # 'yellow', 'red', 'second_yellow'
    reason: Optional[str] = None

class DuelEvent(BaseEventInfo):
    type_name: str = "duel"
    is_aerial: bool = False
    is_successful: bool = False

class TakeOnEvent(BaseEventInfo):
    type_name: str = "take_on"
    is_successful: bool = False

class GoalkeeperEvent(BaseEventInfo):
    type_name: str = "goalkeeper"
    action_type: str  # e.g., 'save', 'claim', 'punch', 'smother'
    is_successful: bool = False

class BallControlEvent(BaseEventInfo):
    type_name: str = "ball_control" # e.g., ball recovery, touch, dispossessed
    action_type: str 
    is_successful: bool = True

class InterceptionEvent(BaseEventInfo):
    type_name: str = "interception"
    is_successful: bool = False

class TackleEvent(BaseEventInfo):
    type_name: str = "tackle"
    is_successful: bool = False


