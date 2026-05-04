from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from .base import BaseTaskHandler

logger = logging.getLogger(__name__)


class StatisticsTaskHandler(BaseTaskHandler):
    def __init__(self, task_store, file_store, statistics_service_url: str):
        super().__init__(task_store, file_store)
        self._url = statistics_service_url.rstrip("/")

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict]]:
        match_id = payload.get("match_id")
        competition_id = payload.get("competition_id")
        season_id = payload.get("season_id")

        target = match_id or competition_id or season_id or "all matches"
        await self.task_store.update_progress(task_id, 10, f"Rebuilding projections for {target}")

        async with httpx.AsyncClient(timeout=600.0) as client:
            resp = await client.post(
                f"{self._url}/api/v2/statistics/projections/rebuild",
                json={
                    "match_id": match_id,
                    "competition_id": competition_id,
                    "season_id": season_id,
                },
            )
            resp.raise_for_status()
            result = resp.json()

        await self.task_store.update_progress(task_id, 90, "Projection rebuild completed")
        return result, None