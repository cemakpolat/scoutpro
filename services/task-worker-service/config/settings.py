import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "task-worker-service"
    log_level: str = "INFO"
    debug: bool = False

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_tasks_topic: str = "tasks"
    kafka_task_completed_topic: str = "task.completed"
    kafka_consumer_group: str = "task-worker-group"

    # MongoDB
    mongodb_url: str = "mongodb://mongo:27017/scoutpro"
    mongodb_database: str = "scoutpro"

    # MinIO (for large file outputs: PDFs, CSVs, processed videos)
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    minio_secure: bool = False
    minio_tasks_bucket: str = "task-results"

    # Downstream service URLs (task worker calls these via HTTP)
    ml_service_url: str = "http://ml-service:8000"
    report_service_url: str = "http://report-service:8009"
    export_service_url: str = "http://export-service:8010"
    data_sync_service_url: str = "http://data-sync-service:8012"
    video_service_url: str = "http://video-service:8011"
    statistics_service_url: str = "http://statistics-service:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
