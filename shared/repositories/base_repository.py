"""
Base Repository

Abstract base class for all repositories.
Provides common CRUD operations and query functionality for MongoDB.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic
from datetime import datetime
import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING
from dataclasses import asdict

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository for entity persistence

    This class provides:
    - CRUD operations (create, read, update, delete)
    - Query builders
    - Indexing
    - Bulk operations
    - Provider ID lookups

    Subclasses implement entity-specific logic:
    - PlayerRepository
    - TeamRepository
    - MatchRepository
    - EventRepository
    """

    def __init__(
        self,
        mongo_uri: str = 'mongodb://localhost:27017',
        db_name: str = 'scoutpro',
        collection_name: Optional[str] = None
    ):
        """
        Initialize repository

        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name
            collection_name: Collection name (defaults to entity type)
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name or self.get_collection_name()

        # MongoDB connection (lazy loading)
        self._client: Optional[MongoClient] = None
        self._db = None
        self._collection = None

    @abstractmethod
    def get_collection_name(self) -> str:
        """
        Get collection name for this repository

        Returns:
            Collection name (e.g., 'players', 'teams', 'matches', 'events')
        """
        pass

    @abstractmethod
    def to_document(self, entity: T) -> Dict[str, Any]:
        """
        Convert entity to MongoDB document

        Args:
            entity: Entity to convert

        Returns:
            MongoDB document dict

        Example:
            doc = self.to_document(player)
            → {'_id': 'player_123', 'name': 'Mohamed Salah', ...}
        """
        pass

    @abstractmethod
    def from_document(self, doc: Dict[str, Any]) -> T:
        """
        Convert MongoDB document to entity

        Args:
            doc: MongoDB document

        Returns:
            Entity instance

        Example:
            player = self.from_document(doc)
        """
        pass

    def _connect(self):
        """Lazy connect to MongoDB"""
        if self._client is None:
            self._client = MongoClient(self.mongo_uri)
            self._db = self._client[self.db_name]
            self._collection = self._db[self.collection_name]

            # Create indexes
            self.create_indexes()

    @abstractmethod
    def create_indexes(self):
        """
        Create MongoDB indexes for this collection

        Called automatically on first connection.

        Example:
            self._collection.create_index([('name', ASCENDING)])
            self._collection.create_index([('provider_ids.opta', ASCENDING)])
        """
        pass

    # ========================================
    # CREATE
    # ========================================

    def create(self, entity: T) -> T:
        """
        Create a new entity

        Args:
            entity: Entity to create

        Returns:
            Created entity

        Raises:
            pymongo.errors.DuplicateKeyError: If entity with same ID exists

        Example:
            player = ScoutProPlayer(...)
            created = repo.create(player)
        """
        self._connect()

        doc = self.to_document(entity)
        self._collection.insert_one(doc)

        return entity

    def create_many(self, entities: List[T]) -> List[T]:
        """
        Create multiple entities

        Args:
            entities: List of entities to create

        Returns:
            List of created entities

        Example:
            players = [ScoutProPlayer(...), ScoutProPlayer(...)]
            created = repo.create_many(players)
        """
        self._connect()

        if not entities:
            return []

        docs = [self.to_document(e) for e in entities]
        self._collection.insert_many(docs)

        return entities

    # ========================================
    # READ
    # ========================================

    def find_by_id(self, entity_id: str) -> Optional[T]:
        """
        Find entity by ID

        Args:
            entity_id: Entity ID

        Returns:
            Entity or None if not found

        Example:
            player = repo.find_by_id('player_123')
        """
        self._connect()

        doc = self._collection.find_one({'_id': entity_id})

        if doc:
            return self.from_document(doc)

        return None

    def find_by_provider_id(self, provider: str, provider_id: str) -> Optional[T]:
        """
        Find entity by provider-specific ID

        Args:
            provider: Provider name ('opta', 'statsbomb', etc.)
            provider_id: Provider-specific ID

        Returns:
            Entity or None if not found

        Example:
            player = repo.find_by_provider_id('opta', 'p12345')
        """
        self._connect()

        query = {f'provider_ids.{provider}': provider_id}
        doc = self._collection.find_one(query)

        if doc:
            return self.from_document(doc)

        return None

    def find_all(self, limit: Optional[int] = None, skip: int = 0) -> List[T]:
        """
        Find all entities

        Args:
            limit: Max number of results
            skip: Number of results to skip

        Returns:
            List of entities

        Example:
            players = repo.find_all(limit=100)
        """
        self._connect()

        cursor = self._collection.find().skip(skip)

        if limit:
            cursor = cursor.limit(limit)

        return [self.from_document(doc) for doc in cursor]

    def find(
        self,
        query: Dict[str, Any],
        limit: Optional[int] = None,
        skip: int = 0,
        sort: Optional[List[tuple]] = None
    ) -> List[T]:
        """
        Find entities matching query

        Args:
            query: MongoDB query dict
            limit: Max number of results
            skip: Number of results to skip
            sort: Sort specification [(field, direction), ...]

        Returns:
            List of entities

        Example:
            # Find all players with position 'forward'
            players = repo.find({'position': 'forward'}, limit=20)

            # Find with sorting
            players = repo.find(
                {'nationality': 'Egypt'},
                sort=[('name', ASCENDING)]
            )
        """
        self._connect()

        cursor = self._collection.find(query).skip(skip)

        if limit:
            cursor = cursor.limit(limit)

        if sort:
            cursor = cursor.sort(sort)

        return [self.from_document(doc) for doc in cursor]

    def find_one(self, query: Dict[str, Any]) -> Optional[T]:
        """
        Find single entity matching query

        Args:
            query: MongoDB query dict

        Returns:
            Entity or None if not found

        Example:
            player = repo.find_one({'name': 'Mohamed Salah'})
        """
        self._connect()

        doc = self._collection.find_one(query)

        if doc:
            return self.from_document(doc)

        return None

    def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching query

        Args:
            query: MongoDB query dict (None = count all)

        Returns:
            Count

        Example:
            total = repo.count()
            forwards = repo.count({'position': 'forward'})
        """
        self._connect()

        if query:
            return self._collection.count_documents(query)
        else:
            return self._collection.estimated_document_count()

    # ========================================
    # UPDATE
    # ========================================

    def update(self, entity: T) -> T:
        """
        Update an existing entity

        Args:
            entity: Entity to update (must have ID)

        Returns:
            Updated entity

        Raises:
            ValueError: If entity not found

        Example:
            player.name = 'Mo Salah'
            updated = repo.update(player)
        """
        self._connect()

        doc = self.to_document(entity)
        entity_id = doc['_id']

        result = self._collection.replace_one(
            {'_id': entity_id},
            doc
        )

        if result.matched_count == 0:
            raise ValueError(f"Entity with ID {entity_id} not found")

        return entity

    def update_fields(
        self,
        entity_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update specific fields of an entity

        Args:
            entity_id: Entity ID
            updates: Dict of field → value to update

        Returns:
            True if entity was updated, False if not found

        Example:
            repo.update_fields('player_123', {
                'position': 'right_wing',
                'updated_at': datetime.now()
            })
        """
        self._connect()

        result = self._collection.update_one(
            {'_id': entity_id},
            {'$set': updates}
        )

        return result.matched_count > 0

    def upsert(self, entity: T) -> T:
        """
        Insert or update entity (upsert)

        If entity exists, updates it. Otherwise, creates it.

        Args:
            entity: Entity to upsert

        Returns:
            Entity

        Example:
            player = ScoutProPlayer(id='player_123', ...)
            repo.upsert(player)  # Creates or updates
        """
        self._connect()

        doc = self.to_document(entity)
        entity_id = doc['_id']

        self._collection.replace_one(
            {'_id': entity_id},
            doc,
            upsert=True
        )

        return entity

    # ========================================
    # DELETE
    # ========================================

    def delete(self, entity_id: str) -> bool:
        """
        Delete entity by ID

        Args:
            entity_id: Entity ID

        Returns:
            True if deleted, False if not found

        Example:
            deleted = repo.delete('player_123')
        """
        self._connect()

        result = self._collection.delete_one({'_id': entity_id})

        return result.deleted_count > 0

    def delete_many(self, query: Dict[str, Any]) -> int:
        """
        Delete multiple entities matching query

        Args:
            query: MongoDB query dict

        Returns:
            Number of entities deleted

        Example:
            # Delete all players from a specific provider
            count = repo.delete_many({'provider': 'old_provider'})
        """
        self._connect()

        result = self._collection.delete_many(query)

        return result.deleted_count

    # ========================================
    # BULK OPERATIONS
    # ========================================

    def bulk_upsert(self, entities: List[T]) -> int:
        """
        Bulk upsert entities

        Args:
            entities: List of entities to upsert

        Returns:
            Number of entities upserted

        Example:
            players = [ScoutProPlayer(...), ScoutProPlayer(...)]
            count = repo.bulk_upsert(players)
        """
        self._connect()

        if not entities:
            return 0

        operations = []
        for entity in entities:
            doc = self.to_document(entity)
            entity_id = doc['_id']

            operations.append(
                pymongo.ReplaceOne(
                    {'_id': entity_id},
                    doc,
                    upsert=True
                )
            )

        result = self._collection.bulk_write(operations)

        return result.upserted_count + result.modified_count

    # ========================================
    # UTILITY
    # ========================================

    def exists(self, entity_id: str) -> bool:
        """
        Check if entity exists

        Args:
            entity_id: Entity ID

        Returns:
            True if exists, False otherwise

        Example:
            if repo.exists('player_123'):
                print("Player exists")
        """
        self._connect()

        return self._collection.count_documents({'_id': entity_id}, limit=1) > 0

    def drop_collection(self):
        """
        Drop the entire collection

        WARNING: This deletes all data!

        Example:
            repo.drop_collection()  # Careful!
        """
        self._connect()

        self._collection.drop()

    def __del__(self):
        """Close MongoDB connection on destruction"""
        if hasattr(self, '_client') and self._client:
            self._client.close()
