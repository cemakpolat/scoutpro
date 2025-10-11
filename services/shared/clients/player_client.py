"""
HTTP Client for Player Service
"""
from typing import Optional, Dict, Any, List
from .base_client import BaseServiceClient
import os


class PlayerServiceClient(BaseServiceClient):
    """
    Client for communicating with Player Service API
    Replaces direct PlayerAPI calls in microservices architecture
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Player Service client

        Args:
            base_url: Base URL of player service (default: from env or http://player-service:8000)
        """
        if base_url is None:
            base_url = os.getenv("PLAYER_SERVICE_URL", "http://player-service:8000")
        super().__init__(base_url)

    # ============ Player Data Methods ============

    async def get_player_by_id(self, player_id: str) -> Optional[Dict[str, Any]]:
        """
        Get player by ID

        Args:
            player_id: Player ID

        Returns:
            Player data or None
        """
        try:
            return await self._get(f"/api/v2/players/{player_id}")
        except Exception:
            return None

    async def search_players(
        self,
        query: Optional[str] = None,
        team_name: Optional[str] = None,
        position: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for players

        Args:
            query: Search query (player name)
            team_name: Filter by team name
            position: Filter by position
            limit: Maximum results

        Returns:
            List of players
        """
        params = {"limit": limit}
        if query:
            params["q"] = query
        if team_name:
            params["team"] = team_name
        if position:
            params["position"] = position

        try:
            response = await self._get("/api/v2/players", params=params)
            return response.get("players", [])
        except Exception:
            return []

    async def get_player_data(self, team_name: str, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Get player data by team and name (legacy PlayerAPI.getPlayerData)

        Args:
            team_name: Team name
            player_name: Player name

        Returns:
            Player data or None
        """
        params = {"team": team_name, "name": player_name}
        try:
            response = await self._get("/api/v2/players/by-name", params=params)
            return response
        except Exception:
            return None

    # ============ Player Statistics Methods ============

    async def get_player_statistics(
        self,
        player_id: Optional[str] = None,
        team_name: Optional[str] = None,
        player_name: Optional[str] = None,
        per_90: bool = False,
        stat_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get player statistics (legacy PlayerAPI.getPlayerStatistics)

        Args:
            player_id: Player ID
            team_name: Team name (alternative to player_id)
            player_name: Player name (alternative to player_id)
            per_90: Normalize to per 90 minutes
            stat_type: Type of statistics (e.g., "passing", "shooting")

        Returns:
            Player statistics or None
        """
        params = {"per_90": per_90}

        if player_id:
            endpoint = f"/api/v2/players/{player_id}/stats"
        elif team_name and player_name:
            endpoint = "/api/v2/players/stats/by-name"
            params["team"] = team_name
            params["name"] = player_name
        else:
            return None

        if stat_type:
            params["type"] = stat_type

        try:
            return await self._get(endpoint, params=params)
        except Exception:
            return None

    async def get_player_pass_events(
        self,
        team_name: str,
        player_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get player pass events (legacy PlayerAPI.getPlayerPassEvents)

        Args:
            team_name: Team name
            player_name: Player name

        Returns:
            List of pass events
        """
        params = {"team": team_name, "name": player_name}
        try:
            response = await self._get("/api/v2/players/events/passes", params=params)
            return response.get("passes", [])
        except Exception:
            return []

    async def get_player_shot_events(
        self,
        team_name: str,
        player_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get player shot events (legacy PlayerAPI.getPlayerShotEvents)

        Args:
            team_name: Team name
            player_name: Player name

        Returns:
            List of shot events
        """
        params = {"team": team_name, "name": player_name}
        try:
            response = await self._get("/api/v2/players/events/shots", params=params)
            return response.get("shots", [])
        except Exception:
            return []

    # ============ Player Comparison Methods ============

    async def compare_players(
        self,
        team1: str,
        player1: str,
        team2: str,
        player2: str
    ) -> Optional[Dict[str, Any]]:
        """
        Compare two players (legacy PlayerAPI.comparePlayers)

        Args:
            team1: First player's team
            player1: First player name
            team2: Second player's team
            player2: Second player name

        Returns:
            Comparison data or None
        """
        params = {
            "team1": team1,
            "player1": player1,
            "team2": team2,
            "player2": player2
        }
        try:
            return await self._get("/api/v2/players/compare", params=params)
        except Exception:
            return None

    # ============ Minutes Played Methods ============

    async def calculate_minutes_played(
        self,
        team_name: str,
        player_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate minutes played for a player (legacy PlayerAPI.calculateMinutesPlayed)

        Args:
            team_name: Team name
            player_name: Player name

        Returns:
            Minutes played data or None
        """
        params = {"team": team_name, "name": player_name}
        try:
            return await self._get("/api/v2/players/minutes", params=params)
        except Exception:
            return None

    # ============ Event-specific Methods ============

    async def get_player_events(
        self,
        player_id: str,
        event_type: Optional[str] = None,
        match_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get player events

        Args:
            player_id: Player ID
            event_type: Event type filter (e.g., "pass", "shot", "duel")
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
            response = await self._get(f"/api/v2/players/{player_id}/events", params=params)
            return response.get("events", [])
        except Exception:
            return []

    # ============ Bulk Operations ============

    async def get_players_by_team(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Get all players for a team

        Args:
            team_name: Team name

        Returns:
            List of players
        """
        params = {"team": team_name}
        try:
            response = await self._get("/api/v2/players/by-team", params=params)
            return response.get("players", [])
        except Exception:
            return []

    async def get_top_players(
        self,
        stat_name: str,
        limit: int = 10,
        position: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top players by statistic

        Args:
            stat_name: Statistic name (e.g., "goals", "assists")
            limit: Number of players
            position: Position filter

        Returns:
            List of top players
        """
        params = {"stat": stat_name, "limit": limit}
        if position:
            params["position"] = position

        try:
            response = await self._get("/api/v2/players/top", params=params)
            return response.get("players", [])
        except Exception:
            return []
