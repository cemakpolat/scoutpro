"""
Opta event processing modules
"""
# Export all event modules
from .Events import EventIDs
from .QTypes import QTypes
from .PassEvent import *
from .ShotandGoalEvents import *
from .GoalkeeperEvents import *
from .DuelEvents import *
from .TouchEvents import *
from .AerialDuelEvents import *
from .event_handler import EventHandler, GamesandMinutesEvents

__all__ = [
    'EventIDs',
    'QTypes',
    'EventHandler',
    'GamesandMinutesEvents',
]
