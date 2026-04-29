"""Analytics Service Configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    service_name: str = "analytics-service"
    debug: bool = False
    log_level: str = "INFO"

    mongodb_url: str = "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
    mongodb_database: str = "scoutpro"

    redis_url: str = "redis://redis:6379/0"
    timescaledb_url: str = "postgresql://scoutpro:scoutpro123@timescaledb:5432/scoutpro"

    cache_ttl_analytics: int = 600  # 10 minutes

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
