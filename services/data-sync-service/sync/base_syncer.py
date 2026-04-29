"""
Base Syncer

Abstract base class for entity synchronization.
Defines the workflow for syncing data from providers to canonical storage.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic
from datetime import datetime
from enum import Enum
import asyncio

from shared.adapters.factory import get_factory
from shared.repositories import BaseRepository
from shared.resolution import BaseResolver
from shared.merger import BaseMerger
from shared.quality import QualityEnricher

T = TypeVar('T')


class SyncStatus(Enum):
    """Status of a sync operation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncResult:
    """Result of a sync operation"""

    def __init__(
        self,
        status: SyncStatus,
        entities_fetched: int = 0,
        entities_created: int = 0,
        entities_updated: int = 0,
        entities_merged: int = 0,
        conflicts_detected: int = 0,
        errors: Optional[List[str]] = None,
        duration_seconds: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.status = status
        self.entities_fetched = entities_fetched
        self.entities_created = entities_created
        self.entities_updated = entities_updated
        self.entities_merged = entities_merged
        self.conflicts_detected = conflicts_detected
        self.errors = errors or []
        self.duration_seconds = duration_seconds
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            'status': self.status.value,
            'entities_fetched': self.entities_fetched,
            'entities_created': self.entities_created,
            'entities_updated': self.entities_updated,
            'entities_merged': self.entities_merged,
            'conflicts_detected': self.conflicts_detected,
            'errors': self.errors,
            'duration_seconds': self.duration_seconds,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class BaseSyncer(ABC, Generic[T]):
    """
    Abstract base class for entity synchronization

    Workflow:
    1. Fetch entities from provider
    2. Map to canonical format
    3. Resolve entities (match with existing)
    4. Merge with existing data
    5. Enrich with quality metadata
    6. Store in repository

    Subclasses:
    - PlayerSyncer
    - TeamSyncer
    - MatchSyncer
    - EventSyncer
    """

    def __init__(
        self,
        provider: str,
        repository: BaseRepository[T],
        resolver: Optional[BaseResolver] = None,
        merger: Optional[BaseMerger] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize syncer

        Args:
            provider: Provider name ('opta', 'statsbomb', etc.)
            repository: Repository for storing entities
            resolver: Resolver for entity matching
            merger: Merger for combining data from multiple providers
            config: Provider configuration
        """
        self.provider = provider
        self.repository = repository
        self.resolver = resolver
        self.merger = merger
        self.config = config or {}

        # Factory for getting adapters
        self.factory = get_factory()

        # Quality enricher
        self.enricher = QualityEnricher()

        # Sync statistics
        self.stats = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'merged': 0,
            'conflicts': 0,
            'errors': []
        }

    @abstractmethod
    def get_entity_type(self) -> str:
        """Get entity type name"""
        pass

    @abstractmethod
    async def fetch_entities(self, **kwargs) -> List[T]:
        """
        Fetch entities from provider

        Args:
            **kwargs: Provider-specific parameters

        Returns:
            List of entities in canonical format

        Example:
            entities = await self.fetch_entities(
                competition_id='8',
                season_id='2023'
            )
        """
        pass

    async def sync(self, **kwargs) -> SyncResult:
        """
        Perform full sync workflow

        Args:
            **kwargs: Parameters for fetching entities

        Returns:
            SyncResult with statistics

        Example:
            result = await syncer.sync(
                competition_id='8',
                season_id='2023'
            )
            print(f"Synced {result.entities_created} new entities")
        """
        start_time = datetime.now()

        try:
            # 1. Fetch entities from provider
            print(f"[{self.provider}] Fetching {self.get_entity_type()}...")
            entities = await self.fetch_entities(**kwargs)
            self.stats['fetched'] = len(entities)
            print(f"[{self.provider}] Fetched {len(entities)} {self.get_entity_type()}")

            if not entities:
                return SyncResult(
                    status=SyncStatus.COMPLETED,
                    entities_fetched=0,
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )

            # 2. Resolve and merge entities
            print(f"[{self.provider}] Resolving and merging {self.get_entity_type()}...")
            merged_entities = await self.resolve_and_merge(entities)
            self.stats['merged'] = len([e for e in merged_entities if e is not None])

            # 3. Enrich with quality metadata
            print(f"[{self.provider}] Enriching {self.get_entity_type()}...")
            enriched_entities = self.enrich_entities(merged_entities)

            # 4. Store in repository
            print(f"[{self.provider}] Storing {self.get_entity_type()}...")
            stored_count = await self.store_entities(enriched_entities)
            self.stats['created'] = stored_count

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            # Build result
            result = SyncResult(
                status=SyncStatus.COMPLETED,
                entities_fetched=self.stats['fetched'],
                entities_created=self.stats['created'],
                entities_updated=self.stats['updated'],
                entities_merged=self.stats['merged'],
                conflicts_detected=self.stats['conflicts'],
                duration_seconds=duration,
                metadata={
                    'provider': self.provider,
                    'entity_type': self.get_entity_type(),
                    **kwargs
                }
            )

            print(f"[{self.provider}] Sync completed in {duration:.2f}s")
            return result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Sync failed: {str(e)}"
            self.stats['errors'].append(error_msg)
            print(f"[{self.provider}] {error_msg}")

            return SyncResult(
                status=SyncStatus.FAILED,
                entities_fetched=self.stats['fetched'],
                entities_created=self.stats['created'],
                errors=[error_msg],
                duration_seconds=duration
            )

    async def resolve_and_merge(self, entities: List[T]) -> List[Optional[T]]:
        """
        Resolve entities against existing data and merge

        Args:
            entities: List of entities from provider

        Returns:
            List of merged entities

        Example:
            merged = await self.resolve_and_merge(fetched_entities)
        """
        merged_entities = []

        for entity in entities:
            try:
                # Check if entity already exists in repository
                existing = await self.find_existing_entity(entity)

                if existing:
                    # Merge with existing
                    if self.merger:
                        merged = self.merger.merge(
                            existing,
                            entity,
                            primary_provider=existing.provider,
                            secondary_provider=self.provider
                        )
                        merged_entities.append(merged)
                        self.stats['updated'] += 1
                    else:
                        # No merger - just use new entity
                        merged_entities.append(entity)
                        self.stats['updated'] += 1
                else:
                    # New entity
                    merged_entities.append(entity)

            except Exception as e:
                error_msg = f"Error resolving entity: {str(e)}"
                self.stats['errors'].append(error_msg)
                print(f"[{self.provider}] {error_msg}")
                merged_entities.append(None)

        return merged_entities

    async def find_existing_entity(self, entity: T) -> Optional[T]:
        """
        Find existing entity in repository

        Uses resolver to match entities across providers.

        Args:
            entity: Entity to find

        Returns:
            Existing entity or None

        Example:
            existing = await self.find_existing_entity(player)
        """
        # Try to find by provider ID
        if hasattr(entity, 'external_id') and entity.external_id:
            existing = self.repository.find_by_provider_id(self.provider, entity.external_id)
            if existing:
                return existing

        # Try to find by resolver (fuzzy matching)
        if self.resolver:
            # Get all canonical entities (this could be optimized with better queries)
            candidates = self.repository.find_by_provider('canonical', limit=1000)

            if candidates:
                match_result = self.resolver.find_match(entity, candidates)
                if match_result:
                    matched_entity, confidence = match_result
                    return matched_entity

        return None

    def enrich_entities(self, entities: List[Optional[T]]) -> List[T]:
        """
        Enrich entities with quality metadata

        Args:
            entities: List of entities (may contain None)

        Returns:
            List of enriched entities (None values filtered out)

        Example:
            enriched = self.enrich_entities(merged_entities)
        """
        enriched = []

        for entity in entities:
            if entity is None:
                continue

            try:
                # Enrich based on entity type
                entity_type = self.get_entity_type()

                if entity_type == 'player':
                    self.enricher.enrich_player(entity)
                elif entity_type == 'team':
                    self.enricher.enrich_team(entity)
                elif entity_type == 'match':
                    self.enricher.enrich_match(entity)
                elif entity_type == 'event':
                    self.enricher.enrich_event(entity)

                enriched.append(entity)

            except Exception as e:
                error_msg = f"Error enriching entity: {str(e)}"
                self.stats['errors'].append(error_msg)
                print(f"[{self.provider}] {error_msg}")

        return enriched

    async def store_entities(self, entities: List[T]) -> int:
        """
        Store entities in repository

        Args:
            entities: List of entities to store

        Returns:
            Number of entities stored

        Example:
            count = await self.store_entities(enriched_entities)
        """
        if not entities:
            return 0

        try:
            # Use bulk upsert for efficiency
            count = self.repository.bulk_upsert(entities)
            return count

        except Exception as e:
            error_msg = f"Error storing entities: {str(e)}"
            self.stats['errors'].append(error_msg)
            print(f"[{self.provider}] {error_msg}")
            return 0

    def reset_stats(self):
        """Reset sync statistics"""
        self.stats = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'merged': 0,
            'conflicts': 0,
            'errors': []
        }
