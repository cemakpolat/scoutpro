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
from worker.video_task import VideoTaskHandler

logger = logging.getLogger(__name__)

TASK_HANDLERS = {
    "ml_predict": "ml",
    "ml_train": "ml",
    "report_generate": "report",
    "data_export": "export",
    "data_sync": "sync",
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

    def _build_handlers(self):
        s = self._settings
        return {
            "ml": MLTaskHandler(self._task_store, self._file_store, s.ml_service_url),
            "report": ReportTaskHandler(self._task_store, self._file_store, s.report_service_url),
            "export": ExportTaskHandler(
                self._task_store, self._file_store, s.export_service_url, s.statistics_service_url
            ),
            "sync": SyncTaskHandler(self._task_store, self._file_store, s.data_sync_service_url),
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
        asyncio.create_task(self._consume_loop())

    async def stop(self) -> None:
        if self._consumer:
            await self._consumer.stop()
        if self._producer:
            await self._producer.stop()

    async def _consume_loop(self) -> None:
        async for msg in self._consumer:
            envelope: Dict[str, Any] = msg.value
            task_id = envelope.get("task_id", "unknown")
            task_type = envelope.get("task_type", "")
            payload = envelope.get("payload", {})

            handler_key = TASK_HANDLERS.get(task_type)
            if not handler_key:
                logger.warning("Unknown task_type '%s' for task %s — skipping", task_type, task_id)
                continue

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
