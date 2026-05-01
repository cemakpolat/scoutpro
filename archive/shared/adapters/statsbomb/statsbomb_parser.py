import logging
import json
from typing import Dict, Any, List

from shared.adapters.statsbomb.statsbomb_mapper import StatsbombMapper
from shared.domain.entities import BaseEventInfo

logger = logging.getLogger(__name__)

class StatsbombParser:
    """
    Unified entry point for raw StatsBomb feed streams. 
    Routes JSON files or API payloads directly to Domain Entities.
    Replaces pandas logic found in oldbackend/stats/src/sb.py.
    """
    def __init__(self):
        self.mapper = StatsbombMapper()

    def parse_events(self, raw_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parses array of raw Statsbomb JSON node dicts into structured Domain Entity
        dictionaries suitable for Kafka distribution or Database ingestion.
        """
        parsed_events = []
        for raw_event in raw_events:
            domain_entity = self.mapper.map_event(raw_event)
            
            if domain_entity:
                parsed_events.append(domain_entity.model_dump())
            else:
                logger.warning(f"Failed parsing StatsBomb Event ID {raw_event.get('id')}")

        return parsed_events
