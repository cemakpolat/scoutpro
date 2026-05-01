"""
Merger Package

Provides functionality for merging data from multiple providers.

Components:
- Merger classes: MatchMerger, EventMerger, PlayerMerger, TeamMerger
- Merge strategies: prefer_primary, average, keep_both, etc.
- Conflict detection: ConflictDetector for logging discrepancies
"""

from .match_merger import MatchMerger
from .event_merger import EventMerger
from .player_merger import PlayerMerger
from .team_merger import TeamMerger
from .conflict_detector import ConflictDetector, ConflictSeverity
from .base_merger import BaseMerger

__all__ = [
    'MatchMerger',
    'EventMerger',
    'PlayerMerger',
    'TeamMerger',
    'ConflictDetector',
    'ConflictSeverity',
    'BaseMerger'
]
