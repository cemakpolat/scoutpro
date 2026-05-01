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
            event_type_name = raw_event.get("type", {}).get("name", "").lower()
            
            # Generic base extractor
            base_data = {
                "event_id": str(raw_event.get("id")),
                "match_id": str(raw_event.get("match_id", "")), # From parent payload or injected
                "player_id": str(raw_event.get("player", {}).get("id")) if "player" in raw_event else None,
                "team_id": str(raw_event.get("team", {}).get("id", "")),
                "minute": int(raw_event.get("minute", 0)),
                "second": int(raw_event.get("second", 0)),
                "period": int(raw_event.get("period", 0)),
                "type_name": event_type_name,
                "provider": "statsbomb",
                "qualifiers": {} # StatsBomb puts these inside explicit sub-dicts (e.g. 'pass')
            }
            
            # Parse Location
            location = raw_event.get("location")
            if location and isinstance(location, list) and len(location) >= 2:
                base_data["location"] = Coordinate(x=float(location[0]), y=float(location[1]))
                
            # Strategy Router
            if event_type_name == "pass":
                return self._map_pass(base_data, raw_event.get("pass", {}))
            elif event_type_name == "shot":
                return self._map_shot(base_data, raw_event.get("shot", {}))
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
