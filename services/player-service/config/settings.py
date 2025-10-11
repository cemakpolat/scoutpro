"""
Player Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Service
    service_name: str = "player-service"
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
    kafka_topic_player_events: str = "player.events"

    # External APIs
    opta_api_key: Optional[str] = None
    statsbomb_api_key: Optional[str] = None

    # Cache TTL (seconds)
    cache_ttl_player: int = 300  # 5 minutes
    cache_ttl_stats: int = 180  # 3 minutes

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
