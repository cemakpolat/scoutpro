"""
Search Service - Main Application
"""
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
consumer_started = False

app = FastAPI(
    title="Search Service",
    description="ScoutPro Search Service with Elasticsearch",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.include_router(search_router)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.service_name}")
    global consumer_started

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


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.service_name}")
    global consumer_started

    try:
        if consumer_started:
            await stop_consumer()
            consumer_started = False
        await app.state.search_client.close()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


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
