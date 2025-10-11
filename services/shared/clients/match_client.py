"""
HTTP Client for Match Service (GameAPI + EventAPI)
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base_client import BaseServiceClient
import os


class MatchServiceClient(BaseServiceClient):
    """
    Client for communicating with Match Service API
    Replaces direct GameAPI and EventAPI calls in microservices architecture
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Match Service client

        Args:
            base_url: Base URL of match service (default: from env or http://match-service:8000)
        """
        if base_url is None:
            base_url = os.getenv("MATCH_SERVICE_URL", "http://match-service:8000")
        super().__init__(base_url)

    # ============ Match Data Methods (GameAPI) ============

    async def get_match_by_id(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match by ID (legacy GameAPI.getGameDataById)

        Args:
            match_id: Match ID

        Returns:
            Match data or None
        """
        try:
            return await self._get(f"/api/v2/matches/{match_id}")
        except Exception:
            return None

    async def get_game_data(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive game data (legacy GameAPI.getGameData)

        Args:
            match_id: Match ID

        Returns:
            Game data or None
        """
        return await self.get_match_by_id(match_id)

    async def get_all_matches(
        self,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all matches (legacy GameAPI.getAllMatches)

        Args:
            competition_id: Competition ID filter
            season_id: Season ID filter
            limit: Maximum results

        Returns:
            List of matches
        """
        params = {"limit": limit}
        if competition_id:
            params["competition_id"] = competition_id
        if season_id:
            params["season_id"] = season_id

        try:
            response = await self._get("/api/v2/matches", params=params)
            return response.get("matches", [])
        except Exception:
            return []

    async def search_matches(
        self,
        team_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for matches

        Args:
            team_id: Filter by team
            start_date: Start date filter
            end_date: End date filter
            status: Match status (e.g., "completed", "live", "scheduled")
            limit: Maximum results

        Returns:
            List of matches
        """
        params = {"limit": limit}
        if team_id:
            params["team_id"] = team_id
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        if status:
            params["status"] = status

        try:
            response = await self._get("/api/v2/matches/search", params=params)
            return response.get("matches", [])
        except Exception:
            return []

    # ============ Match Statistics Methods ============

    async def get_match_statistics(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match statistics

        Args:
            match_id: Match ID

        Returns:
            Match statistics or None
        """
        try:
            return await self._get(f"/api/v2/matches/{match_id}/stats")
        except Exception:
            return None

    async def get_match_summary(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match summary

        Args:
            match_id: Match ID

        Returns:
            Match summary or None
        """
        try:
            return await self._get(f"/api/v2/matches/{match_id}/summary")
        except Exception:
            return None

    # ============ Live Match Methods ============

    async def get_live_matches(self) -> List[Dict[str, Any]]:
        """
        Get currently live matches

        Returns:
            List of live matches
        """
        try:
            response = await self._get("/api/v2/matches/live")
            return response.get("matches", [])
        except Exception:
            return []

    async def get_match_live_data(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get live match data

        Args:
            match_id: Match ID

        Returns:
            Live data or None
        """
        try:
            return await self._get(f"/api/v2/matches/{match_id}/live")
        except Exception:
            return None

    # ============ Match Events Methods (EventAPI) ============

    async def get_match_events(
        self,
        match_id: str,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all events for a match (legacy EventAPI.getMatchEvents)

        Args:
            match_id: Match ID
            event_type: Event type filter (e.g., "pass", "shot", "foul")

        Returns:
            List of events
        """
        params = {}
        if event_type:
            params["type"] = event_type

        try:
            response = await self._get(f"/api/v2/matches/{match_id}/events", params=params)
            return response.get("events", [])
        except Exception:
            return []

    async def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific event by ID (legacy EventAPI.getEventById)

        Args:
            event_id: Event ID

        Returns:
            Event data or None
        """
        try:
            return await self._get(f"/api/v2/events/{event_id}")
        except Exception:
            return None

    async def get_filtered_events(
        self,
        match_id: str,
        event_type: Optional[str] = None,
        team_id: Optional[str] = None,
        player_id: Optional[str] = None,
        period: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get filtered match events

        Args:
            match_id: Match ID
            event_type: Event type filter
            team_id: Team ID filter
            player_id: Player ID filter
            period: Match period filter (1 or 2)

        Returns:
            List of filtered events
        """
        params = {}
        if event_type:
            params["type"] = event_type
        if team_id:
            params["team_id"] = team_id
        if player_id:
            params["player_id"] = player_id
        if period:
            params["period"] = period

        try:
            response = await self._get(f"/api/v2/matches/{match_id}/events/filter", params=params)
            return response.get("events", [])
        except Exception:
            return []

    # ============ Specific Event Types ============

    async def get_match_pass_events(self, match_id: str) -> List[Dict[str, Any]]:
        """
        Get all pass events for a match

        Args:
            match_id: Match ID

        Returns:
            List of pass events
        """
        return await self.get_match_events(match_id, event_type="pass")

    async def get_match_shot_events(self, match_id: str) -> List[Dict[str, Any]]:
        """
        Get all shot events for a match

        Args:
            match_id: Match ID

        Returns:
            List of shot events
        """
        return await self.get_match_events(match_id, event_type="shot")

    async def get_match_goal_events(self, match_id: str) -> List[Dict[str, Any]]:
        """
        Get all goal events for a match

        Args:
            match_id: Match ID

        Returns:
            List of goal events
        """
        return await self.get_match_events(match_id, event_type="goal")

    async def get_match_foul_events(self, match_id: str) -> List[Dict[str, Any]]:
        """
        Get all foul events for a match

        Args:
            match_id: Match ID

        Returns:
            List of foul events
        """
        return await self.get_match_events(match_id, event_type="foul")

    async def get_match_card_events(self, match_id: str) -> List[Dict[str, Any]]:
        """
        Get all card events for a match

        Args:
            match_id: Match ID

        Returns:
            List of card events
        """
        return await self.get_match_events(match_id, event_type="card")

    # ============ Team-specific Match Data ============

    async def get_team_matches(
        self,
        team_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get matches for a team

        Args:
            team_id: Team ID
            limit: Maximum results

        Returns:
            List of matches
        """
        params = {"team_id": team_id, "limit": limit}
        try:
            response = await self._get("/api/v2/matches/by-team", params=params)
            return response.get("matches", [])
        except Exception:
            return []

    async def get_team_match_events(
        self,
        match_id: str,
        team_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get events for a specific team in a match

        Args:
            match_id: Match ID
            team_id: Team ID

        Returns:
            List of team events
        """
        return await self.get_filtered_events(match_id, team_id=team_id)

    # ============ Player-specific Match Data ============

    async def get_player_match_events(
        self,
        match_id: str,
        player_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get events for a specific player in a match

        Args:
            match_id: Match ID
            player_id: Player ID

        Returns:
            List of player events
        """
        return await self.get_filtered_events(match_id, player_id=player_id)

    async def get_player_match_statistics(
        self,
        match_id: str,
        player_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get player statistics for a specific match

        Args:
            match_id: Match ID
            player_id: Player ID

        Returns:
            Player match stats or None
        """
        try:
            return await self._get(f"/api/v2/matches/{match_id}/players/{player_id}/stats")
        except Exception:
            return None

    # ============ Date Range Queries ============

    async def get_matches_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get matches in date range

        Args:
            start_date: Start date
            end_date: End date
            limit: Maximum results

        Returns:
            List of matches
        """
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "limit": limit
        }
        try:
            response = await self._get("/api/v2/matches/date-range", params=params)
            return response.get("matches", [])
        except Exception:
            return []

    # ============ Season Data ============

    async def get_season_matches(
        self,
        competition_id: int,
        season_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all matches for a season

        Args:
            competition_id: Competition ID
            season_id: Season ID

        Returns:
            List of matches
        """
        params = {"competition_id": competition_id, "season_id": season_id}
        try:
            response = await self._get("/api/v2/matches/season", params=params)
            return response.get("matches", [])
        except Exception:
            return []

    async def get_all_season_game_events(
        self,
        team_id: str,
        player_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all game events for a season (legacy GameAPI.getAllSeasonGameEvents)

        Args:
            team_id: Team ID
            player_id: Player ID filter (optional)

        Returns:
            List of events
        """
        params = {"team_id": team_id}
        if player_id:
            params["player_id"] = player_id

        try:
            response = await self._get("/api/v2/matches/season/events", params=params)
            return response.get("events", [])
        except Exception:
            return []
