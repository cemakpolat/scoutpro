"""
Opta Adapter

Wraps existing Opta parsing logic and transforms data to ScoutPro canonical format.
"""

from .opta_mapper import OptaMapper
from .opta_connector import OptaConnector
from .opta_event_taxonomy import OptaEventTaxonomy

__all__ = ['OptaMapper', 'OptaConnector', 'OptaEventTaxonomy']
