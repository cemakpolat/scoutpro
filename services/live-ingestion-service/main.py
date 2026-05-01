"""
Live Ingestion Service - Main Application
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
from api.ingestion import router as ingestion_router
from ingestion.stream_processor import LiveDataProcessor
from aiokafka import AIOKafkaProducer

settings = get_settings()
logger = setup_logger(settings.service_name, settings.log_level)

kafka_producer = None
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
    global kafka_producer, stream_processor
    logger.info(f"Starting {settings.service_name}")

    stream_processor = LiveDataProcessor(
        kafka_producer=None,
        bootstrap_servers=settings.kafka_bootstrap_servers,
    )
    app.state.processor = stream_processor

    try:
        logger.info("Initializing Kafka producer...")
        kafka_producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
        await kafka_producer.start()
        stream_processor.kafka = kafka_producer
        logger.info(f"{settings.service_name} started successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")

    yield

    logger.info(f"Shutting down {settings.service_name}")
    if stream_processor:
        await stream_processor.close()
    elif kafka_producer:
        await kafka_producer.stop()


app = FastAPI(
    title="Live Ingestion Service",
    description="ScoutPro Live Data Ingestion Service",
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

app.include_router(ingestion_router)


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
        reload=settings.debug
    )
