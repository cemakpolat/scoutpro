"""
Live Ingestion Service - Main Application
"""
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

# Global clients to be injected
kafka_producer = None
stream_processor = None

app = FastAPI(
    title="Live Ingestion Service",
    description="ScoutPro Live Data Ingestion Service",
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

app.include_router(ingestion_router)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.service_name}")
    global kafka_producer, stream_processor

    try:
        # Initialize connections
        logger.info("Initializing Kafka producer...")
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers
        )
        await kafka_producer.start()

        # Init global processor
        stream_processor = LiveDataProcessor(
            kafka_producer=kafka_producer
        )
        
        # Make processor available to routers via app state
        app.state.processor = stream_processor

        logger.info(f"{settings.service_name} started successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        # Keep running even if kafka fails on local without compose
        
@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.service_name}")
    global kafka_producer
    
    if kafka_producer:
        await kafka_producer.stop()


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
