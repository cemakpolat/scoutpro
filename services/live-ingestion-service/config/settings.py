"""
Live Ingestion Service Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Service
    service_name: str = "live-ingestion-service"
    debug: bool = False
    log_level: str = "INFO"

    # MongoDB
    mongodb_url: str = "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
    mongodb_database: str = "scoutpro"

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_live_events: str = "live.events"
    kafka_topic_match_updates: str = "match.updates"

    # Opta API
    opta_api_url: str = "https://api.opta.com"
    opta_api_key: Optional[str] = None
    opta_poll_interval: int = 5  # seconds

    # StatsBomb API
    statsbomb_api_url: str = "https://api.statsbomb.com"
    statsbomb_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
