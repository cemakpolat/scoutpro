"""
Task Store — MongoDB-backed task lifecycle management.

Schema (tasks collection):
  task_id        : str (UUID, primary key)
  type           : str  (ml_predict | report_generate | data_export | data_sync | video_analysis)
  status         : str  (pending | running | completed | failed)
  payload        : dict (task-specific input)
  result         : dict | None  (inline result for small payloads)
  result_ref     : dict | None  ({ storage, bucket, key } for large files in MinIO)
  error          : str | None
  created_at     : datetime
  started_at     : datetime | None
  completed_at   : datetime | None
  progress       : int   (0-100)
  progress_msg   : str
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

COLLECTION = "tasks"


class TaskStore:
    def __init__(self, mongodb_url: str, database: str):
        self._client = AsyncIOMotorClient(mongodb_url)
        self._db = self._client[database]
        self._col = self._db[COLLECTION]

    async def ensure_indexes(self) -> None:
        await self._col.create_index("task_id", unique=True)
        await self._col.create_index("status")
        await self._col.create_index("created_at")

    async def create(self, task_id: str, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        doc = {
            "task_id": task_id,
            "type": task_type,
            "status": "pending",
            "payload": payload,
            "result": None,
            "result_ref": None,
            "error": None,
            "created_at": datetime.now(timezone.utc),
            "started_at": None,
            "completed_at": None,
            "progress": 0,
            "progress_msg": "Queued",
        }
        await self._col.insert_one(doc)
        doc.pop("_id", None)
        return _serialize(doc)

    async def mark_running(self, task_id: str, progress_msg: str = "Running") -> None:
        await self._col.update_one(
            {"task_id": task_id},
            {"$set": {
                "status": "running",
                "started_at": datetime.now(timezone.utc),
                "progress": 5,
                "progress_msg": progress_msg,
            }},
        )

    async def update_progress(self, task_id: str, progress: int, msg: str) -> None:
        await self._col.update_one(
            {"task_id": task_id},
            {"$set": {"progress": progress, "progress_msg": msg}},
        )

    async def mark_completed(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        result_ref: Optional[Dict[str, Any]] = None,
    ) -> None:
        await self._col.update_one(
            {"task_id": task_id},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc),
                "progress": 100,
                "progress_msg": "Done",
                "result": result,
                "result_ref": result_ref,
            }},
        )

    async def mark_failed(self, task_id: str, error: str) -> None:
        await self._col.update_one(
            {"task_id": task_id},
            {"$set": {
                "status": "failed",
                "completed_at": datetime.now(timezone.utc),
                "error": error,
                "progress_msg": "Failed",
            }},
        )

    async def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        doc = await self._col.find_one({"task_id": task_id}, {"_id": 0})
        return _serialize(doc) if doc else None

    async def list_recent(self, limit: int = 50) -> list[Dict[str, Any]]:
        cursor = self._col.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return [_serialize(d) async for d in cursor]

    async def close(self) -> None:
        self._client.close()


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime fields to ISO strings for JSON compatibility."""
    for key in ("created_at", "started_at", "completed_at"):
        if doc.get(key) and hasattr(doc[key], "isoformat"):
            doc[key] = doc[key].isoformat()
    return doc
