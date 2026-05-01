from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from .base import BaseTaskHandler

logger = logging.getLogger(__name__)

# Task payload schema:
# {
#   "video_id": "...",
#   "analysis_type": "highlight" | "heatmap" | "full",
#   "player_ids": [...],      # optional
#   "match_id": "...",        # optional
# }


class VideoTaskHandler(BaseTaskHandler):
    def __init__(self, task_store, file_store, video_service_url: str):
        super().__init__(task_store, file_store)
        self._url = video_service_url.rstrip("/")

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict]]:
        video_id = payload["video_id"]
        analysis_type = payload.get("analysis_type", "highlight")

        await self.task_store.update_progress(task_id, 5, f"Submitting video {video_id} for {analysis_type} analysis")

        async with httpx.AsyncClient(timeout=600.0) as client:
            resp = await client.post(
                f"{self._url}/analyze",
                json={
                    "video_id": video_id,
                    "analysis_type": analysis_type,
                    "player_ids": payload.get("player_ids", []),
                    "match_id": payload.get("match_id"),
                },
            )
            resp.raise_for_status()
            analysis_result = resp.json()

        await self.task_store.update_progress(task_id, 70, "Storing analysis output")

        # Store full analysis JSON in MinIO; return presigned URL
        key = f"video-analysis/{task_id}/{video_id}_{analysis_type}.json"
        result_ref = self.file_store.upload_json(key, analysis_result)
        url = self.file_store.presigned_url(key, expires_seconds=86400)

        return {"download_url": url, "analysis_type": analysis_type, "video_id": video_id}, result_ref
