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

    try:
        # Initialize MLflow
        import mlflow
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        logger.info(f"MLflow tracking URI: {settings.mlflow_tracking_uri}")

        # Create model cache directory
        from pathlib import Path
        Path(settings.model_cache_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"{settings.service_name} started successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.service_name}")


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
