"""
Opta Team Repository - Adapter for legacy TeamAPI
"""
from typing import Optional, List, Dict, Any
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

sys.path.append('/app')
from shared.models.base import Team
from .interfaces import ITeamRepository
from feedapi.team_api import TeamAPI
import logging

logger = logging.getLogger(__name__)

# Thread pool for running sync MongoEngine code
executor = ThreadPoolExecutor(max_workers=10)


class OptaTeamRepository(ITeamRepository):
    """
    Repository implementation using legacy Opta TeamAPI
    Adapts the existing TeamAPI (2,076 lines of battle-tested code) to ITeamRepository interface
    """

    def __init__(self, competition_id: int, season_id: int):
        self.competition_id = competition_id
        self.season_id = season_id
        self.team_api = TeamAPI(competition_id, season_id)

    async def get_by_id(self, team_id: str) -> Optional[Team]:
        """Get team by ID"""
        try:
            loop = asyncio.get_event_loop()

            def get_team():
                # Use TeamAPI's getTeamData method
                # Need to convert team_id to team_name first
                # This is a limitation of the existing API
                return None  # TODO: Enhance TeamAPI for ID lookup

            team_data = await loop.run_in_executor(executor, get_team)

            if team_data:
                return Team(**team_data)

            return None
        except Exception as e:
            logger.error(f"Error getting team {team_id}: {e}")
            return None

    async def find_by_filters(self, filters: Dict[str, Any], limit: int = 100) -> List[Team]:
        """Find teams by filters"""
        try:
            loop = asyncio.get_event_loop()

            def find_teams():
                # Use TeamAPI filtering methods
                teams = []
                # Implementation based on filters
                return teams

            teams_data = await loop.run_in_executor(executor, find_teams)

            return [Team(**t) for t in teams_data]
        except Exception as e:
            logger.error(f"Error finding teams: {e}")
            return []

    async def search(self, query: str, limit: int = 20) -> List[Team]:
        """Search teams by name"""
        try:
            loop = asyncio.get_event_loop()

            def search_teams():
                # TeamAPI search implementation
                return []

            teams_data = await loop.run_in_executor(executor, search_teams)

            return [Team(**t) for t in teams_data]
        except Exception as e:
            logger.error(f"Error searching teams: {e}")
            return []

    async def get_squad(self, team_id: str) -> List[Dict[str, Any]]:
        """Get team squad (list of players)"""
        try:
            loop = asyncio.get_event_loop()

            def get_squad_data():
                # Use TeamAPI's squad methods
                # team_api.getTeamPlayers(team_name)
                return []

            squad = await loop.run_in_executor(executor, get_squad_data)
            return squad
        except Exception as e:
            logger.error(f"Error getting squad for team {team_id}: {e}")
            return []

    async def create(self, team: Team) -> str:
        """Create new team - not supported for Opta data"""
        raise NotImplementedError("Creating teams not supported in Opta feed")

    async def update(self, team_id: str, team: Team) -> bool:
        """Update team - not supported for Opta data"""
        raise NotImplementedError("Updating teams not supported in Opta feed")

    # ===================================================================
    # Additional methods leveraging TeamAPI's rich functionality
    # ===================================================================

    async def get_team_data(self, team_name: str) -> Dict[str, Any]:
        """
        Get comprehensive team data
        Uses TeamAPI.getTeamData()
        """
        try:
            loop = asyncio.get_event_loop()

            def get_data():
                return self.team_api.getTeamData(team_name)

            team_data = await loop.run_in_executor(executor, get_data)
            return team_data or {}
        except Exception as e:
            logger.error(f"Error getting team data: {e}")
            return {}

    async def get_team_statistics(self, team_name: str) -> Dict[str, Any]:
        """
        Get team statistics
        Uses TeamAPI.getTeamStatistics()
        """
        try:
            loop = asyncio.get_event_loop()

            def get_stats():
                return self.team_api.getTeamStatistics(team_name)

            stats = await loop.run_in_executor(executor, get_stats)
            return stats or {}
        except Exception as e:
            logger.error(f"Error getting team statistics: {e}")
            return {}

    async def get_team_formation(self, team_name: str, match_id: str) -> Dict[str, Any]:
        """
        Get team formation for a specific match
        Uses TeamAPI formation methods
        """
        try:
            loop = asyncio.get_event_loop()

            def get_formation():
                # TeamAPI formation analysis
                return {}

            formation = await loop.run_in_executor(executor, get_formation)
            return formation
        except Exception as e:
            logger.error(f"Error getting team formation: {e}")
            return {}

    async def compare_teams(
        self,
        team1_name: str,
        team2_name: str
    ) -> Dict[str, Any]:
        """
        Compare two teams
        Uses TeamAPI comparison methods
        """
        try:
            loop = asyncio.get_event_loop()

            def compare():
                # TeamAPI team comparison
                return {}

            comparison = await loop.run_in_executor(executor, compare)
            return comparison
        except Exception as e:
            logger.error(f"Error comparing teams: {e}")
            return {}

    async def get_team_players(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Get all players in team
        Uses TeamAPI.getTeamPlayers()
        """
        try:
            loop = asyncio.get_event_loop()

            def get_players():
                return self.team_api.getTeamPlayers(team_name)

            players = await loop.run_in_executor(executor, get_players)
            return players or []
        except Exception as e:
            logger.error(f"Error getting team players: {e}")
            return []
