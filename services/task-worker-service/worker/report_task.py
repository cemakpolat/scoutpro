from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from .base import BaseTaskHandler

logger = logging.getLogger(__name__)

# Task payload schema:
# {
#   "report_type": "player" | "team" | "match",
#   "entity_id": "...",
#   "format": "pdf",          # default pdf
#   "options": {...},         # optional extra params forwarded to report-service
# }


class ReportTaskHandler(BaseTaskHandler):
    def __init__(self, task_store, file_store, report_service_url: str):
        super().__init__(task_store, file_store)
        self._url = report_service_url.rstrip("/")

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict]]:
        report_type = payload["report_type"]
        entity_id = payload["entity_id"]
        fmt = payload.get("format", "pdf")

        await self.task_store.update_progress(task_id, 10, f"Generating {report_type} report")

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{self._url}/reports/{report_type}",
                json={"entity_id": entity_id, "format": fmt, **payload.get("options", {})},
            )
            resp.raise_for_status()
            file_bytes = resp.content

        await self.task_store.update_progress(task_id, 80, "Uploading report to storage")
        key = f"reports/{task_id}/{report_type}_{entity_id}.{fmt}"
        content_type = "application/pdf" if fmt == "pdf" else "application/octet-stream"
        result_ref = self.file_store.upload_bytes(key, file_bytes, content_type=content_type)

        url = self.file_store.presigned_url(key, expires_seconds=86400)
        return {"download_url": url, "key": key}, result_ref
