"""
Opta event processing modules.

Only constants and the EventHandler are eagerly imported.
The legacy event-type classes (AerialDuelEvents, ShotandGoalEvents, etc.)
are still importable directly but are NOT auto-imported here to avoid
pulling in heavy optional dependencies (pandas, numpy) at startup.
"""
from .Events import EventIDs, EventTypes, EventTypesHelper
from .QTypes import QTypes

__all__ = [
    'EventIDs',
    'EventTypes',
    'EventTypesHelper',
    'QTypes',
]
