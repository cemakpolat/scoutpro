"""
ML Service - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import sys
sys.path.append('/app')
from shared.utils.logger import setup_logger
from config.settings import get_settings
from api.ml import router as ml_router

settings = get_settings()
logger = setup_logger(settings.service_name, settings.log_level)

stream_processor = None

app = FastAPI(
    title="ML Service",
    description="ScoutPro Machine Learning Service",
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

app.include_router(ml_router)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.service_name}")
    global stream_processor

    try:
        # Initialize MLflow
        import mlflow
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        logger.info(f"MLflow tracking URI: {settings.mlflow_tracking_uri}")

        # Create model cache directory
        from pathlib import Path
        Path(settings.model_cache_dir).mkdir(parents=True, exist_ok=True)

        # Start ML Stream Processor
        try:
            logger.info("Starting ML Feature Stream Processor...")
            from services.stream_handler import MLFeatureStreamProcessor

            stream_processor = MLFeatureStreamProcessor()
            import asyncio
            asyncio.create_task(stream_processor.start())
            logger.info("ML Feature Stream Processor started")
        except Exception as e:
            logger.error(f"Failed to start stream processor: {e}")

        # Bootstrap player_features from existing player_statistics
        try:
            from services.feature_extractor import bootstrap_player_features
            feature_count = await bootstrap_player_features()
            logger.info(f"Player feature store bootstrapped with {feature_count} documents")
        except Exception as e:
            logger.warning(f"Feature bootstrap skipped: {e}")

        # Pre-load saved models if available
        try:
            from api.ml import player_predictor
            player_predictor.load_model()
            if player_predictor.is_fitted:
                logger.info("PlayerPerformancePredictor pre-loaded from disk")
        except Exception as e:
            logger.warning(f"Model pre-load skipped: {e}")

        # Pre-train engine algorithms from MongoDB
        try:
            from api.ml import get_engine
            engine = get_engine()
            logger.info("Pre-training AnalyticsEngine algorithms...")
            result = engine.train_from_mongo("player_clustering", settings.mongodb_url, collection="player_features")
            logger.info(f"Clustering trained: {result}")
            result = engine.train_from_mongo("goals_regression", settings.mongodb_url, collection="player_statistics", target_field="goals")
            logger.info(f"Goals regression trained: {result}")
        except Exception as e:
            logger.warning(f"Engine pre-training failed (non-fatal): {e}")

        logger.info(f"{settings.service_name} started successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        # Dont crash if local
        # raise


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.service_name}")
    global stream_processor

    try:
        if stream_processor:
            await stream_processor.stop()
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
