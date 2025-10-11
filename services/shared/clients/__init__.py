"""
Service clients for inter-service HTTP communication
"""
from .base_client import BaseServiceClient
from .player_client import PlayerServiceClient
from .team_client import TeamServiceClient
from .match_client import MatchServiceClient

__all__ = [
    'BaseServiceClient',
    'PlayerServiceClient',
    'TeamServiceClient',
    'MatchServiceClient'
]
