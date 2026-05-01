"""
Report Service - Main Application
Generates PDF and Excel reports for players, teams, and matches
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
from api.endpoints.reports import router as reports_router

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
    title="Report Service",
    description="ScoutPro Report Generation Service",
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

app.include_router(reports_router)

@app.post("/generate-pdf/{match_id}")
async def generate_pdf(match_id: str):
    """
    Advanced Logic Placeholder: PDF Generation
    Would render LaTeX or ReportLab templates with visualizations (matplotlib/plotly)
    inserted into the report body.
    """
    return {
        "match_id": match_id,
        "status": "generated",
        "download_url": f"/downloads/reports/{match_id}_report.pdf",
        "placeholder": True
    }
    logger.info(f"{settings.service_name} shutdown complete")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8009,
        reload=settings.debug,
        workers=1 if settings.debug else 4
    )
