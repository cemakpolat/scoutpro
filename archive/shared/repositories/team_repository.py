"""
Team Repository

Repository for storing and retrieving team data from MongoDB.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo import ASCENDING, TEXT

from shared.domain.models import ScoutProTeam
from shared.repositories.base_repository import BaseRepository


class TeamRepository(BaseRepository[ScoutProTeam]):
    """
    Repository for team entities

    Provides:
    - CRUD operations for teams
    - Search by name
    - Filter by country, league
    - Provider ID lookups

    Usage:
        repo = TeamRepository()

        # Create team
        team = ScoutProTeam(...)
        repo.create(team)

        # Find by ID
        team = repo.find_by_id('team_123')

        # Find by provider ID
        team = repo.find_by_provider_id('opta', 't14')

        # Search by name
        teams = repo.search_by_name('Liverpool')

        # Find by country
        english_teams = repo.find_by_country('England')
    """

    def get_collection_name(self) -> str:
        return "teams"

    def create_indexes(self):
        """Create MongoDB indexes for team collection"""
        if self._collection is None:
            return

        # Name index (for searching)
        self._collection.create_index([('name', TEXT)])

        # Provider IDs (for lookups)
        self._collection.create_index([('provider_ids.opta', ASCENDING)])
        self._collection.create_index([('provider_ids.statsbomb', ASCENDING)])
        self._collection.create_index([('provider_ids.wyscout', ASCENDING)])

        # Country index (for filtering)
        self._collection.create_index([('country', ASCENDING)])

        # League index (for filtering)
        self._collection.create_index([('league', ASCENDING)])

        # Short name index (for lookups)
        self._collection.create_index([('short_name', ASCENDING)])

        # Updated timestamp (for sync)
        self._collection.create_index([('updated_at', ASCENDING)])

    def to_document(self, team: ScoutProTeam) -> Dict[str, Any]:
        """
        Convert ScoutProTeam to MongoDB document

        Args:
            team: Team to convert

        Returns:
            MongoDB document
        """
        doc = {
            '_id': team.id,
            'external_id': team.external_id,
            'provider': team.provider,
            'name': team.name,
            'short_name': team.short_name,
            'code': team.code,
            'country': team.country,
            'league': team.league,
            'stadium': team.stadium,
            'founded': team.founded,
            'provider_ids': team.provider_ids or {},
            'provider_data': team.provider_data or {},
            'data_quality': team.data_quality or {},
            'created_at': team.created_at,
            'updated_at': team.updated_at
        }

        return doc

    def from_document(self, doc: Dict[str, Any]) -> ScoutProTeam:
        """
        Convert MongoDB document to ScoutProTeam

        Args:
            doc: MongoDB document

        Returns:
            ScoutProTeam instance
        """
        team = ScoutProTeam(
            id=doc['_id'],
            external_id=doc.get('external_id'),
            provider=doc.get('provider', 'canonical'),
            name=doc.get('name', ''),
            short_name=doc.get('short_name'),
            code=doc.get('code'),
            country=doc.get('country'),
            league=doc.get('league'),
            stadium=doc.get('stadium'),
            founded=doc.get('founded'),
            provider_ids=doc.get('provider_ids', {}),
            provider_data=doc.get('provider_data', {}),
            data_quality=doc.get('data_quality', {}),
            created_at=doc.get('created_at', datetime.now()),
            updated_at=doc.get('updated_at', datetime.now())
        )

        return team

    # ========================================
    # TEAM-SPECIFIC QUERIES
    # ========================================

    def search_by_name(
        self,
        name: str,
        limit: int = 20
    ) -> List[ScoutProTeam]:
        """
        Search teams by name (fuzzy text search)

        Args:
            name: Name to search for
            limit: Max results

        Returns:
            List of matching teams

        Example:
            teams = repo.search_by_name('Liverpool')
            → [ScoutProTeam(name='Liverpool'), ScoutProTeam(name='Liverpool FC'), ...]
        """
        self._connect()

        # Use MongoDB text search
        query = {'$text': {'$search': name}}

        return self.find(query, limit=limit)

    def find_by_name_exact(self, name: str) -> Optional[ScoutProTeam]:
        """
        Find team by exact name match

        Args:
            name: Full name

        Returns:
            Team or None

        Example:
            team = repo.find_by_name_exact('Liverpool')
        """
        return self.find_one({'name': name})

    def find_by_short_name(self, short_name: str) -> Optional[ScoutProTeam]:
        """
        Find team by short name

        Args:
            short_name: Short name (e.g., 'LIV')

        Returns:
            Team or None

        Example:
            team = repo.find_by_short_name('LIV')
        """
        return self.find_one({'short_name': short_name})

    def find_by_country(
        self,
        country: str,
        limit: Optional[int] = None
    ) -> List[ScoutProTeam]:
        """
        Find teams by country

        Args:
            country: Country name (e.g., 'England', 'Spain')
            limit: Max results

        Returns:
            List of teams

        Example:
            english_teams = repo.find_by_country('England')
        """
        return self.find({'country': country}, limit=limit)

    def find_by_league(
        self,
        league: str,
        limit: Optional[int] = None
    ) -> List[ScoutProTeam]:
        """
        Find teams by league

        Args:
            league: League name (e.g., 'Premier League', 'La Liga')
            limit: Max results

        Returns:
            List of teams

        Example:
            pl_teams = repo.find_by_league('Premier League')
        """
        return self.find({'league': league}, limit=limit)

    def find_recent(self, limit: int = 100) -> List[ScoutProTeam]:
        """
        Find recently updated teams

        Args:
            limit: Max results

        Returns:
            List of teams sorted by updated_at descending

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
    ) -> List[ScoutProTeam]:
        """
        Find all teams from a specific provider

        Args:
            provider: Provider name ('opta', 'statsbomb', 'canonical')
            limit: Max results

        Returns:
            List of teams

        Example:
            opta_teams = repo.find_by_provider('opta')
        """
        return self.find({'provider': provider}, limit=limit)

    def find_canonical_teams(self, limit: Optional[int] = None) -> List[ScoutProTeam]:
        """
        Find all canonical (merged) teams

        Args:
            limit: Max results

        Returns:
            List of canonical teams

        Example:
            canonical = repo.find_canonical_teams()
        """
        return self.find_by_provider('canonical', limit=limit)

    # ========================================
    # AGGREGATION QUERIES
    # ========================================

    def get_country_distribution(self) -> Dict[str, int]:
        """
        Get distribution of teams by country

        Returns:
            Dict of country → count

        Example:
            dist = repo.get_country_distribution()
            → {'England': 20, 'Spain': 20, 'Germany': 18, ...}
        """
        self._connect()

        pipeline = [
            {'$group': {'_id': '$country', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]

        results = self._collection.aggregate(pipeline)

        return {r['_id']: r['count'] for r in results if r['_id']}

    def get_league_distribution(self) -> Dict[str, int]:
        """
        Get distribution of teams by league

        Returns:
            Dict of league → count

        Example:
            dist = repo.get_league_distribution()
            → {'Premier League': 20, 'La Liga': 20, ...}
        """
        self._connect()

        pipeline = [
            {'$group': {'_id': '$league', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]

        results = self._collection.aggregate(pipeline)

        return {r['_id']: r['count'] for r in results if r['_id']}
