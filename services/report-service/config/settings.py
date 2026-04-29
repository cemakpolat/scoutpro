"""
Report Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Service
    service_name: str = "report-service"
    debug: bool = False
    log_level: str = "INFO"

    # MongoDB (for fetching data)
    mongodb_url: str = "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
    mongodb_database: str = "scoutpro"
    
    # Redis (Job tracking)
    redis_url: str = "redis://redis:6379/0"

    # MinIO (for storing generated reports)
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "reports"
    minio_secure: bool = False

    # Service URLs (for fetching data)
    player_service_url: str = "http://player-service:8000"
    team_service_url: str = "http://team-service:8000"
    match_service_url: str = "http://match-service:8000"
    statistics_service_url: str = "http://statistics-service:8000"

    # Report settings
    reports_expire_days: int = 30  # Delete reports older than 30 days
    max_report_size_mb: int = 50  # Maximum report size

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
