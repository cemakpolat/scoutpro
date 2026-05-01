"""
ML Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Service
    service_name: str = "ml-service"
    debug: bool = False
    log_level: str = "INFO"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MLflow
    mlflow_tracking_uri: str = "http://mlflow:5000"
    mlflow_experiment_name: str = "scoutpro"

    # MinIO for model storage
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "mlmodels"

    # MongoDB
    mongodb_url: str = "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"

    # Model settings
    model_cache_dir: str = "/app/model_cache"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
