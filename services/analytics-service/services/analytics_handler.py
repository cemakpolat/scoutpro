import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalyticsHandler:
    def __init__(self):
        self.player_service_url = "http://player-service:8000"
        self.team_service_url = "http://team-service:8000"
        self.match_service_url = "http://match-service:8000" 
        self.statistics_service_url = "http://statistics-service:8000"
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_overview(self, season: Optional[str] = None) -> Dict[str, Any]:
        try:
            # For overview, try aggregating counts from different services
            # This is a sample approach:
            players_resp = await self.client.get(f"{self.player_service_url}/api/v2/players?limit=1")
            matches_resp = await self.client.get(f"{self.match_service_url}/api/v2/matches?limit=1")
            teams_resp = await self.client.get(f"{self.team_service_url}/api/v2/teams?limit=1")

            total_players = players_resp.json().get("total", 0) if players_resp.status_code == 200 else 0
            total_matches = matches_resp.json().get("total", 0) if matches_resp.status_code == 200 else 0
            total_teams = teams_resp.json().get("total", 0) if teams_resp.status_code == 200 else 0

            return {
                "title": "Overview Dashboard",
                "data": {
                    "total_players": total_players,
                    "total_teams": total_teams,
                    "total_matches": total_matches,
                    "avg_goals_per_match": "N/A (Real computing pending)"
                },
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching overview: {e}")
            raise

    async def get_team_dashboard(self, team_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        try:
            team_resp = await self.client.get(f"{self.team_service_url}/api/v2/teams/{team_id}")
            stats_resp = await self.client.get(f"{self.statistics_service_url}/api/v2/statistics/team/{team_id}")
            
            team_data = team_resp.json() if team_resp.status_code == 200 else {}
            stats_data = stats_resp.json() if stats_resp.status_code == 200 else {}

            return {
                "team_id": team_id,
                "season": season or "2023-2024",
                "metrics": stats_data.get("metrics", {}),
                "trends": stats_data.get("trends", {})
            }
        except Exception as e:
            logger.error(f"Error fetching team dashboard: {e}")
            raise

    async def get_player_dashboard(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        try:
            player_resp = await self.client.get(f"{self.player_service_url}/api/v2/players/{player_id}")
            stats_resp = await self.client.get(f"{self.statistics_service_url}/api/v2/statistics/player/{player_id}")

            player_data = player_resp.json() if player_resp.status_code == 200 else {}
            stats_data = stats_resp.json() if stats_resp.status_code == 200 else {}

            return {
                "player_id": player_id,
                "season": season or "2023-2024",
                "performance": stats_data.get("performance", {}),
                "trends": stats_data.get("trends", {})
            }
        except Exception as e:
            logger.error(f"Error fetching player dashboard: {e}")
            raise
            
    async def get_team_rankings(self, competition: str, metric: str, limit: int) -> Dict[str, Any]:
        try:
            response = await self.client.get(
                f"{self.statistics_service_url}/api/v2/rankings/teams",
                params={"competition": competition, "metric": metric, "limit": limit}
            )
            return response.json() if response.status_code == 200 else {"error": "Failed to fetch rankings"}
        except Exception as e:
            logger.error(f"Error fetching team rankings: {e}")
            return {"error": "Service unavailable"}
            
    async def get_player_rankings(self, metric: str, position: Optional[str], limit: int) -> Dict[str, Any]:
        try:
            params = {"metric": metric, "limit": limit}
            if position:
                params["position"] = position
            response = await self.client.get(f"{self.statistics_service_url}/api/v2/rankings/players", params=params)
            return response.json() if response.status_code == 200 else {"error": "Failed to fetch rankings"}
        except Exception as e:
            logger.error(f"Error fetching player rankings: {e}")
            return {"error": "Service unavailable"}

    async def close(self):
        await self.client.aclose()

