from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from config.settings import Settings
from storage.task_store import TaskStore
from storage.file_store import FileStore
from worker.ml_task import MLTaskHandler
from worker.report_task import ReportTaskHandler
from worker.export_task import ExportTaskHandler
from worker.sync_task import SyncTaskHandler
from worker.statistics_task import StatisticsTaskHandler
from worker.video_task import VideoTaskHandler

logger = logging.getLogger(__name__)

TASK_HANDLERS = {
    "ml_predict": "ml",
    "ml_train": "ml",
    "report_generate": "report",
    "data_export": "export",
    "data_sync": "sync",
    "statistics_projection_rebuild": "statistics",
    "video_analysis": "video",
}


class TaskConsumer:
    def __init__(self, settings: Settings, task_store: TaskStore, file_store: FileStore):
        self._settings = settings
        self._task_store = task_store
        self._file_store = file_store
        self._consumer: AIOKafkaConsumer | None = None
        self._producer: AIOKafkaProducer | None = None
        self._handlers = self._build_handlers()
        self._consume_task: asyncio.Task | None = None
        self._inflight_tasks: set[asyncio.Task] = set()
        self._task_semaphore = asyncio.Semaphore(max(1, int(getattr(settings, "task_max_concurrency", 4))))

    def _build_handlers(self):
        s = self._settings
        return {
            "ml": MLTaskHandler(self._task_store, self._file_store, s.ml_service_url),
            "report": ReportTaskHandler(self._task_store, self._file_store, s.report_service_url),
            "export": ExportTaskHandler(
                self._task_store, self._file_store, s.export_service_url, s.statistics_service_url
            ),
            "sync": SyncTaskHandler(self._task_store, self._file_store, s.data_sync_service_url),
            "statistics": StatisticsTaskHandler(
                self._task_store, self._file_store, s.statistics_service_url
            ),
            "video": VideoTaskHandler(self._task_store, self._file_store, s.video_service_url),
        }

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            self._settings.kafka_tasks_topic,
            bootstrap_servers=self._settings.kafka_bootstrap_servers,
            group_id=self._settings.kafka_consumer_group,
            value_deserializer=lambda v: json.loads(v.decode()),
            auto_offset_reset="earliest",
        )
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        await self._consumer.start()
        await self._producer.start()
        logger.info("TaskConsumer started, listening on topic '%s'", self._settings.kafka_tasks_topic)
        self._consume_task = asyncio.create_task(self._consume_loop())

    async def stop(self) -> None:
        if self._consume_task:
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass

        if self._inflight_tasks:
            await asyncio.gather(*self._inflight_tasks, return_exceptions=True)

        if self._consumer:
            await self._consumer.stop()
        if self._producer:
            await self._producer.stop()

    def _track_inflight_task(self, task: asyncio.Task) -> None:
        self._inflight_tasks.add(task)
        task.add_done_callback(self._inflight_tasks.discard)

    async def _process_message(self, envelope: Dict[str, Any]) -> None:
        async with self._task_semaphore:
            task_id = envelope.get("task_id", "unknown")
            task_type = envelope.get("task_type", "")
            payload = envelope.get("payload", {})

            handler_key = TASK_HANDLERS.get(task_type)
            if not handler_key:
                logger.warning("Unknown task_type '%s' for task %s — skipping", task_type, task_id)
                return

            handler = self._handlers[handler_key]
            logger.info("Dispatching task %s (type=%s)", task_id, task_type)

            # Run handler; it updates task_store internally
            await handler.handle(task_id, payload)

            # Publish completion event so WebSocket bridge can notify frontend
            task = await self._task_store.get(task_id)
            if task and self._producer:
                await self._producer.send(
                    self._settings.kafka_task_completed_topic,
                    value={
                        "task_id": task_id,
                        "task_type": task_type,
                        "status": task["status"],
                        "result": task.get("result"),
                        "result_ref": task.get("result_ref"),
                        "error": task.get("error"),
                    },
                )

    async def _consume_loop(self) -> None:
        async for msg in self._consumer:
            envelope: Dict[str, Any] = msg.value
            task = asyncio.create_task(self._process_message(envelope))
            self._track_inflight_task(task)
