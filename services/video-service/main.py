"""
Video Service - Main Application
Handles video uploads, processing, and analysis
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
from api.endpoints.videos import router as videos_router

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
    title="Video Service",
    description="ScoutPro Video Processing Service",
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
app.include_router(videos_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name, "version": "1.0.0"}

@app.get("/")
async def root():
    return {"service": settings.service_name, "version": "1.0.0", "docs": "/docs"}

@app.post("/analyze-video")
async def analyze_video(video_id: str):
    """
    Advanced Logic Placeholder: OpenCV/YOLO
    In a fully functional setup, this would load the video, run OpenCV frame extraction,
    and apply a YOLO model for player detection and tracking.
    """
    return {
        "status": "processing",
        "video_id": video_id,
        "message": "Video queued for OpenCV/YOLO pipeline analysis.",
        "placeholder": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8011, reload=settings.debug, workers=1 if settings.debug else 4)
