"""
Player Resolver

Matches players across different providers using fuzzy matching.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import date

from shared.domain.models import ScoutProPlayer
from shared.resolution.base_resolver import BaseResolver


class PlayerResolver(BaseResolver):
    """
    Resolves player entities across providers

    Uses multiple signals to match players:
    - Name similarity (full name, first/last name, known name)
    - Birth date match
    - Position similarity
    - Nationality match

    Weighting:
    - Name: 50%
    - Birth date: 30%
    - Position: 10%
    - Nationality: 10%

    Usage:
        resolver = PlayerResolver()

        # Check if two players are the same
        is_match, confidence = resolver.resolve(opta_player, sb_player)

        # Find matching player in list
        match, confidence = resolver.find_match(opta_player, sb_players)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Weights for different matching signals
        self.weights = {
            'name': 0.5,
            'birth_date': 0.3,
            'position': 0.1,
            'nationality': 0.1
        }

    def get_entity_type(self) -> str:
        return "player"

    def resolve(
        self,
        player1: ScoutProPlayer,
        player2: ScoutProPlayer
    ) -> Tuple[bool, float]:
        """
        Determine if two players are the same

        Args:
            player1: First player
            player2: Second player

        Returns:
            Tuple of (is_match, confidence_score)

        Example:
            opta_player = ScoutProPlayer(
                name='Mohamed Salah',
                first_name='Mohamed',
                last_name='Salah',
                birth_date=date(1992, 6, 15),
                position='forward'
            )

            sb_player = ScoutProPlayer(
                name='Mo Salah',
                first_name='Mo',
                last_name='Salah',
                birth_date=date(1992, 6, 15),
                position='right_wing'
            )

            is_match, confidence = resolver.resolve(opta_player, sb_player)
            → (True, 0.92)
        """
        scores = {}

        # Name similarity
        scores['name'] = self.name_similarity(
            player1.name,
            player2.name,
            player1.first_name,
            player1.last_name,
            player2.first_name,
            player2.last_name
        )

        # Birth date similarity
        if player1.birth_date and player2.birth_date:
            scores['birth_date'] = self.date_similarity(player1.birth_date, player2.birth_date)
        else:
            scores['birth_date'] = 0.0

        # Position similarity
        if player1.position and player2.position:
            scores['position'] = self._position_similarity(player1.position, player2.position)
        else:
            scores['position'] = 0.0

        # Nationality similarity
        if player1.nationality and player2.nationality:
            scores['nationality'] = 1.0 if player1.nationality == player2.nationality else 0.0
        else:
            scores['nationality'] = 0.0

        # Calculate weighted score
        confidence = self.calculate_weighted_score(scores, self.weights)

        # Check if match
        is_match = self.is_match(confidence)

        return is_match, confidence

    def find_match(
        self,
        player: ScoutProPlayer,
        candidates: List[ScoutProPlayer]
    ) -> Optional[Tuple[ScoutProPlayer, float]]:
        """
        Find best matching player from candidates

        Args:
            player: Player to match
            candidates: List of candidate players

        Returns:
            Tuple of (matched_player, confidence) or None if no match found

        Example:
            opta_player = ScoutProPlayer(name='Mohamed Salah', ...)
            sb_players = [
                ScoutProPlayer(name='Mo Salah', ...),
                ScoutProPlayer(name='Sadio Mane', ...),
                ...
            ]

            match, confidence = resolver.find_match(opta_player, sb_players)
            → (ScoutProPlayer(name='Mo Salah'), 0.92)
        """
        best_match = None
        best_confidence = 0.0

        for candidate in candidates:
            is_match, confidence = self.resolve(player, candidate)

            if is_match and confidence > best_confidence:
                best_match = candidate
                best_confidence = confidence

        if best_match and best_confidence >= self.similarity_threshold:
            return (best_match, best_confidence)

        return None

    # ========================================
    # PLAYER-SPECIFIC MATCHING
    # ========================================

    def _position_similarity(self, pos1: str, pos2: str) -> float:
        """
        Calculate position similarity

        Handles position families:
        - Forward family: 'forward', 'striker', 'center_forward', 'right_wing', 'left_wing'
        - Midfield family: 'midfielder', 'attacking_midfielder', 'defensive_midfielder', etc.
        - Defense family: 'defender', 'center_back', 'left_back', 'right_back'
        - Goalkeeper: 'goalkeeper'

        Args:
            pos1: Position 1
            pos2: Position 2

        Returns:
            Similarity score (0.0 to 1.0)

        Example:
            _position_similarity('forward', 'right_wing') → 0.8
            _position_similarity('forward', 'goalkeeper') → 0.0
        """
        if not pos1 or not pos2:
            return 0.0

        # Exact match
        if pos1.lower() == pos2.lower():
            return 1.0

        # Position families
        position_families = {
            'forward': ['forward', 'striker', 'center_forward', 'right_wing', 'left_wing', 'winger', 'attacker'],
            'midfielder': ['midfielder', 'midfield', 'attacking_midfielder', 'defensive_midfielder', 'central_midfielder', 'wide_midfielder'],
            'defender': ['defender', 'defense', 'center_back', 'left_back', 'right_back', 'full_back', 'wing_back'],
            'goalkeeper': ['goalkeeper', 'goalie', 'gk']
        }

        # Find which family each position belongs to
        family1 = None
        family2 = None

        for family, positions in position_families.items():
            if any(p in pos1.lower() for p in positions):
                family1 = family
            if any(p in pos2.lower() for p in positions):
                family2 = family

        if family1 == family2 and family1 is not None:
            # Same family - high similarity
            return 0.8

        # Different families
        return 0.0

    def resolve_bulk(
        self,
        players1: List[ScoutProPlayer],
        players2: List[ScoutProPlayer]
    ) -> List[Tuple[ScoutProPlayer, Optional[ScoutProPlayer], float]]:
        """
        Resolve multiple players at once

        Args:
            players1: List of players from provider 1
            players2: List of players from provider 2

        Returns:
            List of tuples: (player1, matched_player2, confidence)
            - matched_player2 is None if no match found

        Example:
            matches = resolver.resolve_bulk(opta_players, sb_players)
            for player1, player2, confidence in matches:
                if player2:
                    print(f"{player1.name} → {player2.name} ({confidence:.2f})")
        """
        results = []

        for player1 in players1:
            match_result = self.find_match(player1, players2)

            if match_result:
                matched_player, confidence = match_result
                results.append((player1, matched_player, confidence))
            else:
                results.append((player1, None, 0.0))

        return results
