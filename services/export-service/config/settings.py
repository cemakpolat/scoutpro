"""
Export Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Service
    service_name: str = "export-service"
    debug: bool = False
    log_level: str = "INFO"

    # MongoDB (for fetching data)
    mongodb_url: str = "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
    mongodb_database: str = "scoutpro"

    # Service URLs (for fetching data)
    player_service_url: str = "http://player-service:8000"
    team_service_url: str = "http://team-service:8000"
    match_service_url: str = "http://match-service:8000"
    statistics_service_url: str = "http://statistics-service:8000"

    # Export settings
    max_export_rows: int = 100000  # Maximum rows per export
    export_chunk_size: int = 5000  # Chunk size for large exports

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
