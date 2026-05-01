"""
Search Service - Main Application
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import sys
sys.path.append('/app')
from shared.utils.logger import setup_logger
from config.settings import get_settings
from search.elasticsearch_client import SearchClient
from api.search import router as search_router
from consumers.event_consumer import start_consumer, stop_consumer

settings = get_settings()
logger = setup_logger(settings.service_name, settings.log_level)

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
    consumer_started = False
    logger.info(f"Starting {settings.service_name}")

    try:
        search_client = SearchClient(
            es_url=settings.elasticsearch_url,
            mongodb_url=settings.mongodb_url,
        )
        await search_client.connect()
        app.state.search_client = search_client
        logger.info(f"Search backend: {search_client.backend}")

        try:
            index_counts = await search_client.bulk_index_from_mongo()
            logger.info(f"Bulk index result: {index_counts}")
        except Exception as e:
            logger.warning(f"Bulk index from mongo skipped: {e}")

        try:
            await start_consumer()
            consumer_started = True
            logger.info("Search event consumer started")
        except Exception as e:
            logger.error(f"Failed to start search event consumer: {e}")

        logger.info(f"{settings.service_name} started successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    logger.info(f"Shutting down {settings.service_name}")
    try:
        if consumer_started:
            await stop_consumer()
        if hasattr(app.state, "search_client"):
            await app.state.search_client.close()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


app = FastAPI(
    title="Search Service",
    description="ScoutPro Search Service with Elasticsearch",
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

app.include_router(search_router)


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
        workers=1 if settings.debug else 2
    )
