"""
Repository interfaces for dependency inversion
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
sys.path.append('/app')
from shared.models.base import Match


class IMatchRepository(ABC):
    """Match repository interface"""

    @abstractmethod
    async def get_by_id(self, match_id: str) -> Optional[Match]:
        """Get match by ID"""
        pass

    @abstractmethod
    async def find_by_filters(self, filters: Dict[str, Any], limit: int = 100) -> List[Match]:
        """Find matches by filters"""
        pass

    @abstractmethod
    async def get_by_team(self, team_id: str, limit: int = 20) -> List[Match]:
        """Get matches for a team"""
        pass

    @abstractmethod
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[Match]:
        """Get matches in date range"""
        pass

    @abstractmethod
    async def get_live_matches(self) -> List[Match]:
        """Get currently live matches"""
        pass

    @abstractmethod
    async def get_match_events(self, match_id: str) -> List[Dict[str, Any]]:
        """Get all events for a match"""
        pass

    @abstractmethod
    async def create(self, match: Match) -> str:
        """Create new match"""
        pass

    @abstractmethod
    async def update(self, match_id: str, match: Match) -> bool:
        """Update match"""
        pass

    @abstractmethod
    async def update_live_data(self, match_id: str, live_data: Dict[str, Any]) -> bool:
        """Update live match data"""
        pass
