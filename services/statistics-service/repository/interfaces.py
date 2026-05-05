"""
Repository interfaces for dependency inversion
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import sys
sys.path.append('/app')
from shared.models.base import PlayerStatistics


class IStatisticsRepository(ABC):
    """Statistics repository interface"""

    @abstractmethod
    async def get_player_statistics(
        self,
        player_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
        per_90: bool = False
    ) -> Optional[PlayerStatistics]:
        """Get player statistics"""
        pass

    @abstractmethod
    async def get_team_statistics(
        self,
        team_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get team statistics"""
        pass

    @abstractmethod
    async def get_player_rankings(
        self,
        stat_name: str,
        position: Optional[str] = None,
        competition_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get player rankings by statistic"""
        pass

    @abstractmethod
    async def get_team_rankings(
        self,
        stat_name: str,
        competition_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get team rankings by statistic"""
        pass

    @abstractmethod
    async def get_player_comparison(
        self,
        player_ids: List[str],
        stat_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple players"""
        pass

    @abstractmethod
    async def aggregate_player_stats(
        self,
        player_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Aggregate player stats over time period"""
        pass

    @abstractmethod
    async def get_match_advanced_metrics(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get persisted advanced match metrics"""
        pass

    @abstractmethod
    async def get_match_tactical_snapshot(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get persisted tactical snapshot for a match"""
        pass

    @abstractmethod
    async def get_match_pass_network(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get persisted pass network for a match"""
        pass

    @abstractmethod
    async def get_match_sequence_summary(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get persisted sequence summary for a match"""
        pass

    @abstractmethod
    async def get_match_statistics(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get aggregated match-level statistics (box score + timeline)"""
        pass
