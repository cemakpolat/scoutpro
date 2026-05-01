"""
Match Service - Main Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import os
import sys
sys.path.append('/app')
from shared.utils.logger import setup_logger
from config.settings import get_settings
from api.matches import router as matches_router
from dependencies import (
    get_database_manager,
    kafka_producer,
    db_manager
)
from services.stream_handler import MatchStreamProcessor

settings = get_settings()
logger = setup_logger(settings.service_name, settings.log_level)
stream_processor = None

_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://api-gateway:3001,http://localhost:3001,http://localhost:5173,http://localhost:5174",
    ).split(",")
    if o.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global stream_processor
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
            logger.info("Starting Match Stream Processor...")
            import asyncio
            stream_processor = MatchStreamProcessor()
            asyncio.create_task(stream_processor.start())
            logger.info("Match Stream Processor started")
        except Exception as e:
            logger.error(f"Failed to start stream processor: {e}")

        logger.info(f"{settings.service_name} started successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")

    yield

    logger.info(f"Shutting down {settings.service_name}")
    try:
        if stream_processor:
            await stream_processor.stop()
        if db_manager:
            await db_manager.close_all()
        logger.info(f"{settings.service_name} shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


app = FastAPI(
    title="Match Service",
    description="ScoutPro Match Data Service",
    version="2.0.0",
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

app.include_router(matches_router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": "2.0.0"
    }


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "version": "2.0.0",
        "docs": "/docs"
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
