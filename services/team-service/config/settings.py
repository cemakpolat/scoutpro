"""
Team Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Service
    service_name: str = "team-service"
    debug: bool = False
    log_level: str = "INFO"

    # MongoDB
    mongodb_url: str = "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
    mongodb_database: str = "scoutpro"

    # Redis
    redis_url: str = "redis://redis:6379/0"
    redis_password: Optional[str] = None

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_team_events: str = "team.events"

    # Cache TTL (seconds)
    cache_ttl_team: int = 600  # 10 minutes
    cache_ttl_squad: int = 300  # 5 minutes

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
