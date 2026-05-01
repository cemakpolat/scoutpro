import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Optional

from shared.domain.entities import (
    BaseEventInfo, PassEvent, ShotEvent, FoulEvent,
    Coordinate, CardEvent, DuelEvent, TakeOnEvent, GoalkeeperEvent,
    BallControlEvent, InterceptionEvent, TackleEvent
)

logger = logging.getLogger(__name__)

class OptaEventStrategy(ABC):
    """
    Interface for cleanly parsing Opta events into our unified Domain Entity language.
    Isolates QType translation constraints per type_id.
    """
    @abstractmethod
    def parse(self, raw_event: Dict[str, Any]) -> Optional[BaseEventInfo]:
        pass
    
    def _extract_base_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        # Extract qualifiers safely
        qualifier_list = raw_event.get("qualifier", [])
        qtypes = {str(q.get("qualifier_id")): q.get("value") for q in qualifier_list} if isinstance(qualifier_list, list) else {}
        
        return {
            "event_id": str(raw_event.get("id")),
            "match_id": str(raw_event.get("game_id", raw_event.get("match_id", ""))),
            "player_id": str(raw_event.get("player_id")) if "player_id" in raw_event else None,
            "team_id": str(raw_event.get("team_id", "")),
            "minute": int(raw_event.get("min", 0)),
            "second": int(raw_event.get("sec", 0)),
            "period": int(raw_event.get("period_id", 0)),
            "provider": "opta",
            "location": Coordinate(x=float(raw_event.get("x", 0.0)), y=float(raw_event.get("y", 0.0))),
            "qualifiers": qtypes
        }

class PassEventStrategy(OptaEventStrategy):
    """Parses Type ID 1 (Pass) into a PassEvent entity"""
    
    def parse(self, raw_event: Dict[str, Any]) -> Optional[PassEvent]:
        # Start with standard extracted base info
        base_data = self._extract_base_event(raw_event)
        qtypes = base_data["qualifiers"]
        
        # Opta Standard Qualifiers:
        # 140 = Pass end X, 141 = Pass end Y
        # 212 = Cross, 1 = Long Ball, 196 = Switch
        end_location = None
        if "140" in qtypes and "141" in qtypes:
            end_location = Coordinate(x=float(qtypes["140"]), y=float(qtypes["141"]))
        
        # Outcome is typically in outcome field of Opta payload.
        is_successful = bool(raw_event.get("outcome", 0))

        # Determine pass type from qualifier types
        pass_type = "short"
        if "212" in qtypes: pass_type = "cross"
        elif "1" in qtypes: pass_type = "long_ball"
        elif "196" in qtypes: pass_type = "switch"
        
        return PassEvent(
            **base_data,
            end_location=end_location,
            is_successful=is_successful,
            pass_type=pass_type,
            assist_potential=("210" in qtypes) # 210 = Assist
        )

class ShotEventStrategy(OptaEventStrategy):
    """Parses Type ID 13, 14, 15, 16 into a ShotEvent entity"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[ShotEvent]:
        base_data = self._extract_base_event(raw_event)
        qtypes = base_data["qualifiers"]
        type_id = int(raw_event.get("type_id", 0))
        
        is_goal = (type_id == 16)
        
        # 15 = Header, 9 = Penalty, 26 = Free Kick
        shot_type = "open_play"
        body_part = "foot"
        
        if "15" in qtypes: body_part = "header"
        if "20" in qtypes: body_part = "right_foot"
        if "72" in qtypes: body_part = "left_foot"
        
        if "9" in qtypes: shot_type = "penalty"
        elif "26" in qtypes: shot_type = "free_kick"
        
        # Optional: Advanced Stats Integration
        xg_value = float(qtypes.get("321", 0.0)) if "321" in qtypes else None
        
        return ShotEvent(
            **base_data,
            is_goal=is_goal,
            shot_type=shot_type,
            body_part=body_part,
            xg_value=xg_value
            # situation missing mapping, mapped 'shot_type' logic above
        )

class FoulEventStrategy(OptaEventStrategy):
    """Parses Type ID 4 (Foul) into a FoulEvent entity"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[FoulEvent]:
        base_data = self._extract_base_event(raw_event)
        qtypes = base_data["qualifiers"]
        
        # 13 = Foul drawn/won? Often 4 is Foul, outcome differs or Qtype 13
        is_foul_won = ("13" in qtypes)
        
        card_type = None
        if "31" in qtypes: card_type = "yellow"
        elif "32" in qtypes: card_type = "red"
        elif "33" in qtypes: card_type = "second_yellow"
        
        return FoulEvent(
            **base_data,
            is_foul_won=is_foul_won,
            card_type=card_type
        )

class CardEventStrategy(OptaEventStrategy):
    """Parses Type ID 17 (Card) into a CardEvent"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[CardEvent]:
        base_data = self._extract_base_event(raw_event)
        qtypes = base_data["qualifiers"]
        
        card_type = "yellow"
        if "33" in qtypes:
            card_type = "second_yellow"
        elif "32" in qtypes:
            card_type = "red"
        elif "31" in qtypes:
            card_type = "yellow"
            
        return CardEvent(
            **base_data,
            card_type=card_type,
            reason="foul" # Could extract more from QTypes
        )

class DuelEventStrategy(OptaEventStrategy):
    """Parses Type ID 44 (Aerial) and others into DuelEvent"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[DuelEvent]:
        base_data = self._extract_base_event(raw_event)
        type_id = int(raw_event.get("type_id", 0))
        
        is_aerial = (type_id == 44)
        is_successful = bool(raw_event.get("outcome", 0))
        
        return DuelEvent(
            **base_data,
            is_aerial=is_aerial,
            is_successful=is_successful
        )

class TakeOnEventStrategy(OptaEventStrategy):
    """Parses Take-on / Dribble (e.g. Type ID 3)"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[TakeOnEvent]:
        base_data = self._extract_base_event(raw_event)
        is_successful = bool(raw_event.get("outcome", 0))
        
        return TakeOnEvent(
            **base_data,
            is_successful=is_successful
        )

class GoalkeeperEventStrategy(OptaEventStrategy):
    """Parses GK events (e.g., 10 for Save, 11 for Claim, 12 for Clearance, 41 for Smother)"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[GoalkeeperEvent]:
        base_data = self._extract_base_event(raw_event)
        type_id = int(raw_event.get("type_id", 0))
        
        action_map = {
            10: "save",
            11: "claim",
            41: "smother",
            58: "penalty_save"
        }
        action_type = action_map.get(type_id, "unknown")
        is_successful = bool(raw_event.get("outcome", 1)) # Usually successful if logged as save/claim
        
        return GoalkeeperEvent(
            **base_data,
            action_type=action_type,
            is_successful=is_successful
        )

class BallControlEventStrategy(OptaEventStrategy):
    """Parses Ball Recovery (49) or Dispossessed (50)"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[BallControlEvent]:
        base_data = self._extract_base_event(raw_event)
        type_id = int(raw_event.get("type_id", 0))
        
        action_type = "recovery" if type_id == 49 else "dispossessed" if type_id == 50 else "touch"
        is_successful = (type_id == 49) # Recovery = success, dispossessed = failure
        
        return BallControlEvent(
            **base_data,
            action_type=action_type,
            is_successful=is_successful
        )

class InterceptionEventStrategy(OptaEventStrategy):
    """Parses Interception (8)"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[InterceptionEvent]:
        base_data = self._extract_base_event(raw_event)
        is_successful = bool(raw_event.get("outcome", 0))
        
        return InterceptionEvent(
            **base_data,
            is_successful=is_successful
        )

class TackleEventStrategy(OptaEventStrategy):
    """Parses Tackle (7)"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[TackleEvent]:
        base_data = self._extract_base_event(raw_event)
        is_successful = bool(raw_event.get("outcome", 0))
        
        return TackleEvent(
            **base_data,
            is_successful=is_successful
        )

