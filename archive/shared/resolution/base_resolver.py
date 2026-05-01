"""
Base Resolver

Abstract base class for entity resolution across providers.
Entity resolution is the process of determining if two entities from
different providers refer to the same real-world entity.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from difflib import SequenceMatcher


class BaseResolver(ABC):
    """
    Abstract base class for entity resolvers

    Resolvers match entities across providers using:
    - Fuzzy string matching (names, attributes)
    - Exact ID matching (where cross-provider mappings exist)
    - Heuristic rules (e.g., birth dates, positions)
    - Similarity scoring

    Subclasses:
    - PlayerResolver: Matches players across providers
    - TeamResolver: Matches teams across providers
    - MatchResolver: Matches matches across providers
    """

    def __init__(
        self,
        similarity_threshold: float = 0.8,
        confidence_threshold: float = 0.7
    ):
        """
        Initialize resolver

        Args:
            similarity_threshold: Min similarity score to consider match (0.0 to 1.0)
            confidence_threshold: Min confidence to auto-link entities (0.0 to 1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.confidence_threshold = confidence_threshold

    @abstractmethod
    def get_entity_type(self) -> str:
        """Get entity type name"""
        pass

    @abstractmethod
    def resolve(
        self,
        entity1: Any,
        entity2: Any
    ) -> Tuple[bool, float]:
        """
        Determine if two entities are the same

        Args:
            entity1: First entity
            entity2: Second entity

        Returns:
            Tuple of (is_match, confidence_score)
            - is_match: True if entities match
            - confidence_score: Confidence (0.0 to 1.0)
        """
        pass

    @abstractmethod
    def find_match(
        self,
        entity: Any,
        candidates: List[Any]
    ) -> Optional[Tuple[Any, float]]:
        """
        Find best matching entity from candidates

        Args:
            entity: Entity to match
            candidates: List of candidate entities

        Returns:
            Tuple of (matched_entity, confidence) or None if no match found
        """
        pass

    # ========================================
    # STRING SIMILARITY
    # ========================================

    def string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity (0.0 to 1.0)

        Uses SequenceMatcher ratio for fuzzy matching.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score (0.0 to 1.0)

        Example:
            similarity('Mohamed Salah', 'Mo Salah') → 0.85
        """
        if not str1 or not str2:
            return 0.0

        # Normalize strings
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()

        # Exact match
        if str1 == str2:
            return 1.0

        # Use SequenceMatcher
        return SequenceMatcher(None, str1, str2).ratio()

    def name_similarity(
        self,
        name1: str,
        name2: str,
        first_name1: Optional[str] = None,
        last_name1: Optional[str] = None,
        first_name2: Optional[str] = None,
        last_name2: Optional[str] = None
    ) -> float:
        """
        Calculate name similarity with special handling

        Handles:
        - Full name vs nickname ('Mohamed Salah' vs 'Mo Salah')
        - First/last name components
        - Substring matching

        Args:
            name1: Full name 1
            name2: Full name 2
            first_name1: First name 1 (optional)
            last_name1: Last name 1 (optional)
            first_name2: First name 2 (optional)
            last_name2: Last name 2 (optional)

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Full name similarity
        full_name_sim = self.string_similarity(name1, name2)

        # Substring matching (for nicknames)
        norm1 = name1.lower().strip()
        norm2 = name2.lower().strip()

        if norm1 in norm2 or norm2 in norm1:
            full_name_sim = max(full_name_sim, 0.8)

        # If we have component names, compare them
        if first_name1 and first_name2 and last_name1 and last_name2:
            first_sim = self.string_similarity(first_name1, first_name2)
            last_sim = self.string_similarity(last_name1, last_name2)

            # Weighted average (last name more important)
            component_sim = (first_sim * 0.4) + (last_sim * 0.6)

            # Use max of full name similarity and component similarity
            return max(full_name_sim, component_sim)

        return full_name_sim

    # ========================================
    # DATE SIMILARITY
    # ========================================

    def date_similarity(self, date1: Optional[Any], date2: Optional[Any]) -> float:
        """
        Calculate date similarity

        Args:
            date1: First date
            date2: Second date

        Returns:
            Similarity score (0.0 or 1.0)

        Example:
            date_similarity(date(1992, 6, 15), date(1992, 6, 15)) → 1.0
            date_similarity(date(1992, 6, 15), date(1992, 6, 16)) → 0.0
        """
        if date1 is None or date2 is None:
            return 0.0

        # Exact match
        return 1.0 if date1 == date2 else 0.0

    # ========================================
    # SCORING
    # ========================================

    def calculate_weighted_score(
        self,
        scores: Dict[str, float],
        weights: Dict[str, float]
    ) -> float:
        """
        Calculate weighted similarity score

        Args:
            scores: Dict of field → similarity score
            weights: Dict of field → weight

        Returns:
            Weighted average score (0.0 to 1.0)

        Example:
            scores = {'name': 0.9, 'birth_date': 1.0, 'position': 0.8}
            weights = {'name': 0.5, 'birth_date': 0.3, 'position': 0.2}
            calculate_weighted_score(scores, weights) → 0.89
        """
        total_score = 0.0
        total_weight = 0.0

        for field, weight in weights.items():
            if field in scores:
                total_score += scores[field] * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return total_score / total_weight

    def is_match(self, similarity_score: float) -> bool:
        """Check if similarity score indicates a match"""
        return similarity_score >= self.similarity_threshold

    def is_confident(self, confidence_score: float) -> bool:
        """Check if confidence is high enough for auto-linking"""
        return confidence_score >= self.confidence_threshold
