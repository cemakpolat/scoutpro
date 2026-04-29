"""
Report Service - Main Application
Generates PDF and Excel reports for players, teams, and matches
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import sys
sys.path.append('/app')
from shared.utils.logger import setup_logger
from config.settings import get_settings
from api.endpoints.reports import router as reports_router

# Settings
settings = get_settings()

# Setup logging
logger = setup_logger(settings.service_name, settings.log_level)

# FastAPI app
app = FastAPI(
    title="Report Service",
    description="ScoutPro Report Generation Service",
    version="1.0.0",
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
app.include_router(reports_router)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info(f"Starting {settings.service_name}")
    logger.info(f"{settings.service_name} started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    logger.info(f"Shutting down {settings.service_name}")

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
