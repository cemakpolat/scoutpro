import logging
from typing import Dict, Any, Optional

from shared.domain.entities import BaseEventInfo, PassEvent, ShotEvent, Coordinate

logger = logging.getLogger(__name__)

class StatsbombMapper:
    """
    Translates raw StatsBomb Event JSON directly into our unified Domain Entity language.
    Does not rely on legacy Pandas dependencies like oldbackend/stats/src/sb.py did.
    """
    def map_event(self, raw_event: Dict[str, Any]) -> Optional[BaseEventInfo]:
        try:
            event_type_name = self._event_type_name(raw_event)
            
            # Generic base extractor
            base_data = {
                "event_id": str(raw_event.get("id")),
                "match_id": str(raw_event.get("match_id", "")), # From parent payload or injected
                "player_id": self._string_id(
                    raw_event.get("canonical_player_id")
                    or self._nested_id(raw_event, "player")
                    or raw_event.get("player_id")
                    or raw_event.get("formation_player_id")
                ),
                "team_id": self._string_id(
                    raw_event.get("canonical_team_id")
                    or self._nested_id(raw_event, "team")
                    or raw_event.get("team_id")
                    or raw_event.get("possession_team_id")
                ),
                "minute": self._as_int(raw_event.get("minute")),
                "second": self._as_int(raw_event.get("second")),
                "period": self._as_int(raw_event.get("period")),
                "type_name": event_type_name,
                "provider": "statsbomb",
                "qualifiers": {} # StatsBomb puts these inside explicit sub-dicts (e.g. 'pass')
            }
            
            # Parse Location
            location = self._location(raw_event)
            if location and isinstance(location, list) and len(location) >= 2:
                base_data["location"] = Coordinate(x=float(location[0]), y=float(location[1]))
                
            # Strategy Router
            if event_type_name == "pass":
                return self._map_pass(base_data, self._pass_data(raw_event))
            elif event_type_name == "shot":
                return self._map_shot(base_data, self._shot_data(raw_event))
            else:
                # Base Unidentified Domain entity type mapping
                return BaseEventInfo(**base_data)

        except Exception as e:
            logger.error(f"Failed to map StatsBomb Event {raw_event.get('id')}: {e}")
            return None

    def _map_pass(self, base_data: Dict[str, Any], pass_data: Dict[str, Any]) -> PassEvent:
        end_location = pass_data.get("end_location")
        is_successful = (pass_data.get("outcome") is None) # Statsbomb omits 'outcome' for successful passes
        assist_potential = (pass_data.get("shot_assist") == True)
        
        pass_type = (pass_data.get("height", {}).get("name", "unknown") == "High Pass") and "long_ball" or "short"
        if pass_data.get("cross"):
            pass_type = "cross"
            
        kwargs = {**base_data, "is_successful": is_successful, "pass_type": pass_type, "assist_potential": assist_potential}
        
        if end_location and isinstance(end_location, list) and len(end_location) >= 2:
            kwargs["end_location"] = Coordinate(x=float(end_location[0]), y=float(end_location[1]))
            
        return PassEvent(**kwargs)

    def _map_shot(self, base_data: Dict[str, Any], shot_data: Dict[str, Any]) -> ShotEvent:
        is_goal = (shot_data.get("outcome", {}).get("name", "").lower() == "goal")
        xg_value = float(shot_data.get("statsbomb_xg", 0.0))
        
        shot_type = shot_data.get("type", {}).get("name", "open_play").lower().replace(" ", "_")
        body_part = shot_data.get("body_part", {}).get("name", "foot").lower().replace(" ", "_")
        situation = shot_data.get("play_pattern", {}).get("name", "unknown").lower().replace(" ", "_")
        
        return ShotEvent(
            **base_data,
            is_goal=is_goal,
            shot_type=shot_type,
            xg_value=xg_value,
            body_part=body_part,
            situation=situation
        )

    @staticmethod
    def _event_type_name(raw_event: Dict[str, Any]) -> str:
        nested_type = raw_event.get("type")
        if isinstance(nested_type, dict):
            type_name = nested_type.get("name")
            if type_name:
                return str(type_name).lower()

        flat_type = raw_event.get("type_name") or raw_event.get("event_type_name")
        return str(flat_type or "").lower()

    @staticmethod
    def _nested_id(raw_event: Dict[str, Any], key: str) -> Optional[str]:
        nested = raw_event.get(key)
        if isinstance(nested, dict) and nested.get("id") is not None:
            return str(nested.get("id"))
        return None

    @staticmethod
    def _string_id(value: Any) -> Optional[str]:
        if value in (None, "", "None"):
            return None
        return str(value)

    @staticmethod
    def _as_int(value: Any) -> int:
        if value in (None, "", "None"):
            return 0
        text = str(value)
        return int(float(text)) if text.replace('.', '', 1).isdigit() else 0

    def _location(self, raw_event: Dict[str, Any]) -> Optional[list]:
        location = raw_event.get("location")
        if isinstance(location, list):
            return location

        x = raw_event.get("location_x")
        y = raw_event.get("location_y")
        if x in (None, "") or y in (None, ""):
            return None
        return [x, y]

    def _pass_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        pass_data = raw_event.get("pass")
        if isinstance(pass_data, dict):
            return pass_data

        end_x = raw_event.get("end_location_x")
        end_y = raw_event.get("end_location_y")
        end_location = None
        if end_x not in (None, "") and end_y not in (None, ""):
            end_location = [end_x, end_y]

        outcome_name = raw_event.get("outcome_name")
        return {
            "end_location": end_location,
            "outcome": {"name": outcome_name} if outcome_name else None,
            "height": {"name": raw_event.get("pass_height_name")} if raw_event.get("pass_height_name") else {},
            "cross": self._as_bool(raw_event.get("pass_cross")),
            "shot_assist": self._as_bool(raw_event.get("shot_shot_assist") or raw_event.get("shot_goal_assist") or raw_event.get("key_pass_id")),
        }

    def _shot_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        shot_data = raw_event.get("shot")
        if isinstance(shot_data, dict):
            return shot_data

        outcome_name = raw_event.get("outcome_name")
        play_pattern = raw_event.get("play_pattern_name")
        technique_name = raw_event.get("technique_name")
        return {
            "outcome": {"name": outcome_name} if outcome_name else {},
            "statsbomb_xg": raw_event.get("statsbomb_xg") or raw_event.get("shot_execution_xg") or 0.0,
            "type": {"name": technique_name} if technique_name else {},
            "body_part": {"name": raw_event.get("body_part_name")} if raw_event.get("body_part_name") else {},
            "play_pattern": {"name": play_pattern} if play_pattern else {},
        }

    @staticmethod
    def _as_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value in (None, "", "0", 0, "false", "False", "None"):
            return False
        return True
