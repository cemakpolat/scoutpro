from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import Settings
from consumer.task_consumer import TaskConsumer
from storage.task_store import TaskStore
from storage.file_store import FileStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()

_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://api-gateway:3001,http://localhost:3001,http://localhost:5173,http://localhost:5174",
    ).split(",")
    if o.strip()
]

task_store: TaskStore | None = None
file_store: FileStore | None = None
consumer: TaskConsumer | None = None
producer: AIOKafkaProducer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global task_store, file_store, consumer, producer

    task_store = TaskStore(settings.mongodb_url, database="scoutpro")
    await task_store.ensure_indexes()

    file_store = FileStore(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_tasks_bucket,
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: __import__("json").dumps(v).encode(),
    )
    await producer.start()

    consumer = TaskConsumer(settings, task_store, file_store)
    await consumer.start()

    logger.info("task-worker-service ready")
    yield

    if consumer:
        await consumer.stop()
    if producer:
        await producer.stop()
    if task_store:
        await task_store.close()
    logger.info("task-worker-service shut down")


app = FastAPI(title="ScoutPro Task Worker Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ──────────────────────────────────────────────────

class SubmitTaskRequest(BaseModel):
    task_type: str      # ml_predict | ml_train | report_generate | data_export | data_sync | video_analysis
    payload: Dict[str, Any]


class TaskResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    progress: int
    progress_msg: str
    result: Optional[Any] = None
    result_ref: Optional[Dict] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "task-worker-service"}


@app.post("/tasks", response_model=TaskResponse, status_code=202)
async def submit_task(req: SubmitTaskRequest):
    task_id = str(uuid.uuid4())
    task = await task_store.create(task_id, req.task_type, req.payload)

    envelope = {"task_id": task_id, "task_type": req.task_type, "payload": req.payload}
    await producer.send(settings.kafka_tasks_topic, value=envelope)

    return TaskResponse(**task)


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    task = await task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task)


@app.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    task = await task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "completed":
        return {"task_id": task_id, "status": task["status"], "result": None}

    result_ref = task.get("result_ref")
    if result_ref and result_ref.get("storage") == "minio":
        url = file_store.presigned_url(result_ref["key"], expires_seconds=3600)
        return {"task_id": task_id, "status": "completed", "download_url": url, "result": task.get("result")}

    return {"task_id": task_id, "status": "completed", "result": task.get("result")}


@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(limit: int = 50):
    tasks = await task_store.list_recent(limit=limit)
    return [TaskResponse(**t) for t in tasks]
