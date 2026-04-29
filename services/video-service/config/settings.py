"""Video Service Configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    service_name: str = "video-service"
    debug: bool = False
    log_level: str = "INFO"

    mongodb_url: str = "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
    mongodb_database: str = "scoutpro"

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "videos"
    minio_secure: bool = False

    max_video_size_mb: int = 500
    allowed_formats: list = [".mp4", ".avi", ".mov", ".mkv"]

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
