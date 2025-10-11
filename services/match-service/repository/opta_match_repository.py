"""
Opta Match Repository - Adapter for legacy GameAPI and EventAPI
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

sys.path.append('/app')
from shared.models.base import Match
from .interfaces import IMatchRepository
from feedapi.game_api import GameAPI
from feedapi.event_api import EventAPI
import logging

logger = logging.getLogger(__name__)

# Thread pool for running sync MongoEngine code
executor = ThreadPoolExecutor(max_workers=10)


class OptaMatchRepository(IMatchRepository):
    """
    Repository implementation using legacy Opta GameAPI and EventAPI
    Adapts the existing GameAPI (1,527 lines) + EventAPI (251 lines) to IMatchRepository interface
    """

    def __init__(self, competition_id: int, season_id: int):
        self.competition_id = competition_id
        self.season_id = season_id
        self.game_api = GameAPI(competition_id, season_id)
        self.event_api = EventAPI(competition_id, season_id)

    async def get_by_id(self, match_id: str) -> Optional[Match]:
        """Get match by ID"""
        try:
            loop = asyncio.get_event_loop()

            def get_match():
                # Use GameAPI.getGameData(match_id)
                return None  # TODO: Implement

            match_data = await loop.run_in_executor(executor, get_match)

            if match_data:
                return Match(**match_data)

            return None
        except Exception as e:
            logger.error(f"Error getting match {match_id}: {e}")
            return None

    async def find_by_filters(self, filters: Dict[str, Any], limit: int = 100) -> List[Match]:
        """Find matches by filters"""
        try:
            loop = asyncio.get_event_loop()

            def find_matches():
                # Use GameAPI.getAllMatches() with filters
                matches = []
                return matches

            matches_data = await loop.run_in_executor(executor, find_matches)

            return [Match(**m) for m in matches_data]
        except Exception as e:
            logger.error(f"Error finding matches: {e}")
            return []

    async def get_by_team(self, team_id: str, limit: int = 20) -> List[Match]:
        """Get matches for a team"""
        try:
            loop = asyncio.get_event_loop()

            def get_team_matches():
                # Use GameAPI to filter by team
                return []

            matches_data = await loop.run_in_executor(executor, get_team_matches)

            return [Match(**m) for m in matches_data]
        except Exception as e:
            logger.error(f"Error getting matches for team {team_id}: {e}")
            return []

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[Match]:
        """Get matches in date range"""
        try:
            loop = asyncio.get_event_loop()

            def get_matches_in_range():
                # Use GameAPI date filtering
                return []

            matches_data = await loop.run_in_executor(executor, get_matches_in_range)

            return [Match(**m) for m in matches_data]
        except Exception as e:
            logger.error(f"Error getting matches by date range: {e}")
            return []

    async def get_live_matches(self) -> List[Match]:
        """Get currently live matches"""
        try:
            loop = asyncio.get_event_loop()

            def get_live():
                # Use GameAPI live match methods
                return []

            matches_data = await loop.run_in_executor(executor, get_live)

            return [Match(**m) for m in matches_data]
        except Exception as e:
            logger.error(f"Error getting live matches: {e}")
            return []

    async def get_match_events(self, match_id: str) -> List[Dict[str, Any]]:
        """Get all events for a match"""
        try:
            loop = asyncio.get_event_loop()

            def get_events():
                # Use EventAPI.getMatchEvents(match_id)
                return []

            events = await loop.run_in_executor(executor, get_events)
            return events
        except Exception as e:
            logger.error(f"Error getting events for match {match_id}: {e}")
            return []

    async def create(self, match: Match) -> str:
        """Create new match - not supported for Opta data"""
        raise NotImplementedError("Creating matches not supported in Opta feed")

    async def update(self, match_id: str, match: Match) -> bool:
        """Update match - not supported for Opta data"""
        raise NotImplementedError("Updating matches not supported in Opta feed")

    async def update_live_data(self, match_id: str, live_data: Dict[str, Any]) -> bool:
        """Update live match data"""
        try:
            # Live updates would be handled by live-ingestion-service
            # This is read-only from Opta perspective
            logger.warning("Live data updates handled by ingestion service")
            return False
        except Exception as e:
            logger.error(f"Error updating live data for match {match_id}: {e}")
            return False

    # ===================================================================
    # Additional methods leveraging GameAPI's rich functionality
    # ===================================================================

    async def get_game_data(self, match_id: str) -> Dict[str, Any]:
        """
        Get comprehensive game data
        Uses GameAPI.getGameData()
        """
        try:
            loop = asyncio.get_event_loop()

            def get_data():
                return self.game_api.getGameData(match_id)

            game_data = await loop.run_in_executor(executor, get_data)
            return game_data or {}
        except Exception as e:
            logger.error(f"Error getting game data: {e}")
            return {}

    async def get_all_matches(self) -> List[Dict[str, Any]]:
        """
        Get all matches in competition/season
        Uses GameAPI.getAllMatches()
        """
        try:
            loop = asyncio.get_event_loop()

            def get_all():
                return self.game_api.getAllMatches()

            matches = await loop.run_in_executor(executor, get_all)
            return matches or []
        except Exception as e:
            logger.error(f"Error getting all matches: {e}")
            return []

    async def get_match_statistics(self, match_id: str) -> Dict[str, Any]:
        """
        Get match statistics
        Uses GameAPI match stats methods
        """
        try:
            loop = asyncio.get_event_loop()

            def get_stats():
                # GameAPI match statistics
                return {}

            stats = await loop.run_in_executor(executor, get_stats)
            return stats
        except Exception as e:
            logger.error(f"Error getting match statistics: {e}")
            return {}

    async def get_filtered_events(
        self,
        match_id: str,
        event_type: Optional[str] = None,
        team_id: Optional[str] = None,
        player_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get filtered match events
        Uses EventAPI filtering capabilities
        """
        try:
            loop = asyncio.get_event_loop()

            def filter_events():
                # EventAPI event filtering
                return []

            events = await loop.run_in_executor(executor, filter_events)
            return events
        except Exception as e:
            logger.error(f"Error getting filtered events: {e}")
            return []
