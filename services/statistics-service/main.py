"""
Statistics Service - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import sys
sys.path.append('/app')
from shared.utils.logger import setup_logger
from config.settings import get_settings
from api.statistics import router as statistics_router
from dependencies import (
    get_database_manager,
    kafka_producer,
    db_manager
)

settings = get_settings()
logger = setup_logger(settings.service_name, settings.log_level)

app = FastAPI(
    title="Statistics Service",
    description="ScoutPro Statistics & Analytics Service",
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

app.include_router(statistics_router)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.service_name}")

    try:
        manager = await get_database_manager()

        logger.info("Connecting to MongoDB...")
        await manager.connect_mongodb(
            settings.mongodb_url,
            settings.mongodb_database
        )
        logger.info("MongoDB connected")

        logger.info("Connecting to Redis...")
        await manager.connect_redis(settings.redis_url)
        logger.info("Redis connected")

        try:
            logger.info("Connecting to Kafka...")
            from aiokafka import AIOKafkaProducer
            global kafka_producer
            kafka_producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers
            )
            await kafka_producer.start()
            logger.info("Kafka connected")
        except Exception as e:
            logger.warning(f"Kafka connection failed (optional): {e}")

        logger.info(f"{settings.service_name} started successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.service_name}")

    try:
        if kafka_producer:
            await kafka_producer.stop()

        if db_manager:
            await db_manager.close_all()

        logger.info(f"{settings.service_name} shutdown complete")

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
        workers=1 if settings.debug else 4
    )
