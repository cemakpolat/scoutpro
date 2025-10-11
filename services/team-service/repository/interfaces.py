"""
Repository interfaces for dependency inversion
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import sys
sys.path.append('/app')
from shared.models.base import Team


class ITeamRepository(ABC):
    """Team repository interface"""

    @abstractmethod
    async def get_by_id(self, team_id: str) -> Optional[Team]:
        """Get team by ID"""
        pass

    @abstractmethod
    async def find_by_filters(self, filters: Dict[str, Any], limit: int = 100) -> List[Team]:
        """Find teams by filters"""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[Team]:
        """Search teams by name"""
        pass

    @abstractmethod
    async def get_squad(self, team_id: str) -> List[Dict[str, Any]]:
        """Get team squad"""
        pass

    @abstractmethod
    async def create(self, team: Team) -> str:
        """Create new team"""
        pass

    @abstractmethod
    async def update(self, team_id: str, team: Team) -> bool:
        """Update team"""
        pass
