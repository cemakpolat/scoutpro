import logging
import math
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from shared.domain.entities import (
    BaseEventInfo, PassEvent, ShotEvent, FoulEvent,
    Coordinate, CardEvent, DuelEvent, TakeOnEvent, GoalkeeperEvent,
    BallControlEvent, ClearanceEvent, InterceptionEvent, TackleEvent
)

logger = logging.getLogger(__name__)

FINAL_THIRD_X = 66.7
BOX_X_MIN = 83.0
BOX_Y_MIN = 21.0
BOX_Y_MAX = 79.0
PROGRESSIVE_PASS_MIN_X = 15.0

class OptaEventStrategy(ABC):
    """
    Interface for cleanly parsing Opta events into our unified Domain Entity language.
    Isolates QType translation constraints per type_id.
    """
    @abstractmethod
    def parse(self, raw_event: Dict[str, Any]) -> Optional[BaseEventInfo]:
        pass

    def _extract_base_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        qualifier_list = raw_event.get("qualifier", [])
        qtypes = {str(q.get("qualifier_id")): q.get("value") for q in qualifier_list} if isinstance(qualifier_list, list) else {}

        minute = int(raw_event.get("min", 0))
        second = int(raw_event.get("sec", 0))
        location = Coordinate(
            x=float(raw_event.get("x", 0.0)),
            y=float(raw_event.get("y", 0.0)),
        )

        return {
            "event_id": str(raw_event.get("id")),
            "match_id": str(raw_event.get("game_id", raw_event.get("match_id", ""))),
            "player_id": str(raw_event.get("player_id")) if "player_id" in raw_event else None,
            "team_id": str(raw_event.get("team_id", "")),
            "minute": minute,
            "second": second,
            "period": int(raw_event.get("period_id", 0)),
            "provider": "opta",
            "location": location,
            "timestamp_seconds": (minute * 60) + second,
            "field_zone": self._field_zone(location.x),
            "lane": self._lane(location.y),
            "in_final_third": self._is_in_final_third(location.x),
            "in_box": self._is_in_box(location.x, location.y),
            "qualifiers": qtypes,
        }

    @staticmethod
    def _flag(qtypes: Dict[str, Any], *qualifier_ids: str) -> bool:
        return any(qualifier_id in qtypes for qualifier_id in qualifier_ids)

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _coordinate_from_qualifiers(
        cls,
        qtypes: Dict[str, Any],
        x_qualifier: str = "140",
        y_qualifier: str = "141",
    ) -> Optional[Coordinate]:
        x_value = cls._to_float(qtypes.get(x_qualifier))
        y_value = cls._to_float(qtypes.get(y_qualifier))
        if x_value is None or y_value is None:
            return None
        return Coordinate(x=x_value, y=y_value)

    @staticmethod
    def _is_successful(raw_event: Dict[str, Any]) -> bool:
        outcome = raw_event.get("outcome", 0)
        if isinstance(outcome, bool):
            return outcome
        if isinstance(outcome, str):
            return outcome.strip() == "1"
        try:
            return int(outcome) == 1
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _is_in_final_third(x_value: Optional[float]) -> bool:
        return x_value is not None and x_value >= FINAL_THIRD_X

    @staticmethod
    def _is_in_box(x_value: Optional[float], y_value: Optional[float]) -> bool:
        return (
            x_value is not None
            and y_value is not None
            and x_value >= BOX_X_MIN
            and BOX_Y_MIN <= y_value <= BOX_Y_MAX
        )

    @staticmethod
    def _field_zone(x_value: float) -> str:
        if x_value < 33.3:
            return "defensive_third"
        if x_value < FINAL_THIRD_X:
            return "middle_third"
        return "attacking_third"

    @staticmethod
    def _lane(y_value: float) -> str:
        if y_value < 33.3:
            return "left"
        if y_value > 66.7:
            return "right"
        return "center"

    @staticmethod
    def _body_part(qtypes: Dict[str, Any]) -> Optional[str]:
        if "15" in qtypes:
            return "head"
        if "72" in qtypes:
            return "left_foot"
        if "20" in qtypes:
            return "right_foot"
        if "21" in qtypes:
            return "other"
        return None

    @classmethod
    def _pass_length(cls, location: Optional[Coordinate], end_location: Optional[Coordinate], qtypes: Dict[str, Any]) -> Optional[float]:
        qualifier_length = cls._to_float(qtypes.get("212"))
        if qualifier_length is not None:
            return round(qualifier_length, 2)
        if location is None or end_location is None:
            return None
        distance = math.sqrt(((end_location.x - location.x) ** 2) + ((end_location.y - location.y) ** 2))
        return round(distance, 2)

    @classmethod
    def _pass_angle(cls, location: Optional[Coordinate], end_location: Optional[Coordinate], qtypes: Dict[str, Any]) -> Optional[float]:
        qualifier_angle = cls._to_float(qtypes.get("213"))
        if qualifier_angle is not None:
            return round(qualifier_angle, 2)
        if location is None or end_location is None:
            return None
        angle = math.degrees(math.atan2(end_location.y - location.y, end_location.x - location.x))
        return round(angle, 2)

    @staticmethod
    def _distance_to_goal(location: Optional[Coordinate]) -> Optional[float]:
        if location is None:
            return None
        dx = ((100.0 - location.x) / 100.0) * 105.0
        dy = ((50.0 - location.y) / 100.0) * 68.0
        return round(math.sqrt((dx ** 2) + (dy ** 2)), 2)

    @staticmethod
    def _angle_to_goal(location: Optional[Coordinate]) -> Optional[float]:
        if location is None:
            return None
        dx = max(100.0 - location.x, 0.1)
        angle = math.degrees(math.atan2(abs(location.y - 50.0), dx))
        return round(angle, 2)

    @staticmethod
    def _analytical_xg(location: Optional[Coordinate], body_part: Optional[str], shot_type: str) -> Optional[float]:
        distance = OptaEventStrategy._distance_to_goal(location)
        if distance is None:
            return None
        base_xg = 0.35 * math.exp(-0.1 * max(distance, 1.0))
        if body_part and "head" in body_part:
            base_xg *= 0.6
        if shot_type == "penalty":
            base_xg = 0.76
        return round(base_xg, 4)

class PassEventStrategy(OptaEventStrategy):
    """Parses Type ID 1 (Pass) into a PassEvent entity"""
    
    def parse(self, raw_event: Dict[str, Any]) -> Optional[PassEvent]:
        base_data = self._extract_base_event(raw_event)
        qtypes = base_data["qualifiers"]
        location = base_data.get("location")
        end_location = self._coordinate_from_qualifiers(qtypes)
        is_successful = self._is_successful(raw_event)

        pass_type = "short"
        if "2" in qtypes:
            pass_type = "cross"
        elif self._flag(qtypes, "4", "266"):
            pass_type = "through_ball"
        elif "196" in qtypes:
            pass_type = "switch"
        elif "1" in qtypes:
            pass_type = "long_ball"
        elif "6" in qtypes:
            pass_type = "corner"
        elif "5" in qtypes:
            pass_type = "free_kick"
        elif "107" in qtypes:
            pass_type = "throw_in"

        progressive_distance = None
        entered_final_third = False
        entered_box = False
        if location is not None and end_location is not None:
            progressive_distance = round(end_location.x - location.x, 2)
            entered_final_third = is_successful and location.x < FINAL_THIRD_X <= end_location.x
            entered_box = is_successful and not self._is_in_box(location.x, location.y) and self._is_in_box(end_location.x, end_location.y)

        is_key_pass = self._flag(qtypes, "154", "210")

        return PassEvent(
            **base_data,
            end_location=end_location,
            is_successful=is_successful,
            pass_type=pass_type,
            assist_potential=is_key_pass,
            body_part=self._body_part(qtypes),
            pass_length=self._pass_length(location, end_location, qtypes),
            pass_angle=self._pass_angle(location, end_location, qtypes),
            progressive_distance=progressive_distance,
            progressive_pass=bool(is_successful and progressive_distance is not None and progressive_distance >= PROGRESSIVE_PASS_MIN_X),
            entered_final_third=entered_final_third,
            entered_box=entered_box,
            end_field_zone=self._field_zone(end_location.x) if end_location else None,
            end_lane=self._lane(end_location.y) if end_location else None,
            is_cross=("2" in qtypes),
            is_through_ball=self._flag(qtypes, "4", "266"),
            is_long_ball=("1" in qtypes),
            is_switch=("196" in qtypes),
            is_cutback=("195" in qtypes),
            is_key_pass=is_key_pass,
            is_assist=("210" in qtypes),
            is_second_assist=("218" in qtypes),
            is_set_piece=self._flag(qtypes, "5", "6", "107", "241", "279"),
        )

class ShotEventStrategy(OptaEventStrategy):
    """Parses blocked, missed, saved, woodwork, and goal shot events."""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[ShotEvent]:
        base_data = self._extract_base_event(raw_event)
        qtypes = base_data["qualifiers"]
        type_id = int(raw_event.get("type_id", 0))
        location = base_data.get("location")
        is_goal = (type_id == 16)

        outcome_map = {
            10: "blocked",
            13: "off_target",
            14: "hit_woodwork",
            15: "saved",
            16: "goal",
        }

        shot_type = "open_play"
        if "9" in qtypes:
            shot_type = "penalty"
        elif "26" in qtypes or "97" in qtypes:
            shot_type = "free_kick"
        elif self._flag(qtypes, "25", "96"):
            shot_type = "corner"

        body_part = self._body_part(qtypes) or "foot"
        xg_value = float(qtypes.get("321", 0.0)) if "321" in qtypes else None

        return ShotEvent(
            **base_data,
            is_goal=is_goal,
            shot_type=shot_type,
            body_part=body_part,
            xg_value=xg_value,
            situation="set_piece" if shot_type != "open_play" else "open_play",
            shot_outcome=outcome_map.get(type_id, "unknown"),
            is_on_target=(type_id in {15, 16}),
            is_big_chance=("214" in qtypes),
            is_first_time=("328" in qtypes),
            is_assisted=self._flag(qtypes, "29", "154", "210", "217"),
            is_set_piece=(shot_type != "open_play"),
            shot_distance=self._distance_to_goal(location),
            shot_angle=self._angle_to_goal(location),
            analytical_xg=self._analytical_xg(location, body_part, shot_type),
            from_corner=(shot_type == "corner"),
            from_free_kick=(shot_type == "free_kick"),
            is_penalty=(shot_type == "penalty"),
        )

class FoulEventStrategy(OptaEventStrategy):
    """Parses Type ID 4 (Foul) into a FoulEvent entity"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[FoulEvent]:
        base_data = self._extract_base_event(raw_event)
        qtypes = base_data["qualifiers"]
        
        # 13 = Foul drawn/won? Often 4 is Foul, outcome differs or Qtype 13
        is_foul_won = ("13" in qtypes)

        card_type = None
        if "31" in qtypes:
            card_type = "yellow"
        elif "32" in qtypes:
            card_type = "second_yellow"
        elif "33" in qtypes:
            card_type = "red"

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
            card_type = "red"
        elif "32" in qtypes:
            card_type = "second_yellow"
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
        is_successful = self._is_successful(raw_event)

        return DuelEvent(
            **base_data,
            is_aerial=is_aerial,
            is_successful=is_successful
        )

class TakeOnEventStrategy(OptaEventStrategy):
    """Parses Take-on / Dribble (e.g. Type ID 3)"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[TakeOnEvent]:
        base_data = self._extract_base_event(raw_event)
        is_successful = self._is_successful(raw_event)

        return TakeOnEvent(
            **base_data,
            is_successful=is_successful
        )

class GoalkeeperEventStrategy(OptaEventStrategy):
    """Parses claim, smother, and penalty-save goalkeeper events."""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[GoalkeeperEvent]:
        base_data = self._extract_base_event(raw_event)
        type_id = int(raw_event.get("type_id", 0))

        action_map = {
            11: "claim",
            41: "smother",
            58: "penalty_save"
        }
        action_type = action_map.get(type_id, "unknown")
        is_successful = self._is_successful(raw_event)

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
        location = base_data.get("location")

        action_type = "recovery" if type_id == 49 else "dispossessed" if type_id == 50 else "touch"
        is_successful = (type_id == 49)

        return BallControlEvent(
            **base_data,
            action_type=action_type,
            is_successful=is_successful,
            high_regain=bool(location and action_type == "recovery" and self._is_in_final_third(location.x))
        )

class InterceptionEventStrategy(OptaEventStrategy):
    """Parses Interception (8)"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[InterceptionEvent]:
        base_data = self._extract_base_event(raw_event)
        location = base_data.get("location")
        is_successful = self._is_successful(raw_event)

        return InterceptionEvent(
            **base_data,
            is_successful=is_successful,
            high_regain=bool(location and self._is_in_final_third(location.x))
        )

class TackleEventStrategy(OptaEventStrategy):
    """Parses Tackle (7)"""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[TackleEvent]:
        base_data = self._extract_base_event(raw_event)
        location = base_data.get("location")
        is_successful = self._is_successful(raw_event)

        return TackleEvent(
            **base_data,
            is_successful=is_successful,
            high_regain=bool(location and self._is_in_final_third(location.x))
        )


class ClearanceEventStrategy(OptaEventStrategy):
    """Parses Clearance (12)."""
    def parse(self, raw_event: Dict[str, Any]) -> Optional[ClearanceEvent]:
        base_data = self._extract_base_event(raw_event)
        location = base_data.get("location")
        is_successful = self._is_successful(raw_event)

        return ClearanceEvent(
            **base_data,
            is_successful=is_successful,
            high_regain=bool(location and self._is_in_final_third(location.x))
        )

