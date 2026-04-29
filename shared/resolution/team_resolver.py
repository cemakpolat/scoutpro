"""
Team Resolver

Matches teams across different providers using fuzzy matching.
"""

from typing import List, Optional, Tuple, Dict, Any

from shared.domain.models import ScoutProTeam
from shared.resolution.base_resolver import BaseResolver


class TeamResolver(BaseResolver):
    """
    Resolves team entities across providers

    Uses multiple signals to match teams:
    - Team name similarity (handles 'Liverpool' vs 'Liverpool FC')
    - Short name/code match
    - Country match
    - Stadium match

    Weighting:
    - Name: 70%
    - Country: 20%
    - Stadium: 10%

    Usage:
        resolver = TeamResolver()

        # Check if two teams are the same
        is_match, confidence = resolver.resolve(opta_team, sb_team)

        # Find matching team in list
        match, confidence = resolver.find_match(opta_team, sb_teams)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Weights for different matching signals
        self.weights = {
            'name': 0.7,
            'country': 0.2,
            'stadium': 0.1
        }

    def get_entity_type(self) -> str:
        return "team"

    def resolve(
        self,
        team1: ScoutProTeam,
        team2: ScoutProTeam
    ) -> Tuple[bool, float]:
        """
        Determine if two teams are the same

        Args:
            team1: First team
            team2: Second team

        Returns:
            Tuple of (is_match, confidence_score)

        Example:
            opta_team = ScoutProTeam(
                name='Liverpool',
                short_name='LIV',
                country='England'
            )

            sb_team = ScoutProTeam(
                name='Liverpool FC',
                short_name='Liverpool',
                country='England'
            )

            is_match, confidence = resolver.resolve(opta_team, sb_team)
            → (True, 0.95)
        """
        scores = {}

        # Name similarity
        scores['name'] = self._team_name_similarity(
            team1.name,
            team1.short_name,
            team2.name,
            team2.short_name
        )

        # Country match
        if team1.country and team2.country:
            scores['country'] = 1.0 if team1.country.lower() == team2.country.lower() else 0.0
        else:
            scores['country'] = 0.0

        # Stadium match
        if team1.stadium and team2.stadium:
            scores['stadium'] = self.string_similarity(team1.stadium, team2.stadium)
        else:
            scores['stadium'] = 0.0

        # Calculate weighted score
        confidence = self.calculate_weighted_score(scores, self.weights)

        # Check if match
        is_match = self.is_match(confidence)

        return is_match, confidence

    def find_match(
        self,
        team: ScoutProTeam,
        candidates: List[ScoutProTeam]
    ) -> Optional[Tuple[ScoutProTeam, float]]:
        """
        Find best matching team from candidates

        Args:
            team: Team to match
            candidates: List of candidate teams

        Returns:
            Tuple of (matched_team, confidence) or None if no match found

        Example:
            opta_team = ScoutProTeam(name='Liverpool', ...)
            sb_teams = [
                ScoutProTeam(name='Liverpool FC', ...),
                ScoutProTeam(name='Manchester United', ...),
                ...
            ]

            match, confidence = resolver.find_match(opta_team, sb_teams)
            → (ScoutProTeam(name='Liverpool FC'), 0.95)
        """
        best_match = None
        best_confidence = 0.0

        for candidate in candidates:
            is_match, confidence = self.resolve(team, candidate)

            if is_match and confidence > best_confidence:
                best_match = candidate
                best_confidence = confidence

        if best_match and best_confidence >= self.similarity_threshold:
            return (best_match, best_confidence)

        return None

    # ========================================
    # TEAM-SPECIFIC MATCHING
    # ========================================

    def _team_name_similarity(
        self,
        name1: str,
        short_name1: Optional[str],
        name2: str,
        short_name2: Optional[str]
    ) -> float:
        """
        Calculate team name similarity

        Handles common team name variations:
        - 'Liverpool' vs 'Liverpool FC'
        - 'Man United' vs 'Manchester United'
        - Short names: 'LIV', 'MUN', etc.

        Args:
            name1: Full name 1
            short_name1: Short name 1
            name2: Full name 2
            short_name2: Short name 2

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize names
        norm_name1 = self._normalize_team_name(name1)
        norm_name2 = self._normalize_team_name(name2)

        # Full name similarity
        name_sim = self.string_similarity(norm_name1, norm_name2)

        # Check substring matching (for 'Liverpool' vs 'Liverpool FC')
        if norm_name1 in norm_name2 or norm_name2 in norm_name1:
            name_sim = max(name_sim, 0.9)

        # Short name matching
        if short_name1 and short_name2:
            short_sim = self.string_similarity(short_name1, short_name2)
            # If short names match well, boost score
            if short_sim > 0.8:
                name_sim = max(name_sim, short_sim)

        return name_sim

    def _normalize_team_name(self, name: str) -> str:
        """
        Normalize team name for comparison

        Removes common suffixes and handles abbreviations.

        Args:
            name: Team name

        Returns:
            Normalized name

        Example:
            _normalize_team_name('Liverpool FC') → 'liverpool'
            _normalize_team_name('Man United') → 'manchester united'
        """
        if not name:
            return ''

        # Remove common suffixes
        suffixes_to_remove = [
            ' FC', ' CF', ' AFC', ' BFC', ' United', ' City',
            ' Rovers', ' Wanderers', ' Town', ' Athletic'
        ]

        normalized = name
        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]

        # Handle common abbreviations
        abbreviations = {
            'Man United': 'Manchester United',
            'Man City': 'Manchester City',
            'Spurs': 'Tottenham Hotspur',
            'Wolves': 'Wolverhampton Wanderers',
        }

        if name in abbreviations:
            normalized = abbreviations[name]

        return normalized.lower().strip()

    def resolve_bulk(
        self,
        teams1: List[ScoutProTeam],
        teams2: List[ScoutProTeam]
    ) -> List[Tuple[ScoutProTeam, Optional[ScoutProTeam], float]]:
        """
        Resolve multiple teams at once

        Args:
            teams1: List of teams from provider 1
            teams2: List of teams from provider 2

        Returns:
            List of tuples: (team1, matched_team2, confidence)
            - matched_team2 is None if no match found

        Example:
            matches = resolver.resolve_bulk(opta_teams, sb_teams)
            for team1, team2, confidence in matches:
                if team2:
                    print(f"{team1.name} → {team2.name} ({confidence:.2f})")
        """
        results = []

        for team1 in teams1:
            match_result = self.find_match(team1, teams2)

            if match_result:
                matched_team, confidence = match_result
                results.append((team1, matched_team, confidence))
            else:
                results.append((team1, None, 0.0))

        return results
