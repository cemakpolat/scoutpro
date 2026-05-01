"""
Rich attribute classes for event-specific data
"""

from .pass_attributes import PassAttributes
from .shot_attributes import ShotAttributes
from .defensive_attributes import DefensiveAttributes

__all__ = [
    'PassAttributes',
    'ShotAttributes',
    'DefensiveAttributes',
]
