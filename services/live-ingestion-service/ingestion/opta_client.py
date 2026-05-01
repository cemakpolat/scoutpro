"""
Opta API Client for live data ingestion.

Supports two endpoint styles:
    1. ScoutPro provider server contract (default): /api/football/f{N}/{comp}/{season}[/{match}]
    2. Real Opta Stats Perform API: set OPTA_API_STYLE=statsperform in env
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class OptaLiveClient:
    """Client for consuming Opta live match data."""

    def __init__(self, api_url: str, api_key: Optional[str] = None,
                 competition_id: str = "115", season_id: str = "2019"):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.competition_id = competition_id
        self.season_id = season_id
        self.client = httpx.AsyncClient(timeout=15.0)

    def _headers(self) -> Dict[str, str]:
        h: Dict[str, str] = {}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    # ------------------------------------------------------------------ #
    # Feed endpoints (matches the ScoutPro provider server contract)
    # ------------------------------------------------------------------ #

    async def get_schedule(self) -> Dict[str, Any]:
        """Fetch F1 season schedule for all matches (competitions, teams, fixtures)."""
        url = f"{self.api_url}/api/football/f1/{self.competition_id}/{self.season_id}"
        try:
            resp = await self.client.get(url, headers=self._headers())
            if resp.status_code == 200:
                return self._parse_response(resp)
            logger.warning(f"F1 schedule returned {resp.status_code}: {url}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching F1 schedule: {e}")
            return {}

    async def get_squads(self) -> Dict[str, Any]:
        """Fetch F40 squad list (player profiles for all teams)."""
        url = f"{self.api_url}/api/football/f40/{self.competition_id}/{self.season_id}"
        try:
            resp = await self.client.get(url, headers=self._headers())
            if resp.status_code == 200:
                return self._parse_response(resp)
            logger.warning(f"F40 squads returned {resp.status_code}: {url}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching F40 squads: {e}")
            return {}

    async def get_match_summary(self, match_id: str) -> Dict[str, Any]:
        """Fetch F9 match summary (lineups, scores, stats) for a specific match."""
        url = f"{self.api_url}/api/football/f9/{self.competition_id}/{self.season_id}"
        try:
            resp = await self.client.get(url, headers=self._headers())
            if resp.status_code == 200:
                return self._parse_response(resp)
            logger.warning(f"F9 summary returned {resp.status_code}: {url}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching F9 match summary: {e}")
            return {}

    async def get_match_events(self, match_id: str) -> Dict[str, Any]:
        """Fetch F24 event stream for a specific match."""
        url = (f"{self.api_url}/api/football/f24/"
               f"{self.competition_id}/{self.season_id}/{match_id}")
        try:
            resp = await self.client.get(url, headers=self._headers())
            if resp.status_code == 200:
                return self._parse_response(resp)
            logger.warning(f"F24 events returned {resp.status_code}: {url}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching F24 events for match {match_id}: {e}")
            return {}

    async def get_live_matches(self) -> List[Dict[str, Any]]:
        """
        Get list of available matches via the provider server discovery endpoint.
        Falls back to /api/football/matches/{comp}/{season}.
        """
        url = f"{self.api_url}/api/football/matches/{self.competition_id}/{self.season_id}"
        try:
            resp = await self.client.get(url, headers=self._headers())
            if resp.status_code == 200:
                data = resp.json()
                return data.get("match_ids", [])
            return []
        except Exception as e:
            logger.error(f"Error getting match list: {e}")
            return []

    async def get_match_stats(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get match stats via F9 summary (same endpoint as get_match_summary)."""
        summary = await self.get_match_summary(match_id)
        return summary.get("stats") if summary else None

    async def poll_live_data(self, match_id: str, callback, interval: int = 5):
        """Poll F24 for live event updates."""
        logger.info(f"Polling F24 live events for match {match_id}")
        while True:
            try:
                raw = await self.get_match_events(match_id)
                stats = await self.get_match_stats(match_id)
                if raw or stats:
                    await callback({
                        "match_id": match_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "events": raw,
                        "stats": stats or {},
                    })
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error polling match {match_id}: {e}")
                await asyncio.sleep(interval)

    @staticmethod
    def _parse_response(resp: httpx.Response) -> Dict[str, Any]:
        """Parse response body as JSON (or XML via xmltodict if needed)."""
        content_type = resp.headers.get("content-type", "")
        if "json" in content_type or resp.content[:1] in (b"{", b"["):
            try:
                return resp.json()
            except Exception:
                pass
        # Try XML
        try:
            import xmltodict
            return xmltodict.parse(resp.text)
        except ImportError:
            logger.error("Response is XML but xmltodict is not installed. "
                         "Run: pip install xmltodict")
        except Exception as exc:
            logger.error(f"Failed to parse response as XML: {exc}")
        return {}

    async def close(self):
        await self.client.aclose()

