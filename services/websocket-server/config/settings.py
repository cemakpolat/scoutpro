"""
WebSocket Server Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Service
    service_name: str = "websocket-server"
    debug: bool = False
    log_level: str = "INFO"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_consumer_group: str = "websocket-server"
    kafka_topics: str = "live.events,match.updates,player.events"

    # WebSocket settings
    heartbeat_interval: int = 30  # seconds
    max_connections: int = 10000

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
