"""
Match Resolver

Matches football matches across different providers.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta

from shared.domain.models import ScoutProMatch
from shared.resolution.base_resolver import BaseResolver


class MatchResolver(BaseResolver):
    """
    Resolves match entities across providers

    Uses multiple signals to match matches:
    - Team IDs (home and away)
    - Match date/time
    - Competition/season
    - Score (if available)

    Weighting:
    - Teams: 50%
    - Date: 30%
    - Competition: 10%
    - Score: 10%

    Usage:
        resolver = MatchResolver()

        # Check if two matches are the same
        is_match, confidence = resolver.resolve(opta_match, sb_match)

        # Find matching match in list
        match, confidence = resolver.find_match(opta_match, sb_matches)
    """

    def __init__(self, date_threshold_hours: int = 24, **kwargs):
        """
        Initialize match resolver

        Args:
            date_threshold_hours: Max time difference (hours) to consider matches the same
            **kwargs: Additional args passed to BaseResolver
        """
        super().__init__(**kwargs)

        self.date_threshold_hours = date_threshold_hours

        # Weights for different matching signals
        self.weights = {
            'teams': 0.5,
            'date': 0.3,
            'competition': 0.1,
            'score': 0.1
        }

    def get_entity_type(self) -> str:
        return "match"

    def resolve(
        self,
        match1: ScoutProMatch,
        match2: ScoutProMatch
    ) -> Tuple[bool, float]:
        """
        Determine if two matches are the same

        Args:
            match1: First match
            match2: Second match

        Returns:
            Tuple of (is_match, confidence_score)

        Example:
            opta_match = ScoutProMatch(
                home_team_id='team_123',
                away_team_id='team_456',
                date=datetime(2023, 10, 28, 15, 0),
                home_score=2,
                away_score=1
            )

            sb_match = ScoutProMatch(
                home_team_id='team_123',
                away_team_id='team_456',
                date=datetime(2023, 10, 28, 15, 0),
                home_score=2,
                away_score=1
            )

            is_match, confidence = resolver.resolve(opta_match, sb_match)
            → (True, 1.0)
        """
        scores = {}

        # Team matching (most important signal)
        scores['teams'] = self._team_match_score(
            match1.home_team_id,
            match1.away_team_id,
            match2.home_team_id,
            match2.away_team_id
        )

        # Date matching
        if match1.date and match2.date:
            scores['date'] = self._date_similarity(match1.date, match2.date)
        else:
            scores['date'] = 0.0

        # Competition matching
        if match1.competition_id and match2.competition_id:
            scores['competition'] = 1.0 if match1.competition_id == match2.competition_id else 0.0
        else:
            scores['competition'] = 0.0

        # Score matching (if available)
        if self._has_score(match1) and self._has_score(match2):
            scores['score'] = self._score_similarity(
                match1.home_score,
                match1.away_score,
                match2.home_score,
                match2.away_score
            )
        else:
            scores['score'] = 0.0

        # Calculate weighted score
        confidence = self.calculate_weighted_score(scores, self.weights)

        # Check if match
        is_match = self.is_match(confidence)

        return is_match, confidence

    def find_match(
        self,
        match: ScoutProMatch,
        candidates: List[ScoutProMatch]
    ) -> Optional[Tuple[ScoutProMatch, float]]:
        """
        Find best matching match from candidates

        Args:
            match: Match to find
            candidates: List of candidate matches

        Returns:
            Tuple of (matched_match, confidence) or None if no match found

        Example:
            opta_match = ScoutProMatch(home_team_id='team_123', ...)
            sb_matches = [
                ScoutProMatch(home_team_id='team_123', ...),
                ScoutProMatch(home_team_id='team_456', ...),
                ...
            ]

            match, confidence = resolver.find_match(opta_match, sb_matches)
        """
        best_match = None
        best_confidence = 0.0

        for candidate in candidates:
            is_match, confidence = self.resolve(match, candidate)

            if is_match and confidence > best_confidence:
                best_match = candidate
                best_confidence = confidence

        if best_match and best_confidence >= self.similarity_threshold:
            return (best_match, best_confidence)

        return None

    # ========================================
    # MATCH-SPECIFIC MATCHING
    # ========================================

    def _team_match_score(
        self,
        home1: str,
        away1: str,
        home2: str,
        away2: str
    ) -> float:
        """
        Calculate team matching score

        Both home and away teams must match.

        Args:
            home1: Home team 1
            away1: Away team 1
            home2: Home team 2
            away2: Away team 2

        Returns:
            Score (0.0 to 1.0)
        """
        if not home1 or not away1 or not home2 or not away2:
            return 0.0

        # Both teams must match
        home_match = (home1 == home2)
        away_match = (away1 == away2)

        if home_match and away_match:
            return 1.0

        return 0.0

    def _date_similarity(self, date1: datetime, date2: datetime) -> float:
        """
        Calculate date similarity

        Matches are considered similar if dates are within threshold.

        Args:
            date1: Date 1
            date2: Date 2

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not date1 or not date2:
            return 0.0

        # Calculate time difference
        time_diff = abs((date1 - date2).total_seconds())
        threshold_seconds = self.date_threshold_hours * 3600

        if time_diff == 0:
            return 1.0
        elif time_diff <= threshold_seconds:
            # Linear decay within threshold
            return 1.0 - (time_diff / threshold_seconds)
        else:
            return 0.0

    def _score_similarity(
        self,
        home_score1: Optional[int],
        away_score1: Optional[int],
        home_score2: Optional[int],
        away_score2: Optional[int]
    ) -> float:
        """
        Calculate score similarity

        Args:
            home_score1: Home score 1
            away_score1: Away score 1
            home_score2: Home score 2
            away_score2: Away score 2

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if home_score1 is None or away_score1 is None or home_score2 is None or away_score2 is None:
            return 0.0

        # Exact score match
        if home_score1 == home_score2 and away_score1 == away_score2:
            return 1.0

        # Same result (win/draw/loss) but different score
        result1 = self._get_result(home_score1, away_score1)
        result2 = self._get_result(home_score2, away_score2)

        if result1 == result2:
            return 0.5  # Partial match

        return 0.0

    def _get_result(self, home_score: int, away_score: int) -> str:
        """Get match result (home_win, away_win, draw)"""
        if home_score > away_score:
            return 'home_win'
        elif away_score > home_score:
            return 'away_win'
        else:
            return 'draw'

    def _has_score(self, match: ScoutProMatch) -> bool:
        """Check if match has score data"""
        return match.home_score is not None and match.away_score is not None

    def resolve_bulk(
        self,
        matches1: List[ScoutProMatch],
        matches2: List[ScoutProMatch]
    ) -> List[Tuple[ScoutProMatch, Optional[ScoutProMatch], float]]:
        """
        Resolve multiple matches at once

        Args:
            matches1: List of matches from provider 1
            matches2: List of matches from provider 2

        Returns:
            List of tuples: (match1, matched_match2, confidence)
            - matched_match2 is None if no match found

        Example:
            matches = resolver.resolve_bulk(opta_matches, sb_matches)
            for match1, match2, confidence in matches:
                if match2:
                    print(f"Match resolved ({confidence:.2f})")
        """
        results = []

        for match1 in matches1:
            match_result = self.find_match(match1, matches2)

            if match_result:
                matched_match, confidence = match_result
                results.append((match1, matched_match, confidence))
            else:
                results.append((match1, None, 0.0))

        return results
