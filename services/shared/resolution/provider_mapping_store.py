"""Persistence helpers for canonical provider mappings."""

from datetime import datetime
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from shared.models.provider_mapping import ProviderMapping


class ProviderMappingStore:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["provider_mappings"]
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        await self.collection.create_index(
            [("entity_type", 1), ("provider", 1), ("provider_id", 1)],
            unique=True,
        )
        await self.collection.create_index([("entity_type", 1), ("canonical_id", 1)])
        self._initialized = True

    async def get_canonical_id(
        self,
        entity_type: str,
        provider: str,
        provider_id: str,
    ) -> Optional[str]:
        await self.initialize()

        document = await self.collection.find_one(
            {
                "entity_type": entity_type,
                "provider": provider,
                "provider_id": str(provider_id),
            },
            {"canonical_id": 1},
        )
        if not document:
            return None
        return document.get("canonical_id")

    async def upsert_mapping(
        self,
        entity_type: str,
        provider: str,
        provider_id: str,
        canonical_id: str,
        display_name: Optional[str] = None,
        source_match_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        await self.initialize()

        query = {
            "entity_type": entity_type,
            "provider": provider,
            "provider_id": str(provider_id),
        }
        existing = await self.collection.find_one(query)
        existing_created_at = existing.get("created_at") if existing else None

        mapping = ProviderMapping(
            canonical_id=str(existing.get("canonical_id") if existing and existing.get("canonical_id") else canonical_id),
            entity_type=entity_type,
            provider=provider,
            provider_id=str(provider_id),
            display_name=display_name,
            source_match_id=source_match_id,
            metadata=metadata or {},
            created_at=existing_created_at or datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        payload = mapping.model_dump(mode="json")
        await self.collection.update_one(query, {"$set": payload}, upsert=True)
        return mapping.canonical_id
