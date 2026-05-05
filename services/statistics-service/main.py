"""
Statistics Service - Main Application
"""
import asyncio
import os
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import sys
sys.path.append('/app')
from shared.utils.logger import setup_logger
from config.settings import get_settings
from api.statistics import router as statistics_router
from api.events import router as events_router
from api.events_enhanced import router as events_enhanced_router
from dependencies import (
    get_database_manager,
    kafka_producer,
    db_manager
)
from services.stream_handler import StatisticsStreamProcessor

# ---------------------------------------------------------------------------
# Periodic aggregation scheduler
# ---------------------------------------------------------------------------
_scheduler = None


def _scheduler_run_pipeline():
    """Called by APScheduler in a background thread to run the stats pipeline."""
    from services.event_stats_pipeline import EventStatsPipeline
    logger_s = logging.getLogger("scheduler.pipeline")
    logger_s.info("Periodic EventStatsPipeline run started")
    pipeline = EventStatsPipeline()
    try:
        result = pipeline.run()
        logger_s.info("Periodic pipeline complete: %s", result)
    except Exception as exc:
        logger_s.error("Periodic pipeline failed: %s", exc, exc_info=True)
    finally:
        pipeline.close()


def _start_scheduler():
    """Start APScheduler with a configurable interval."""
    global _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        interval_hours = int(os.getenv("STATS_AGGREGATE_INTERVAL_HOURS", "24"))
        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(
            _scheduler_run_pipeline,
            "interval",
            hours=interval_hours,
            id="event_stats_pipeline",
            replace_existing=True,
        )
        _scheduler.start()
        logger.info(
            "APScheduler started: EventStatsPipeline will run every %d hour(s)",
            interval_hours,
        )
    except ImportError:
        logger.warning(
            "apscheduler not installed — periodic stats aggregation disabled. "
            "Install with: pip install apscheduler"
        )
    except Exception as exc:
        logger.error("Failed to start scheduler: %s", exc)


settings = get_settings()
logger = setup_logger(settings.service_name, settings.log_level)
stream_processor = None
stream_processor_task = None
APP_VERSION = "2.0.0"

OPENAPI_TAGS = [
    {
        "name": "statistics",
        "description": "Persistent player, team, and match projection endpoints owned by statistics-service.",
    },
    {
        "name": "events",
        "description": "Event-derived analytics endpoints built from normalized match_events.",
    },
    {
        "name": "system",
        "description": "Service health and metadata endpoints.",
    },
]

_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://api-gateway:3001,http://localhost:3001,http://localhost:5173,http://localhost:5174",
    ).split(",")
    if o.strip()
]


def _handle_stream_processor_exit(task: asyncio.Task) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        logger.info("Statistics Stream Processor task cancelled")
    except Exception as exc:
        logger.error(f"Statistics Stream Processor stopped unexpectedly: {exc}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global stream_processor, stream_processor_task
    logger.info(f"Starting {settings.service_name}")

    try:
        manager = await get_database_manager()

        logger.info("Connecting to MongoDB...")
        await manager.connect_mongodb(settings.mongodb_url, settings.mongodb_database)
        logger.info("MongoDB connected")

        logger.info("Connecting to Redis...")
        await manager.connect_redis(settings.redis_url)
        logger.info("Redis connected")

        try:
            logger.info("Starting Statistics Stream Processor...")
            stream_processor = StatisticsStreamProcessor()
            stream_processor_task = asyncio.create_task(stream_processor.start())
            stream_processor_task.add_done_callback(_handle_stream_processor_exit)
            logger.info("Statistics Stream Processor started")
        except Exception as e:
            logger.error(f"Failed to start stream processor: {e}")

        # Start periodic scheduler
        _start_scheduler()

        # On startup, run pipeline once in background if player_statistics is empty
        # or has fewer docs than match_events to catch up from seeding
        async def _bootstrap_pipeline():
            try:
                from motor.motor_asyncio import AsyncIOMotorClient
                mongo_url = settings.mongodb_url
                db_name = settings.mongodb_database
                client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=3000)
                db = client[db_name]
                ps_count = await db.player_statistics.count_documents({})
                events_count = await db.match_events.count_documents({})
                client.close()

                if events_count > 0 and ps_count == 0:
                    logger.info(
                        "player_statistics is empty but %d match_events exist — "
                        "running initial EventStatsPipeline bootstrap in background",
                        events_count,
                    )
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, _scheduler_run_pipeline)
                else:
                    logger.info(
                        "player_statistics has %d docs — skipping bootstrap run",
                        ps_count,
                    )
            except Exception as exc:
                logger.warning("Bootstrap pipeline check failed: %s", exc)

        asyncio.create_task(_bootstrap_pipeline())

        logger.info(f"{settings.service_name} started successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")

    yield

    logger.info(f"Shutting down {settings.service_name}")
    try:
        if _scheduler and _scheduler.running:
            _scheduler.shutdown(wait=False)
        if stream_processor:
            await stream_processor.stop()
        if stream_processor_task:
            if not stream_processor_task.done():
                stream_processor_task.cancel()
            with suppress(asyncio.CancelledError):
                await stream_processor_task
        if db_manager:
            await db_manager.close_all()
        logger.info(f"{settings.service_name} shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    finally:
        stream_processor = None
        stream_processor_task = None


app = FastAPI(
    title="Statistics Service",
    description="ScoutPro Statistics & Analytics Service",
    version=APP_VERSION,
    contact={
        "name": "ScoutPro Platform",
    },
    license_info={
        "name": "Proprietary",
    },
    openapi_tags=OPENAPI_TAGS,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.include_router(statistics_router)
app.include_router(events_router)
app.include_router(events_enhanced_router)


@app.get("/health", tags=["system"], summary="Service health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": APP_VERSION
    }


@app.get("/", tags=["system"], summary="Service metadata")
async def root():
    return {
        "service": settings.service_name,
        "version": APP_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        workers=1 if settings.debug else 4
    )
