import logging
from typing import Dict, Any, List

from shared.adapters.opta.taxonomies.factory import OptaEventFactory
from shared.domain.entities import BaseEventInfo

logger = logging.getLogger(__name__)

class OptaParser:
    """
    Unified entry point for raw Opta feed streams. 
    Routes unstructured raw dictionaries through Clean Architecture Domain validations.
    """
    
    def __init__(self):
        self.factory = OptaEventFactory()

    def parse_events(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses multiple raw events into strongly-typed serialized model dictionaries
        suitable for Kafka routing.
        """
        events_list = raw_data.get("events", [])
        match_id = str(raw_data.get("match_id", "") or "")
        parsed_events = []
        
        for raw_event in events_list:
            normalized_event = self._normalize_event(raw_event, match_id)

            # Map deep taxonomy
            domain_entity = self.factory.create_event(normalized_event)
            
            if domain_entity:
                # Convert the Pydantic Entity back into dicts for Kafka payload standard envelope
                parsed_events.append(domain_entity.model_dump())
            else:
                logger.warning(f"Failed to map Event ID into unified domain entity schema: {raw_event.get('id')}")

        return parsed_events

    def _normalize_event(self, raw_event: Dict[str, Any], match_id: str) -> Dict[str, Any]:
        if not isinstance(raw_event, dict):
            return {}

        normalized = dict(raw_event)
        attributes = normalized.pop("@attributes", {})
        if isinstance(attributes, dict):
            normalized.update(attributes)

        qualifiers = normalized.pop("Q", None)
        if qualifiers is not None and "qualifier" not in normalized:
            normalized["qualifier"] = self._normalize_qualifiers(qualifiers)

        if match_id and not normalized.get("game_id") and not normalized.get("match_id"):
            normalized["match_id"] = match_id

        if normalized.get("id") is None and normalized.get("event_id") is not None:
            normalized["id"] = normalized["event_id"]

        outcome = normalized.get("outcome")
        if isinstance(outcome, str) and outcome.isdigit():
            normalized["outcome"] = int(outcome)

        return normalized

    @staticmethod
    def _normalize_qualifiers(qualifiers: Any) -> List[Dict[str, Any]]:
        normalized_qualifiers = []

        if not isinstance(qualifiers, list):
            return normalized_qualifiers

        for qualifier in qualifiers:
            if not isinstance(qualifier, dict):
                continue

            attributes = qualifier.get("@attributes", {})
            if not isinstance(attributes, dict):
                continue

            normalized_qualifiers.append({
                "qualifier_id": str(attributes.get("qualifier_id", "")),
                "value": attributes.get("value") or qualifier.get("@value") or "",
            })

        return normalized_qualifiers
