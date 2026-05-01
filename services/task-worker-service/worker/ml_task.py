from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from .base import BaseTaskHandler

logger = logging.getLogger(__name__)

# Task payload schema:
# {
#   "algorithm": "player_clustering" | "goals_regression" | "advanced_player_similarity" | ...,
#   "action": "train" | "predict",
#   "data": [...],          # for train
#   "input_data": {...},    # for predict
# }


class MLTaskHandler(BaseTaskHandler):
    def __init__(self, task_store, file_store, ml_service_url: str):
        super().__init__(task_store, file_store)
        self._url = ml_service_url.rstrip("/")

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict]]:
        algorithm = payload["algorithm"]
        action = payload.get("action", "predict")

        async with httpx.AsyncClient(timeout=120.0) as client:
            if action == "train":
                await self.task_store.update_progress(task_id, 10, f"Training {algorithm}")
                resp = await client.post(
                    f"{self._url}/train/{algorithm}",
                    json={"data": payload["data"]},
                )
                resp.raise_for_status()
                result = resp.json()
            else:
                await self.task_store.update_progress(task_id, 10, f"Running {algorithm} prediction")
                resp = await client.post(
                    f"{self._url}/predict/{algorithm}",
                    json=payload.get("input_data", {}),
                )
                resp.raise_for_status()
                result = resp.json()

        await self.task_store.update_progress(task_id, 90, "Storing result")
        # Inline result (small) — no MinIO needed for ML outputs
        return result, None
