"""
Entity Resolution Package

Provides functionality for matching entities across different data providers.

Components:
- PlayerResolver: Match players using name, birth date, position
- TeamResolver: Match teams using name, country, stadium
- MatchResolver: Match matches using teams, date, score
"""

from .player_resolver import PlayerResolver
from .team_resolver import TeamResolver
from .match_resolver import MatchResolver
from .base_resolver import BaseResolver

__all__ = [
    'PlayerResolver',
    'TeamResolver',
    'MatchResolver',
    'BaseResolver'
]
