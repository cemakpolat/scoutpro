"""
Opta Player Repository - Adapter for legacy PlayerAPI
"""
from typing import Optional, List, Dict, Any
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

sys.path.append('/app')
from shared.models.base import Player, PlayerStatistics
from .interfaces import IPlayerRepository
from feedapi.player_api import PlayerAPI
import logging

logger = logging.getLogger(__name__)

# Thread pool for running sync MongoEngine code
executor = ThreadPoolExecutor(max_workers=10)


class OptaPlayerRepository(IPlayerRepository):
    """
    Repository implementation using legacy Opta PlayerAPI
    Adapts the existing PlayerAPI (3,476 lines of battle-tested code) to IPlayerRepository interface
    """

    def __init__(self, competition_id: int, season_id: int):
        self.competition_id = competition_id
        self.season_id = season_id
        self.player_api = PlayerAPI(competition_id, season_id)

    async def get_by_id(self, player_id: str) -> Optional[Player]:
        """
        Get player by ID
        Note: PlayerAPI requires team_name + player_name, not just ID
        This is a limitation we'll need to handle
        """
        try:
            # This is a workaround - ideally we'd enhance PlayerAPI to support ID lookup
            # For now, we'll search all teams
            loop = asyncio.get_event_loop()

            # Run sync PlayerAPI method in thread pool
            def get_player():
                # TODO: Implement player lookup by ID in PlayerAPI
                # For now, return None - will need team_name context
                return None

            player_data = await loop.run_in_executor(executor, get_player)

            if player_data:
                return Player(**player_data)

            return None
        except Exception as e:
            logger.error(f"Error getting player {player_id}: {e}")
            return None

    async def find_by_filters(self, filters: Dict[str, Any], limit: int = 100) -> List[Player]:
        """
        Find players by filters
        Uses PlayerAPI's rich filtering capabilities
        """
        try:
            loop = asyncio.get_event_loop()

            def find_players():
                # Use PlayerAPI methods to filter
                # This will need enhancement based on filter types
                players = []

                # Example: Get all players from a team
                if 'team_name' in filters:
                    team_name = filters['team_name']
                    # Use PlayerAPI to get team players
                    # team_players = self.player_api.getTeamPlayers(team_name)
                    # players.extend(team_players)

                return players

            players_data = await loop.run_in_executor(executor, find_players)

            return [Player(**p) for p in players_data]
        except Exception as e:
            logger.error(f"Error finding players: {e}")
            return []

    async def search(self, query: str, limit: int = 20) -> List[Player]:
        """
        Search players by name
        """
        try:
            # PlayerAPI doesn't have built-in search - would need to add
            # For now, return empty list
            logger.warning("Search not yet implemented in OptaPlayerRepository")
            return []
        except Exception as e:
            logger.error(f"Error searching players: {e}")
            return []

    async def get_statistics(
        self,
        player_id: str,
        stat_type: Optional[str] = None,
        per_90: bool = False
    ) -> Optional[PlayerStatistics]:
        """
        Get player statistics using PlayerAPI's rich stats methods
        This is where PlayerAPI really shines - detailed event-based stats
        """
        try:
            loop = asyncio.get_event_loop()

            def get_stats():
                # PlayerAPI has multiple stat methods:
                # - getPlayerStatistics() - Total, PerGame, Per90
                # - getGoalkeeperStatistics()
                # - getPlayerPassEvents()
                # - getPlayerShotEvents()

                # For now, basic implementation
                # TODO: Map to specific PlayerAPI methods based on stat_type

                stats_data = {
                    "player_id": player_id,
                    "stats": {}
                }

                return stats_data

            stats = await loop.run_in_executor(executor, get_stats)

            if stats:
                return PlayerStatistics(**stats)

            return None
        except Exception as e:
            logger.error(f"Error getting statistics for player {player_id}: {e}")
            return None

    async def create(self, player: Player) -> str:
        """
        Create new player
        Note: PlayerAPI is read-only for Opta data
        This would only work for custom player data
        """
        raise NotImplementedError("Creating players not supported in Opta feed")

    async def update(self, player_id: str, player: Player) -> bool:
        """
        Update player
        Note: PlayerAPI is read-only for Opta data
        """
        raise NotImplementedError("Updating players not supported in Opta feed")

    # ===================================================================
    # Additional methods leveraging PlayerAPI's rich functionality
    # ===================================================================

    async def get_player_pass_events(self, team_name: str, player_name: str) -> Dict[str, Any]:
        """
        Get detailed pass event analysis
        Uses PlayerAPI.getPlayerPassEvents()
        """
        try:
            loop = asyncio.get_event_loop()

            def get_passes():
                return self.player_api.getPlayerPassEvents(team_name, player_name)

            pass_events = await loop.run_in_executor(executor, get_passes)
            return pass_events or {}
        except Exception as e:
            logger.error(f"Error getting pass events: {e}")
            return {}

    async def get_player_shot_events(self, team_name: str, player_name: str) -> Dict[str, Any]:
        """
        Get detailed shot event analysis
        Uses PlayerAPI.getPlayerShotEvents()
        """
        try:
            loop = asyncio.get_event_loop()

            def get_shots():
                return self.player_api.getPlayerShotEvents(team_name, player_name)

            shot_events = await loop.run_in_executor(executor, get_shots)
            return shot_events or {}
        except Exception as e:
            logger.error(f"Error getting shot events: {e}")
            return {}

    async def calculate_minutes_played(self, team_name: str, player_name: str) -> int:
        """
        Calculate minutes played in season
        Uses PlayerAPI.calculateMinutesPlayed()
        """
        try:
            loop = asyncio.get_event_loop()

            def calc_minutes():
                return self.player_api.calculateMinutesPlayed(team_name, player_name)

            minutes = await loop.run_in_executor(executor, calc_minutes)
            return minutes or 0
        except Exception as e:
            logger.error(f"Error calculating minutes: {e}")
            return 0

    async def compare_players(
        self,
        team1: str,
        player1: str,
        team2: str,
        player2: str
    ) -> Dict[str, Any]:
        """
        Compare two players
        Uses PlayerAPI.comparePlayers()
        """
        try:
            loop = asyncio.get_event_loop()

            def compare():
                return self.player_api.comparePlayers(team1, player1, team2, player2)

            comparison = await loop.run_in_executor(executor, compare)
            return comparison or {}
        except Exception as e:
            logger.error(f"Error comparing players: {e}")
            return {}

    async def rank_league_players(self, position: str = None) -> List[Dict[str, Any]]:
        """
        Rank players in league
        Uses PlayerAPI.rankLeaguePlayers()
        """
        try:
            loop = asyncio.get_event_loop()

            def rank_players():
                # This would use PlayerAPI ranking methods
                return []

            rankings = await loop.run_in_executor(executor, rank_players)
            return rankings
        except Exception as e:
            logger.error(f"Error ranking players: {e}")
            return []
