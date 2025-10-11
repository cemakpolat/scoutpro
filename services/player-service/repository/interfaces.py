"""
Repository interfaces for dependency inversion
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import sys
sys.path.append('/app')
from shared.models.base import Player, PlayerStatistics


class IPlayerRepository(ABC):
    """Player repository interface"""

    @abstractmethod
    async def get_by_id(self, player_id: str) -> Optional[Player]:
        """Get player by ID"""
        pass

    @abstractmethod
    async def find_by_filters(self, filters: Dict[str, Any], limit: int = 100) -> List[Player]:
        """Find players by filters"""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[Player]:
        """Search players by name"""
        pass

    @abstractmethod
    async def get_statistics(
        self,
        player_id: str,
        stat_type: Optional[str] = None,
        per_90: bool = False
    ) -> Optional[PlayerStatistics]:
        """Get player statistics"""
        pass

    @abstractmethod
    async def create(self, player: Player) -> str:
        """Create new player"""
        pass

    @abstractmethod
    async def update(self, player_id: str, player: Player) -> bool:
        """Update player"""
        pass
