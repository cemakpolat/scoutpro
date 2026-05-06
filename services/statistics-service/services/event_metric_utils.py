from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any, Dict, Optional


class EventMetricAccumulator:
    """Build additive event-derived metric increments from normalized events.

    This logic is shared by the stream processor and the batch pipeline so both
    write the same canonical metric fields into persistent statistics documents.
    """

    PASS_EVENT_TYPES = {"pass", "cross", "offside_pass", "offside pass", "corner_taken", "corner"}
    SHOT_EVENT_TYPES = {
        "shot",
        "goal",
        "miss",
        "post",
        "attempt_saved",
        "attempt saved",
        "blocked_shot",
        "blocked shot",
        "chance_missed",
        "chance missed",
    }
    RECOVERY_EVENT_TYPES = {"ball_recovery", "ball recovery", "recovery"}
    BLOCK_EVENT_TYPES = {"blocked_pass", "blocked pass", "blocked_shot", "blocked shot", "block"}

    @classmethod
    def build_increments(cls, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = str(raw_event.get("type_name", "")).strip().lower()
        increments: Dict[str, Any] = {"total_events": 1}

        if event_type in cls.PASS_EVENT_TYPES:
            increments["passes"] = 1
            if raw_event.get("is_successful"):
                increments["passes_completed"] = 1
            if cls._is_truthy(raw_event.get("progressive_pass")):
                increments["progressive_passes"] = 1
            if cls._is_truthy(raw_event.get("entered_final_third")):
                increments["final_third_entries"] = 1
            if cls._is_truthy(raw_event.get("entered_box")):
                increments["passes_into_box"] = 1
            if cls._is_truthy(raw_event.get("is_cross")) or str(raw_event.get("pass_type", "")).lower() == "cross":
                increments["crosses"] = 1
            if cls._is_truthy(raw_event.get("is_through_ball")) or str(raw_event.get("pass_type", "")).lower() == "through_ball":
                increments["through_balls"] = 1
            if cls._is_truthy(raw_event.get("is_long_ball")) or str(raw_event.get("pass_type", "")).lower() == "long_ball":
                increments["long_balls"] = 1
            if cls._is_truthy(raw_event.get("is_switch")):
                increments["switches_of_play"] = 1
            if cls._is_truthy(raw_event.get("is_key_pass")) or cls._is_truthy(raw_event.get("assist_potential")):
                increments["key_passes"] = 1
            if cls._is_truthy(raw_event.get("is_assist")):
                increments["assists"] = 1
            if cls._is_truthy(raw_event.get("is_second_assist")):
                increments["second_assists"] = 1
            if cls._is_truthy(raw_event.get("is_set_piece")):
                increments["set_piece_passes"] = 1
            pass_length = cls._optional_float(raw_event.get("pass_length"))
            if pass_length is not None:
                increments["pass_length_total"] = pass_length
            xa_value = cls._optional_float(raw_event.get("xa_value"))
            if xa_value is None:
                xa_value = cls._optional_float(raw_event.get("analytical_xa"))
            if xa_value is not None:
                increments["xA"] = xa_value
                increments["xa_total"] = xa_value
                increments["passes_with_xa"] = 1

        elif event_type in cls.SHOT_EVENT_TYPES:
            increments["shots"] = 1
            if cls._is_truthy(raw_event.get("is_on_target")) or event_type in {"goal", "attempt_saved", "attempt saved"}:
                increments["shots_on_target"] = 1
            if raw_event.get("is_goal") or event_type == "goal":
                increments["goals"] = 1
            if cls._is_truthy(raw_event.get("is_big_chance")):
                increments["big_chances"] = 1
            if (raw_event.get("is_goal") or event_type == "goal") and cls._is_truthy(raw_event.get("is_big_chance")):
                increments["big_chances_scored"] = 1
            if cls._is_truthy(raw_event.get("is_set_piece")):
                increments["set_piece_shots"] = 1
            xg_value = cls._optional_float(raw_event.get("xg_value"))
            if xg_value is None:
                xg_value = cls._optional_float(raw_event.get("analytical_xg"))
            if xg_value is None:
                xg_value = cls.compute_analytical_xg(raw_event)
            increments["xG"] = xg_value
            increments["xg_total"] = xg_value
            increments["shots_with_xg"] = 1
            shot_distance = cls._optional_float(raw_event.get("shot_distance"))
            if shot_distance is not None:
                increments["shot_distance_total"] = shot_distance
            body_part = str(raw_event.get("body_part", "")).lower()
            if "head" in body_part:
                increments["headed_shots"] = 1

        elif event_type == "foul":
            increments["fouls"] = 1

        elif event_type == "card":
            increments["cards"] = 1
            card_type = str(raw_event.get("card_type", "")).lower()
            if card_type == "yellow":
                increments["yellow_cards"] = 1
            elif card_type == "red":
                increments["red_cards"] = 1

        elif event_type == "duel":
            increments["duels"] = 1
            if raw_event.get("is_successful"):
                increments["duels_won"] = 1

        elif event_type == "aerial":
            increments["duels"] = 1
            increments["aerials"] = 1
            if raw_event.get("is_successful"):
                increments["duels_won"] = 1
                increments["aerials_won"] = 1

        elif event_type == "take_on":
            increments["take_ons"] = 1
            if raw_event.get("is_successful"):
                increments["take_ons_won"] = 1

        elif event_type == "interception":
            increments["interceptions"] = 1
            if cls._is_high_regain(raw_event):
                increments["high_regains"] = 1

        elif event_type == "tackle":
            increments["tackles"] = 1
            if raw_event.get("is_successful"):
                increments["tackles_won"] = 1
            if cls._is_high_regain(raw_event):
                increments["high_regains"] = 1

        elif event_type == "clearance":
            increments["clearances"] = 1
            if cls._is_high_regain(raw_event):
                increments["high_regains"] = 1

        elif event_type == "goalkeeper":
            increments["goalkeeper_actions"] = 1
            if raw_event.get("action_type") == "save" and raw_event.get("is_successful"):
                increments["saves"] = 1

        elif event_type == "pressure":
            increments["pressures"] = 1

        elif event_type in cls.RECOVERY_EVENT_TYPES:
            increments["recoveries"] = 1
            if cls._is_high_regain(raw_event):
                increments["high_regains"] = 1

        elif event_type == "ball_control":
            increments["ball_controls"] = 1
            action_type = str(raw_event.get("action_type", "")).lower()
            if action_type == "recovery":
                increments["recoveries"] = 1
                if cls._is_high_regain(raw_event):
                    increments["high_regains"] = 1
            elif action_type == "dispossessed":
                increments["dispossessions"] = 1

        elif event_type in cls.BLOCK_EVENT_TYPES:
            increments["blocks"] = 1

        else:
            safe_event_name = re.sub(r"[^a-z0-9]+", "_", event_type).strip("_")
            if safe_event_name:
                increments[f"event_{safe_event_name}"] = 1

        return increments

    @staticmethod
    def compute_analytical_xg(event: Dict[str, Any]) -> float:
        """Distance-based analytical xG fallback (no ML dependency)."""
        location = event.get("location") or {}
        try:
            x_value = float(location.get("x", 50))
            y_value = float(location.get("y", 50))
            delta_x = (100.0 - x_value) / 100.0 * 105.0
            delta_y = (50.0 - y_value) / 100.0 * 68.0
            distance = math.sqrt(delta_x ** 2 + delta_y ** 2)
            raw_event = event.get("raw_event") or {}
            body_part = str(event.get("body_part") or raw_event.get("body_part", "")).lower()
            shot_type = str(event.get("shot_type") or raw_event.get("shot_type", "")).lower()
            base_xg = 0.35 * math.exp(-0.1 * max(distance, 1.0))
            if "head" in body_part:
                base_xg *= 0.6
            if shot_type == "penalty":
                base_xg = 0.76
            return round(base_xg, 4)
        except Exception:
            return 0.05

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes"}
        return False

    @staticmethod
    def _optional_float(value: Any) -> Optional[float]:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _is_high_regain(cls, raw_event: Dict[str, Any]) -> bool:
        if cls._is_truthy(raw_event.get("high_regain")):
            return True

        location = raw_event.get("location") or {}
        if not isinstance(location, Mapping):
            return False

        x_value = cls._optional_float(location.get("x"))
        return x_value is not None and x_value >= 66.7