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
        parsed_events = []
        
        for raw_event in events_list:
            
            # Map deep taxonomy
            domain_entity = self.factory.create_event(raw_event)
            
            if domain_entity:
                # Convert the Pydantic Entity back into dicts for Kafka payload standard envelope
                parsed_events.append(domain_entity.model_dump())
            else:
                logger.warning(f"Failed to map Event ID into unified domain entity schema: {raw_event.get('id')}")

        return parsed_events
