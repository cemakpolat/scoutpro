"""
HTTP Client for Team Service
"""
from typing import Optional, Dict, Any, List
from .base_client import BaseServiceClient
import os


class TeamServiceClient(BaseServiceClient):
    """
    Client for communicating with Team Service API
    Replaces direct TeamAPI calls in microservices architecture
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Team Service client

        Args:
            base_url: Base URL of team service (default: from env or http://team-service:8000)
        """
        if base_url is None:
            base_url = os.getenv("TEAM_SERVICE_URL", "http://team-service:8000")
        super().__init__(base_url)

    # ============ Team Data Methods ============

    async def get_team_by_id(self, team_id: str) -> Optional[Dict[str, Any]]:
        """
        Get team by ID

        Args:
            team_id: Team ID

        Returns:
            Team data or None
        """
        try:
            return await self._get(f"/api/v2/teams/{team_id}")
        except Exception:
            return None

    async def get_team_by_name(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Get team by name

        Args:
            team_name: Team name

        Returns:
            Team data or None
        """
        params = {"name": team_name}
        try:
            return await self._get("/api/v2/teams/by-name", params=params)
        except Exception:
            return None

    async def get_team_data(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive team data (legacy TeamAPI.getTeamData)

        Args:
            team_name: Team name

        Returns:
            Team data or None
        """
        return await self.get_team_by_name(team_name)

    async def search_teams(
        self,
        query: Optional[str] = None,
        competition_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for teams

        Args:
            query: Search query (team name)
            competition_id: Filter by competition
            limit: Maximum results

        Returns:
            List of teams
        """
        params = {"limit": limit}
        if query:
            params["q"] = query
        if competition_id:
            params["competition_id"] = competition_id

        try:
            response = await self._get("/api/v2/teams", params=params)
            return response.get("teams", [])
        except Exception:
            return []

    # ============ Team Statistics Methods ============

    async def get_team_statistics(
        self,
        team_id: Optional[str] = None,
        team_name: Optional[str] = None,
        stat_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get team statistics (legacy TeamAPI.getTeamStatistics)

        Args:
            team_id: Team ID
            team_name: Team name (alternative)
            stat_type: Type of statistics

        Returns:
            Team statistics or None
        """
        params = {}
        if stat_type:
            params["type"] = stat_type

        if team_id:
            endpoint = f"/api/v2/teams/{team_id}/stats"
        elif team_name:
            endpoint = "/api/v2/teams/stats/by-name"
            params["name"] = team_name
        else:
            return None

        try:
            return await self._get(endpoint, params=params)
        except Exception:
            return None

    async def get_team_season_stats(
        self,
        team_name: str,
        season_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get team season statistics

        Args:
            team_name: Team name
            season_id: Season ID

        Returns:
            Season statistics or None
        """
        params = {"name": team_name, "season_id": season_id}
        try:
            return await self._get("/api/v2/teams/stats/season", params=params)
        except Exception:
            return None

    # ============ Team Players Methods ============

    async def get_team_players(
        self,
        team_id: Optional[str] = None,
        team_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all players in a team (legacy TeamAPI.getTeamPlayers)

        Args:
            team_id: Team ID
            team_name: Team name (alternative)

        Returns:
            List of players
        """
        if team_id:
            endpoint = f"/api/v2/teams/{team_id}/players"
            params = {}
        elif team_name:
            endpoint = "/api/v2/teams/players/by-name"
            params = {"name": team_name}
        else:
            return []

        try:
            response = await self._get(endpoint, params=params)
            return response.get("players", [])
        except Exception:
            return []

    async def get_team_squad(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Get team squad with detailed player information

        Args:
            team_name: Team name

        Returns:
            List of squad players
        """
        params = {"name": team_name}
        try:
            response = await self._get("/api/v2/teams/squad", params=params)
            return response.get("squad", [])
        except Exception:
            return []

    # ============ Team Comparison Methods ============

    async def compare_teams(
        self,
        team1_name: str,
        team2_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Compare two teams (legacy TeamAPI.compareTeams)

        Args:
            team1_name: First team name
            team2_name: Second team name

        Returns:
            Comparison data or None
        """
        params = {"team1": team1_name, "team2": team2_name}
        try:
            return await self._get("/api/v2/teams/compare", params=params)
        except Exception:
            return None

    # ============ Team Matches Methods ============

    async def get_team_matches(
        self,
        team_id: Optional[str] = None,
        team_name: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get matches for a team

        Args:
            team_id: Team ID
            team_name: Team name (alternative)
            limit: Maximum results

        Returns:
            List of matches
        """
        params = {"limit": limit}

        if team_id:
            endpoint = f"/api/v2/teams/{team_id}/matches"
        elif team_name:
            endpoint = "/api/v2/teams/matches/by-name"
            params["name"] = team_name
        else:
            return []

        try:
            response = await self._get(endpoint, params=params)
            return response.get("matches", [])
        except Exception:
            return []

    async def get_team_fixtures(
        self,
        team_name: str,
        upcoming: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get team fixtures (upcoming or past)

        Args:
            team_name: Team name
            upcoming: True for upcoming, False for past

        Returns:
            List of fixtures
        """
        params = {"name": team_name, "upcoming": upcoming}
        try:
            response = await self._get("/api/v2/teams/fixtures", params=params)
            return response.get("fixtures", [])
        except Exception:
            return []

    # ============ Team Form and Rankings ============

    async def get_team_form(
        self,
        team_name: str,
        last_n_matches: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get team form (last N matches)

        Args:
            team_name: Team name
            last_n_matches: Number of recent matches

        Returns:
            Form data or None
        """
        params = {"name": team_name, "n": last_n_matches}
        try:
            return await self._get("/api/v2/teams/form", params=params)
        except Exception:
            return None

    async def get_league_standings(
        self,
        competition_id: int,
        season_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get league standings

        Args:
            competition_id: Competition ID
            season_id: Season ID

        Returns:
            List of teams with standings
        """
        params = {"competition_id": competition_id, "season_id": season_id}
        try:
            response = await self._get("/api/v2/teams/standings", params=params)
            return response.get("standings", [])
        except Exception:
            return []

    # ============ Team Events Methods ============

    async def get_team_events(
        self,
        team_id: str,
        event_type: Optional[str] = None,
        match_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get team events

        Args:
            team_id: Team ID
            event_type: Event type filter
            match_id: Match ID filter

        Returns:
            List of events
        """
        params = {}
        if event_type:
            params["type"] = event_type
        if match_id:
            params["match_id"] = match_id

        try:
            response = await self._get(f"/api/v2/teams/{team_id}/events", params=params)
            return response.get("events", [])
        except Exception:
            return []

    # ============ Bulk Operations ============

    async def get_all_teams(
        self,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all teams in competition/season

        Args:
            competition_id: Competition ID filter
            season_id: Season ID filter

        Returns:
            List of teams
        """
        params = {}
        if competition_id:
            params["competition_id"] = competition_id
        if season_id:
            params["season_id"] = season_id

        try:
            response = await self._get("/api/v2/teams/all", params=params)
            return response.get("teams", [])
        except Exception:
            return []
