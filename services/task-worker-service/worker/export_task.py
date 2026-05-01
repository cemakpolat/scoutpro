from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .base import BaseTaskHandler

logger = logging.getLogger(__name__)

# Task payload schema:
# {
#   "export_type": "players" | "matches" | "events" | "statistics",
#   "filters": {...},         # forwarded to export-service or statistics-service
#   "format": "csv" | "json",
#   "player_ids": [...],      # optional subset
# }


class ExportTaskHandler(BaseTaskHandler):
    def __init__(self, task_store, file_store, export_service_url: str, statistics_service_url: str):
        super().__init__(task_store, file_store)
        self._export_url = export_service_url.rstrip("/")
        self._stats_url = statistics_service_url.rstrip("/")

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict]]:
        export_type = payload["export_type"]
        fmt = payload.get("format", "csv")

        await self.task_store.update_progress(task_id, 10, f"Fetching {export_type} data")

        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{self._export_url}/export/{export_type}",
                json={"format": fmt, **payload.get("filters", {})},
            )
            resp.raise_for_status()
            rows: List[Dict] = resp.json()

        await self.task_store.update_progress(task_id, 60, f"Serializing {len(rows)} rows")

        if fmt == "csv":
            file_bytes, content_type = self._to_csv(rows), "text/csv"
            ext = "csv"
        else:
            file_bytes = json.dumps(rows).encode()
            content_type = "application/json"
            ext = "json"

        await self.task_store.update_progress(task_id, 80, "Uploading to storage")
        key = f"exports/{task_id}/{export_type}.{ext}"
        result_ref = self.file_store.upload_bytes(key, file_bytes, content_type=content_type)
        url = self.file_store.presigned_url(key, expires_seconds=86400)

        return {"download_url": url, "row_count": len(rows), "format": fmt}, result_ref

    @staticmethod
    def _to_csv(rows: List[Dict]) -> bytes:
        if not rows:
            return b""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue().encode()
