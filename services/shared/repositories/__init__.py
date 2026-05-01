"""
Repository Package

Provides data access layer for storing and retrieving canonical entities.

Components:
- BaseRepository: Abstract base class for all repositories
- PlayerRepository: Repository for player entities
- TeamRepository: Repository for team entities
- MatchRepository: Repository for match entities
- EventRepository: Repository for event entities

Usage:
    from shared.repositories import PlayerRepository, MatchRepository

    player_repo = PlayerRepository()
    players = player_repo.find_by_position('forward', limit=20)

    match_repo = MatchRepository()
    matches = match_repo.find_by_team('team_123')
"""

from .base_repository import BaseRepository
from .player_repository import PlayerRepository
from .team_repository import TeamRepository
from .match_repository import MatchRepository
from .event_repository import EventRepository

__all__ = [
    'BaseRepository',
    'PlayerRepository',
    'TeamRepository',
    'MatchRepository',
    'EventRepository'
]
