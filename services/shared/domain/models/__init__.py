"""
Canonical domain models
"""

from .competition import ScoutProCompetition
from .event import ScoutProEvent, EventType, EventQuality
from .match import ScoutProMatch, MatchStatus
from .player import ScoutProPlayer
from .season import ScoutProSeason
from .team import ScoutProTeam
from .venue import ScoutProVenue

__all__ = [
    'ScoutProCompetition',
    'ScoutProEvent',
    'EventType',
    'EventQuality',
    'ScoutProMatch',
    'MatchStatus',
    'ScoutProPlayer',
    'ScoutProSeason',
    'ScoutProTeam',
    'ScoutProVenue',
]
