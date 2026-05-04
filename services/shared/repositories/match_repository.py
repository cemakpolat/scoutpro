"""
Match Repository

Repository for storing and retrieving match data from MongoDB.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo import ASCENDING, DESCENDING

from shared.domain.models import ScoutProMatch, MatchStatus
from shared.repositories.base_repository import BaseRepository


class MatchRepository(BaseRepository[ScoutProMatch]):
    """
    Repository for match entities

    Provides:
    - CRUD operations for matches
    - Filter by team, competition, season, date
    - Provider ID lookups
    - Status queries

    Usage:
        repo = MatchRepository()

        # Create match
        match = ScoutProMatch(...)
        repo.create(match)

        # Find by ID
        match = repo.find_by_id('match_123')

        # Find by provider ID
        match = repo.find_by_provider_id('opta', 'g2187923')

        # Find by team
        matches = repo.find_by_team('team_123')

        # Find by competition
        matches = repo.find_by_competition('8', '2023')
    """

    def get_collection_name(self) -> str:
        return "matches"

    def create_indexes(self):
        """Create MongoDB indexes for match collection"""
        if self._collection is None:
            return

        # Provider IDs (for lookups)
        self._collection.create_index([('provider_ids.opta', ASCENDING)])
        self._collection.create_index([('provider_ids.statsbomb', ASCENDING)])
        self._collection.create_index([('provider_ids.wyscout', ASCENDING)])

        # Team indexes (for filtering by team)
        self._collection.create_index([('home_team_id', ASCENDING)])
        self._collection.create_index([('away_team_id', ASCENDING)])

        # Competition/Season (for filtering)
        self._collection.create_index([('competition_id', ASCENDING), ('season_id', ASCENDING)])

        # Date index (for range queries)
        self._collection.create_index([('date', DESCENDING)])

        # Status index (for filtering by status)
        self._collection.create_index([('status', ASCENDING)])

        # Compound index for team + date queries
        self._collection.create_index([('home_team_id', ASCENDING), ('date', DESCENDING)])
        self._collection.create_index([('away_team_id', ASCENDING), ('date', DESCENDING)])

        # Updated timestamp (for sync)
        self._collection.create_index([('updated_at', ASCENDING)])

    def to_document(self, match: ScoutProMatch) -> Dict[str, Any]:
        """
        Convert ScoutProMatch to MongoDB document

        Args:
            match: Match to convert

        Returns:
            MongoDB document
        """
        doc = {
            '_id': match.id,
            'uID': (match.provider_ids or {}).get('opta') or match.external_id,
            'external_id': match.external_id,
            'provider': match.provider,
            'homeTeamID': match.home_team_id,
            'awayTeamID': match.away_team_id,
            'home_team_id': match.home_team_id,
            'away_team_id': match.away_team_id,
            'competitionID': match.competition_id,
            'seasonID': match.season_id,
            'competition_id': match.competition_id,
            'season_id': match.season_id,
            'homeScore': match.home_score,
            'awayScore': match.away_score,
            'date': match.date,
            'status': match.status.value if isinstance(match.status, MatchStatus) else match.status,
            'home_score': match.home_score,
            'away_score': match.away_score,
            'venue': match.venue,
            'attendance': match.attendance,
            'referee': match.referee,
            'provider_ids': match.provider_ids or {},
            'provider_data': match.provider_data or {},
            'data_quality': match.data_quality or {},
            'created_at': match.created_at,
            'updated_at': match.updated_at
        }

        return doc

    def from_document(self, doc: Dict[str, Any]) -> ScoutProMatch:
        """
        Convert MongoDB document to ScoutProMatch

        Args:
            doc: MongoDB document

        Returns:
            ScoutProMatch instance
        """
        # Parse status
        status_val = doc.get('status', MatchStatus.SCHEDULED.value)
        if isinstance(status_val, str):
            try:
                status = MatchStatus(status_val)
            except ValueError:
                status = MatchStatus.SCHEDULED
        else:
            status = status_val

        match = ScoutProMatch(
            id=doc['_id'],
            external_id=doc.get('external_id'),
            provider=doc.get('provider', 'canonical'),
            home_team_id=doc.get('home_team_id', 0),
            away_team_id=doc.get('away_team_id', 0),
            competition_id=doc.get('competition_id', 0),
            season_id=doc.get('season_id', 0),
            date=doc.get('date'),
            status=status,
            home_score=doc.get('home_score'),
            away_score=doc.get('away_score'),
            venue=doc.get('venue'),
            attendance=doc.get('attendance'),
            referee=doc.get('referee'),
            provider_ids=doc.get('provider_ids', {}),
            provider_data=doc.get('provider_data', {}),
            data_quality=doc.get('data_quality', {}),
            created_at=doc.get('created_at', datetime.now()),
            updated_at=doc.get('updated_at', datetime.now())
        )

        return match

    # ========================================
    # MATCH-SPECIFIC QUERIES
    # ========================================

    def find_by_team(
        self,
        team_id: str,
        limit: Optional[int] = None
    ) -> List[ScoutProMatch]:
        """
        Find all matches for a team (home or away)

        Args:
            team_id: Team ID
            limit: Max results

        Returns:
            List of matches

        Example:
            matches = repo.find_by_team('team_123', limit=20)
        """
        query = {
            '$or': [
                {'home_team_id': team_id},
                {'away_team_id': team_id}
            ]
        }

        return self.find(query, limit=limit, sort=[('date', DESCENDING)])

    def find_by_teams(
        self,
        team1_id: str,
        team2_id: str,
        limit: Optional[int] = None
    ) -> List[ScoutProMatch]:
        """
        Find matches between two specific teams

        Args:
            team1_id: First team ID
            team2_id: Second team ID
            limit: Max results

        Returns:
            List of matches

        Example:
            # Find Liverpool vs Manchester United matches
            matches = repo.find_by_teams('team_liv', 'team_manu')
        """
        query = {
            '$or': [
                {'home_team_id': team1_id, 'away_team_id': team2_id},
                {'home_team_id': team2_id, 'away_team_id': team1_id}
            ]
        }

        return self.find(query, limit=limit, sort=[('date', DESCENDING)])

    def find_by_competition(
        self,
        competition_id: str,
        season_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ScoutProMatch]:
        """
        Find matches in a competition

        Args:
            competition_id: Competition ID
            season_id: Season ID (optional)
            limit: Max results

        Returns:
            List of matches

        Example:
            # Find all Premier League 2023 matches
            matches = repo.find_by_competition('8', '2023')
        """
        query = {'competition_id': competition_id}

        if season_id:
            query['season_id'] = season_id

        return self.find(query, limit=limit, sort=[('date', DESCENDING)])

    def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: Optional[int] = None
    ) -> List[ScoutProMatch]:
        """
        Find matches in a date range

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Max results

        Returns:
            List of matches

        Example:
            from datetime import datetime
            start = datetime(2023, 10, 1)
            end = datetime(2023, 10, 31)
            october_matches = repo.find_by_date_range(start, end)
        """
        query = {
            'date': {
                '$gte': start_date,
                '$lte': end_date
            }
        }

        return self.find(query, limit=limit, sort=[('date', DESCENDING)])

    def find_by_status(
        self,
        status: MatchStatus,
        limit: Optional[int] = None
    ) -> List[ScoutProMatch]:
        """
        Find matches by status

        Args:
            status: Match status (SCHEDULED, LIVE, FINISHED, etc.)
            limit: Max results

        Returns:
            List of matches

        Example:
            live_matches = repo.find_by_status(MatchStatus.LIVE)
        """
        query = {'status': status.value}

        return self.find(query, limit=limit, sort=[('date', DESCENDING)])

    def find_recent(self, limit: int = 100) -> List[ScoutProMatch]:
        """
        Find recent matches (by date)

        Args:
            limit: Max results

        Returns:
            List of matches sorted by date descending

        Example:
            recent = repo.find_recent(limit=50)
        """
        return self.find(
            {},
            limit=limit,
            sort=[('date', DESCENDING)]
        )

    def find_upcoming(self, limit: int = 100) -> List[ScoutProMatch]:
        """
        Find upcoming matches (future dates, scheduled status)

        Args:
            limit: Max results

        Returns:
            List of upcoming matches

        Example:
            upcoming = repo.find_upcoming(limit=20)
        """
        query = {
            'date': {'$gte': datetime.now()},
            'status': MatchStatus.SCHEDULED.value
        }

        return self.find(query, limit=limit, sort=[('date', ASCENDING)])

    def find_by_provider(
        self,
        provider: str,
        limit: Optional[int] = None
    ) -> List[ScoutProMatch]:
        """
        Find all matches from a specific provider

        Args:
            provider: Provider name ('opta', 'statsbomb', 'canonical')
            limit: Max results

        Returns:
            List of matches

        Example:
            opta_matches = repo.find_by_provider('opta')
        """
        return self.find({'provider': provider}, limit=limit)

    def find_canonical_matches(self, limit: Optional[int] = None) -> List[ScoutProMatch]:
        """
        Find all canonical (merged) matches

        Args:
            limit: Max results

        Returns:
            List of canonical matches

        Example:
            canonical = repo.find_canonical_matches()
        """
        return self.find_by_provider('canonical', limit=limit)

    # ========================================
    # AGGREGATION QUERIES
    # ========================================

    def get_competition_stats(self, competition_id: str, season_id: str) -> Dict[str, Any]:
        """
        Get statistics for a competition/season

        Args:
            competition_id: Competition ID
            season_id: Season ID

        Returns:
            Dict with competition stats

        Example:
            stats = repo.get_competition_stats('8', '2023')
            → {
                'total_matches': 380,
                'completed': 200,
                'avg_home_score': 1.5,
                'avg_away_score': 1.2
            }
        """
        self._connect()

        query = {
            'competition_id': competition_id,
            'season_id': season_id
        }

        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': None,
                'total_matches': {'$sum': 1},
                'completed': {
                    '$sum': {
                        '$cond': [{'$eq': ['$status', MatchStatus.FINISHED.value]}, 1, 0]
                    }
                },
                'avg_home_score': {'$avg': '$home_score'},
                'avg_away_score': {'$avg': '$away_score'}
            }}
        ]

        results = list(self._collection.aggregate(pipeline))

        if results:
            stats = results[0]
            del stats['_id']
            return stats

        return {}

    def get_team_stats(self, team_id: str) -> Dict[str, Any]:
        """
        Get statistics for a team

        Args:
            team_id: Team ID

        Returns:
            Dict with team stats

        Example:
            stats = repo.get_team_stats('team_123')
            → {
                'total_matches': 38,
                'home_matches': 19,
                'away_matches': 19,
                'wins': 25,
                'draws': 8,
                'losses': 5
            }
        """
        self._connect()

        # Get all matches for team
        matches = self.find_by_team(team_id)

        total = len(matches)
        home = sum(1 for m in matches if m.home_team_id == team_id)
        away = total - home

        # Calculate wins/draws/losses
        wins = 0
        draws = 0
        losses = 0

        for match in matches:
            if match.home_score is None or match.away_score is None:
                continue

            if match.home_team_id == team_id:
                # Team is home
                if match.home_score > match.away_score:
                    wins += 1
                elif match.home_score == match.away_score:
                    draws += 1
                else:
                    losses += 1
            else:
                # Team is away
                if match.away_score > match.home_score:
                    wins += 1
                elif match.away_score == match.home_score:
                    draws += 1
                else:
                    losses += 1

        return {
            'total_matches': total,
            'home_matches': home,
            'away_matches': away,
            'wins': wins,
            'draws': draws,
            'losses': losses
        }
