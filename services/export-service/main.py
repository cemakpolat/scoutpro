"""
Export Service - Main Application
Handles data exports in CSV, JSON, and Excel formats
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import sys
sys.path.append('/app')
from shared.utils.logger import setup_logger
from config.settings import get_settings
from api.endpoints.exports import router as exports_router

# Settings
settings = get_settings()

# Setup logging
logger = setup_logger(settings.service_name, settings.log_level)

# FastAPI app
app = FastAPI(
    title="Export Service",
    description="ScoutPro Data Export Service",
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
app.include_router(exports_router)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info(f"Starting {settings.service_name}")
    logger.info(f"{settings.service_name} started successfully")


from fastapi.responses import StreamingResponse

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    logger.info(f"Shutting down {settings.service_name}")
    logger.info(f"{settings.service_name} shutdown complete")

async def large_data_generator():
    yield "timestamp,player_id,x_pos,y_pos\n"
    for i in range(100):
        yield f"2026-04-26T15:00:00Z,P_{i},12.5,44.2\n"

@app.get("/stream-export/{match_id}")
async def stream_export(match_id: str):
    """
    Advanced Logic Placeholder: Streaming exports
    Streams vast amounts of match tracking records directly from db to client
    to avoid running out of API memory.
    """
    return StreamingResponse(
        large_data_generator(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=export_{match_id}.csv"}
    )


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
        port=8010,
        reload=settings.debug,
        workers=1 if settings.debug else 4
    )
