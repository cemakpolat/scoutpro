"""
Dependency injection for FastAPI
"""
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis import Redis
from aiokafka import AIOKafkaProducer
from typing import Optional
import sys
sys.path.append('/app')
from shared.utils.database import DatabaseManager
from repository.mongo_repository import MongoPlayerRepository
from services.player_service import PlayerService
from config.settings import get_settings

# Global instances
db_manager: Optional[DatabaseManager] = None
mongo_db: Optional[AsyncIOMotorDatabase] = None
redis_client: Optional[Redis] = None
kafka_producer: Optional[AIOKafkaProducer] = None


async def get_database_manager() -> DatabaseManager:
    """Get database manager instance"""
    global db_manager
    if not db_manager:
        db_manager = DatabaseManager()
    return db_manager


async def get_mongo_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance"""
    global mongo_db
    if not mongo_db:
        settings = get_settings()
        manager = await get_database_manager()
        mongo_db = await manager.connect_mongodb(
            settings.mongodb_url,
            settings.mongodb_database
        )
    return mongo_db


async def get_redis() -> Redis:
    """Get Redis client instance"""
    global redis_client
    if not redis_client:
        settings = get_settings()
        manager = await get_database_manager()
        redis_client = await manager.connect_redis(settings.redis_url)
    return redis_client


async def get_kafka_producer() -> Optional[AIOKafkaProducer]:
    """Get Kafka producer instance"""
    global kafka_producer
    if not kafka_producer:
        try:
            settings = get_settings()
            kafka_producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: v
            )
            await kafka_producer.start()
        except Exception as e:
            # Kafka is optional - service can work without it
            import logging
            logging.warning(f"Could not connect to Kafka: {e}")
            kafka_producer = None
    return kafka_producer


async def get_player_service(
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    redis: Redis = Depends(get_redis),
    kafka: Optional[AIOKafkaProducer] = Depends(get_kafka_producer)
) -> PlayerService:
    """Get Player Service instance with dependencies"""
    settings = get_settings()

    # Create repository
    repository = MongoPlayerRepository(mongo_db)

    # Create service
    service = PlayerService(
        repository=repository,
        redis_client=redis,
        kafka_producer=kafka,
        cache_ttl=settings.cache_ttl_player
    )

    return service
