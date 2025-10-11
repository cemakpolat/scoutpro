"""
Search Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Service
    service_name: str = "search-service"
    debug: bool = False
    log_level: str = "INFO"

    # Elasticsearch
    elasticsearch_url: str = "http://elasticsearch:9200"
    elasticsearch_index_players: str = "players"
    elasticsearch_index_teams: str = "teams"
    elasticsearch_index_matches: str = "matches"

    # MongoDB (for fallback)
    mongodb_url: str = "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
    mongodb_database: str = "scoutpro"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Cache TTL
    cache_ttl: int = 300  # 5 minutes

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
