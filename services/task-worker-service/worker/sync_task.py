from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from .base import BaseTaskHandler

logger = logging.getLogger(__name__)

# Task payload schema:
# {
#   "provider": "statsbomb" | "opta" | "all",
#   "competition_id": 11,     # optional
#   "season_id": 90,          # optional
# }


class SyncTaskHandler(BaseTaskHandler):
    def __init__(self, task_store, file_store, data_sync_service_url: str):
        super().__init__(task_store, file_store)
        self._url = data_sync_service_url.rstrip("/")

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict]]:
        provider = payload.get("provider", "all")

        await self.task_store.update_progress(task_id, 5, f"Triggering {provider} sync")

        async with httpx.AsyncClient(timeout=600.0) as client:
            resp = await client.post(
                f"{self._url}/sync/trigger",
                json={
                    "provider": provider,
                    "competition_id": payload.get("competition_id"),
                    "season_id": payload.get("season_id"),
                },
            )
            resp.raise_for_status()
            result = resp.json()

        return result, None
