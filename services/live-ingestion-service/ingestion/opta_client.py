"""
Opta API Client for live data ingestion
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class OptaLiveClient:
    """Client for consuming Opta live match data"""

    def __init__(self, api_url: str, api_key: Optional[str] = None):
        self.api_url = api_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_live_matches(self) -> List[Dict[str, Any]]:
        """Get currently live matches"""
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = await self.client.get(
                f"{self.api_url}/live/matches",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()

            logger.warning(f"Failed to get live matches: {response.status_code}")
            return []

        except Exception as e:
            logger.error(f"Error getting live matches: {e}")
            return []

    async def get_match_events(self, match_id: str) -> List[Dict[str, Any]]:
        """Get live events for a match"""
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = await self.client.get(
                f"{self.api_url}/match/{match_id}/events",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()

            return []

        except Exception as e:
            logger.error(f"Error getting match events: {e}")
            return []

    async def get_match_stats(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get live statistics for a match"""
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = await self.client.get(
                f"{self.api_url}/match/{match_id}/stats",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()

            return None

        except Exception as e:
            logger.error(f"Error getting match stats: {e}")
            return None

    async def poll_live_data(self, match_id: str, callback, interval: int = 5):
        """Poll for live data updates"""
        logger.info(f"Starting to poll live data for match {match_id}")

        while True:
            try:
                # Get latest events
                events = await self.get_match_events(match_id)

                # Get latest stats
                stats = await self.get_match_stats(match_id)

                # Call callback with data
                if events or stats:
                    await callback({
                        'match_id': match_id,
                        'timestamp': datetime.utcnow().isoformat(),
                        'events': events,
                        'stats': stats
                    })

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error polling match {match_id}: {e}")
                await asyncio.sleep(interval)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
