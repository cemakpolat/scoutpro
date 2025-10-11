"""
Database connection utilities
"""
from motor.motor_asyncio import AsyncIOMotorClient
from redis import asyncio as aioredis
from typing import Optional
import os


class DatabaseManager:
    """Manage database connections"""

    def __init__(self):
        self.mongo_client: Optional[AsyncIOMotorClient] = None
        self.redis_client: Optional[aioredis.Redis] = None

    async def connect_mongodb(self, url: str, database: str = "scoutpro"):
        """Connect to MongoDB"""
        self.mongo_client = AsyncIOMotorClient(url)
        self.mongo_db = self.mongo_client[database]
        # Test connection
        await self.mongo_client.admin.command('ping')
        return self.mongo_db

    async def connect_redis(self, url: str):
        """Connect to Redis"""
        self.redis_client = await aioredis.from_url(
            url,
            encoding="utf-8",
            decode_responses=True
        )
        # Test connection
        await self.redis_client.ping()
        return self.redis_client

    async def close_connections(self):
        """Close all database connections"""
        if self.mongo_client:
            self.mongo_client.close()
        if self.redis_client:
            await self.redis_client.close()

    async def close_all(self):
        """Alias for close_connections"""
        await self.close_connections()


# Global database manager instance
db_manager = DatabaseManager()
