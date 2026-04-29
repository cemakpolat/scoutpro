"""
Player Service - Main Application
"""
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import sys
sys.path.append('/app')
from shared.utils.logger import setup_logger
from config.settings import get_settings
try:
    from api.endpoints.players import router as players_router
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Player routes unavailable at startup: {e}")
    players_router = APIRouter()
from dependencies import (
    get_database_manager,
    kafka_producer,
    db_manager
)
from services.cache_invalidator import PlayerCacheInvalidator

# Settings
settings = get_settings()

# Setup logging
logger = setup_logger(settings.service_name, settings.log_level)

# Global Cache Invalidator
cache_invalidator = None

# FastAPI app
app = FastAPI(
    title="Player Service",
    description="ScoutPro Player Data Service",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Include routers
app.include_router(players_router)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info(f"Starting {settings.service_name}")
    global cache_invalidator

    try:
        # Initialize database manager
        manager = await get_database_manager()

        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        await manager.connect_mongodb(
            settings.mongodb_url,
            settings.mongodb_database
        )
        logger.info("MongoDB connected")

        # Connect to Redis
        logger.info("Connecting to Redis...")
        await manager.connect_redis(settings.redis_url)
        logger.info("Redis connected")

        # Connect to Kafka (optional)
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

        # Start Cache Invalidator Stream Processor
        try:
            logger.info("Starting Player Cache Invalidator...")
            cache_invalidator = PlayerCacheInvalidator()
            import asyncio
            asyncio.create_task(cache_invalidator.start())
            logger.info("Cache Invalidator stream started")
        except Exception as e:
            logger.error(f"Failed to start cache invalidator: {e}")

        logger.info(f"{settings.service_name} started successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        # Dont crash if local
        # raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    logger.info(f"Shutting down {settings.service_name}")
    global cache_invalidator

    try:
        # Stop cache invalidator
        if cache_invalidator:
            await cache_invalidator.stop()

        # Close Kafka producer
        if kafka_producer:
            await kafka_producer.stop()

        # Close database connections
        if db_manager:
            await db_manager.close_all()

        logger.info(f"{settings.service_name} shutdown complete")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": "2.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
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
