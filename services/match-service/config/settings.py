"""
Match Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Service
    service_name: str = "match-service"
    debug: bool = False
    log_level: str = "INFO"

    # MongoDB
    mongodb_url: str = "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
    mongodb_database: str = "scoutpro"

    # TimescaleDB for match events
    timescale_url: str = "postgresql://scoutpro:scoutpro123@timescaledb:5432/scoutpro"

    # Redis
    redis_url: str = "redis://redis:6379/0"
    redis_password: Optional[str] = None

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_match_events: str = "match.events"

    # Cache TTL (seconds)
    cache_ttl_match: int = 60  # 1 minute for live matches
    cache_ttl_events: int = 30  # 30 seconds for match events

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
