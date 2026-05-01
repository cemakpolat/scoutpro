"""
Analytics Service - Main Application
Provides pre-aggregated analytics and dashboards
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
from api.endpoints.analytics import router as analytics_router

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
    logger.info(f"Starting {settings.service_name}")
    yield
    logger.info(f"Shutting down {settings.service_name}")


app = FastAPI(
    title="Analytics Service",
    description="ScoutPro Analytics and BI Service",
    version="1.0.0",
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
app.include_router(analytics_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name, "version": "1.0.0"}

@app.get("/")
async def root():
    return {"service": settings.service_name, "version": "1.0.0", "docs": "/docs"}

@app.get("/advanced-metrics/{match_id}")
async def get_advanced_metrics(match_id: str, time_bucket: str = "5m"):
    """
    Advanced Logic: Calls Statistics service to fetch TimescaleDB aggregations
    for generating heatmaps and player load metrics.
    """
    from services.analytics_handler import AnalyticsHandler
    handler = AnalyticsHandler()
    try:
        # Assuming we have a statistics endpoint for this
        response = await handler.client.get(
            f"{handler.statistics_service_url}/api/v2/statistics/match/{match_id}/advanced",
            params={"time_bucket": time_bucket}
        )
        return response.json() if response.status_code == 200 else {"match_id": match_id, "metrics": []}
    except Exception as e:
        return {"error": str(e), "match_id": match_id, "metrics": []}
    finally:
        await handler.close(),

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8012, reload=settings.debug, workers=1 if settings.debug else 4)
