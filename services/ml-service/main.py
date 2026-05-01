"""
ML Service - Main Application
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
from api.ml import router as ml_router

settings = get_settings()
logger = setup_logger(settings.service_name, settings.log_level)

stream_processor = None
_startup_errors: list[str] = []
_models_ready = False

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
    global stream_processor, _models_ready, _startup_errors
    logger.info(f"Starting {settings.service_name}")

    try:
        import mlflow
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        logger.info(f"MLflow tracking URI: {settings.mlflow_tracking_uri}")

        from pathlib import Path
        Path(settings.model_cache_dir).mkdir(parents=True, exist_ok=True)

        try:
            logger.info("Starting ML Feature Stream Processor...")
            from services.stream_handler import MLFeatureStreamProcessor
            import asyncio
            stream_processor = MLFeatureStreamProcessor()
            asyncio.create_task(stream_processor.start())
            logger.info("ML Feature Stream Processor started")
        except Exception as e:
            err = f"Stream processor failed: {e}"
            logger.error(err)
            _startup_errors.append(err)

        try:
            from services.feature_extractor import bootstrap_player_features
            feature_count = await bootstrap_player_features()
            logger.info(f"Player feature store bootstrapped with {feature_count} documents")
        except Exception as e:
            logger.warning(f"Feature bootstrap skipped: {e}")

        try:
            from api.ml import player_predictor
            player_predictor.load_model()
            if player_predictor.is_fitted:
                logger.info("PlayerPerformancePredictor pre-loaded from disk")
                _models_ready = True
        except Exception as e:
            logger.warning(f"Model pre-load skipped: {e}")

        try:
            from api.ml import get_engine
            engine = get_engine()
            logger.info("Pre-training AnalyticsEngine algorithms...")
            result = engine.train_from_mongo("player_clustering", settings.mongodb_url, collection="player_features")
            logger.info(f"Clustering trained: {result}")
            result = engine.train_from_mongo("goals_regression", settings.mongodb_url, collection="player_statistics", target_field="goals")
            logger.info(f"Goals regression trained: {result}")
            _models_ready = True
        except Exception as e:
            err = f"Engine pre-training failed: {e}"
            logger.warning(err)
            _startup_errors.append(err)

        logger.info(f"{settings.service_name} started successfully")

    except Exception as e:
        err = f"Startup error: {e}"
        logger.error(err)
        _startup_errors.append(err)

    yield

    logger.info(f"Shutting down {settings.service_name}")
    try:
        if stream_processor:
            await stream_processor.stop()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


app = FastAPI(
    title="ML Service",
    description="ScoutPro Machine Learning Service",
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

app.include_router(ml_router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if not _startup_errors else "degraded",
        "models_ready": _models_ready,
        "startup_errors": _startup_errors,
        "service": settings.service_name,
        "version": "2.0.0",
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
