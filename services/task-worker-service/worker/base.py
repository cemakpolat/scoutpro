from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from storage.task_store import TaskStore
from storage.file_store import FileStore

logger = logging.getLogger(__name__)


class BaseTaskHandler(ABC):
    """Abstract handler. Subclasses implement `execute` and return a result dict."""

    def __init__(self, task_store: TaskStore, file_store: FileStore):
        self.task_store = task_store
        self.file_store = file_store

    async def handle(self, task_id: str, payload: Dict[str, Any]) -> None:
        await self.task_store.mark_running(task_id)
        try:
            result, result_ref = await self.execute(task_id, payload)
            await self.task_store.mark_completed(task_id, result=result, result_ref=result_ref)
        except Exception as exc:
            logger.exception("Task %s failed", task_id)
            await self.task_store.mark_failed(task_id, error=str(exc))

    @abstractmethod
    async def execute(self, task_id: str, payload: Dict[str, Any]):
        """Return (inline_result_or_None, result_ref_or_None)."""
