"""
Player Repository

Repository for storing and retrieving player data from MongoDB.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pymongo import ASCENDING, TEXT

from shared.domain.models import ScoutProPlayer
from shared.repositories.base_repository import BaseRepository


class PlayerRepository(BaseRepository[ScoutProPlayer]):
    """
    Repository for player entities

    Provides:
    - CRUD operations for players
    - Search by name (fuzzy matching)
    - Filter by position, nationality, team
    - Provider ID lookups

    Usage:
        repo = PlayerRepository()

        # Create player
        player = ScoutProPlayer(...)
        repo.create(player)

        # Find by ID
        player = repo.find_by_id('player_123')

        # Find by provider ID
        player = repo.find_by_provider_id('opta', 'p12345')

        # Search by name
        players = repo.search_by_name('Salah')

        # Find by position
        forwards = repo.find_by_position('forward')
    """

    def get_collection_name(self) -> str:
        return "players"

    def create_indexes(self):
        """Create MongoDB indexes for player collection"""
        if self._collection is None:
            return

        # Name index (for searching)
        self._collection.create_index([('name', TEXT)])

        # Provider IDs (for lookups)
        self._collection.create_index([('provider_ids.opta', ASCENDING)])
        self._collection.create_index([('provider_ids.statsbomb', ASCENDING)])
        self._collection.create_index([('provider_ids.wyscout', ASCENDING)])

        # Position index (for filtering)
        self._collection.create_index([('position', ASCENDING)])

        # Nationality index (for filtering)
        self._collection.create_index([('nationality', ASCENDING)])

        # Last name index (for searching)
        self._collection.create_index([('last_name', ASCENDING)])

        # Updated timestamp (for sync)
        self._collection.create_index([('updated_at', ASCENDING)])

    def to_document(self, player: ScoutProPlayer) -> Dict[str, Any]:
        """
        Convert ScoutProPlayer to MongoDB document

        Args:
            player: Player to convert

        Returns:
            MongoDB document
        """
        doc = {
            '_id': player.id,
            'external_id': player.external_id,
            'provider': player.provider,
            'name': player.name,
            'first_name': player.first_name,
            'last_name': player.last_name,
            'known_name': player.known_name,
            'birth_date': player.birth_date.isoformat() if player.birth_date else None,
            'position': player.position,
            'detailed_position': player.detailed_position,
            'nationality': player.nationality,
            'height_cm': player.height_cm,
            'weight_kg': player.weight_kg,
            'preferred_foot': player.preferred_foot,
            'provider_ids': player.provider_ids or {},
            'provider_data': player.provider_data or {},
            'data_quality': player.data_quality or {},
            'created_at': player.created_at,
            'updated_at': player.updated_at
        }

        return doc

    def from_document(self, doc: Dict[str, Any]) -> ScoutProPlayer:
        """
        Convert MongoDB document to ScoutProPlayer

        Args:
            doc: MongoDB document

        Returns:
            ScoutProPlayer instance
        """
        # Parse birth_date
        birth_date_val = None
        if doc.get('birth_date'):
            try:
                birth_date_val = date.fromisoformat(doc['birth_date'])
            except (ValueError, TypeError):
                pass

        player = ScoutProPlayer(
            id=doc['_id'],
            external_id=doc.get('external_id'),
            provider=doc.get('provider', 'canonical'),
            name=doc.get('name', ''),
            first_name=doc.get('first_name'),
            last_name=doc.get('last_name'),
            known_name=doc.get('known_name'),
            birth_date=birth_date_val,
            position=doc.get('position'),
            detailed_position=doc.get('detailed_position'),
            nationality=doc.get('nationality'),
            height_cm=doc.get('height_cm'),
            weight_kg=doc.get('weight_kg'),
            preferred_foot=doc.get('preferred_foot'),
            provider_ids=doc.get('provider_ids', {}),
            provider_data=doc.get('provider_data', {}),
            data_quality=doc.get('data_quality', {}),
            created_at=doc.get('created_at', datetime.now()),
            updated_at=doc.get('updated_at', datetime.now())
        )

        return player

    # ========================================
    # PLAYER-SPECIFIC QUERIES
    # ========================================

    def search_by_name(
        self,
        name: str,
        limit: int = 20
    ) -> List[ScoutProPlayer]:
        """
        Search players by name (fuzzy text search)

        Args:
            name: Name to search for
            limit: Max results

        Returns:
            List of matching players

        Example:
            players = repo.search_by_name('Salah')
            → [ScoutProPlayer(name='Mohamed Salah'), ...]
        """
        self._connect()

        # Use MongoDB text search
        query = {'$text': {'$search': name}}

        return self.find(query, limit=limit)

    def find_by_name_exact(self, name: str) -> Optional[ScoutProPlayer]:
        """
        Find player by exact name match

        Args:
            name: Full name

        Returns:
            Player or None

        Example:
            player = repo.find_by_name_exact('Mohamed Salah')
        """
        return self.find_one({'name': name})

    def find_by_position(
        self,
        position: str,
        limit: Optional[int] = None
    ) -> List[ScoutProPlayer]:
        """
        Find players by position

        Args:
            position: Position (e.g., 'forward', 'midfielder')
            limit: Max results

        Returns:
            List of players

        Example:
            forwards = repo.find_by_position('forward', limit=50)
        """
        return self.find({'position': position}, limit=limit)

    def find_by_nationality(
        self,
        nationality: str,
        limit: Optional[int] = None
    ) -> List[ScoutProPlayer]:
        """
        Find players by nationality

        Args:
            nationality: Nationality (e.g., 'Egypt', 'England')
            limit: Max results

        Returns:
            List of players

        Example:
            egyptian_players = repo.find_by_nationality('Egypt')
        """
        return self.find({'nationality': nationality}, limit=limit)

    def find_by_birth_year(
        self,
        year: int,
        limit: Optional[int] = None
    ) -> List[ScoutProPlayer]:
        """
        Find players born in a specific year

        Args:
            year: Birth year
            limit: Max results

        Returns:
            List of players

        Example:
            players_1992 = repo.find_by_birth_year(1992)
        """
        # Query for birth_date starting with year
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        query = {
            'birth_date': {
                '$gte': start_date,
                '$lte': end_date
            }
        }

        return self.find(query, limit=limit)

    def find_recent(self, limit: int = 100) -> List[ScoutProPlayer]:
        """
        Find recently updated players

        Args:
            limit: Max results

        Returns:
            List of players sorted by updated_at descending

        Example:
            recent = repo.find_recent(limit=50)
        """
        from pymongo import DESCENDING

        return self.find(
            {},
            limit=limit,
            sort=[('updated_at', DESCENDING)]
        )

    def find_by_provider(
        self,
        provider: str,
        limit: Optional[int] = None
    ) -> List[ScoutProPlayer]:
        """
        Find all players from a specific provider

        Args:
            provider: Provider name ('opta', 'statsbomb', 'canonical')
            limit: Max results

        Returns:
            List of players

        Example:
            opta_players = repo.find_by_provider('opta')
        """
        return self.find({'provider': provider}, limit=limit)

    def find_canonical_players(self, limit: Optional[int] = None) -> List[ScoutProPlayer]:
        """
        Find all canonical (merged) players

        Args:
            limit: Max results

        Returns:
            List of canonical players

        Example:
            canonical = repo.find_canonical_players()
        """
        return self.find_by_provider('canonical', limit=limit)

    # ========================================
    # AGGREGATION QUERIES
    # ========================================

    def get_position_distribution(self) -> Dict[str, int]:
        """
        Get distribution of players by position

        Returns:
            Dict of position → count

        Example:
            dist = repo.get_position_distribution()
            → {'forward': 1234, 'midfielder': 2345, ...}
        """
        self._connect()

        pipeline = [
            {'$group': {'_id': '$position', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]

        results = self._collection.aggregate(pipeline)

        return {r['_id']: r['count'] for r in results if r['_id']}

    def get_nationality_distribution(self) -> Dict[str, int]:
        """
        Get distribution of players by nationality

        Returns:
            Dict of nationality → count

        Example:
            dist = repo.get_nationality_distribution()
            → {'England': 567, 'Brazil': 432, ...}
        """
        self._connect()

        pipeline = [
            {'$group': {'_id': '$nationality', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]

        results = self._collection.aggregate(pipeline)

        return {r['_id']: r['count'] for r in results if r['_id']}

    def get_avg_completeness(self) -> float:
        """
        Get average completeness score across all players

        Returns:
            Average completeness (0.0 to 1.0)

        Example:
            avg = repo.get_avg_completeness()
            → 0.87
        """
        self._connect()

        pipeline = [
            {'$group': {'_id': None, 'avg': {'$avg': '$data_quality.completeness_score'}}}
        ]

        results = list(self._collection.aggregate(pipeline))

        if results:
            return results[0]['avg'] or 0.0

        return 0.0
