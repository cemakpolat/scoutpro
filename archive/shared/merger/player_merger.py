"""
Player Merger

Merges player data from multiple providers into canonical ScoutProPlayer format.
Handles name variations, position mapping, and profile enrichment.
"""

from typing import Optional
from datetime import datetime, date

from shared.domain.models import ScoutProPlayer
from shared.merger.base_merger import BaseMerger


class PlayerMerger(BaseMerger):
    """
    Merges player data from multiple providers

    This merger handles:
    - Name normalization (e.g., 'Mo Salah' vs 'Mohamed Salah')
    - Position standardization
    - Birth date reconciliation
    - Profile enrichment from multiple sources

    Usage:
        merger = PlayerMerger()

        merged_player = merger.merge(
            opta_player,
            statsbomb_player,
            primary_provider='opta',
            secondary_provider='statsbomb'
        )
    """

    def get_entity_type(self) -> str:
        return "player"

    def merge(
        self,
        primary_player: ScoutProPlayer,
        secondary_player: ScoutProPlayer,
        primary_provider: str = 'primary',
        secondary_provider: str = 'secondary'
    ) -> ScoutProPlayer:
        """
        Merge two ScoutProPlayer instances

        Args:
            primary_player: Player from primary provider
            secondary_player: Player from secondary provider
            primary_provider: Primary provider name
            secondary_provider: Secondary provider name

        Returns:
            Merged ScoutProPlayer

        Example:
            opta_player = ScoutProPlayer(
                id='player_opta_12345',
                name='Mohamed Salah',
                position='forward',
                provider='opta'
            )

            sb_player = ScoutProPlayer(
                id='player_sb_98765',
                name='Mo Salah',
                position='right_wing',
                provider='statsbomb'
            )

            merged = merger.merge(opta_player, sb_player, 'opta', 'statsbomb')
        """
        # Use primary player ID as base
        merged_id = primary_player.id

        # Context for conflict logging
        context = {
            'player_id': merged_id,
            'player_name': primary_player.name
        }

        # Merge name fields
        name = self.merge_field(
            'name',
            primary_player.name,
            secondary_player.name,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        first_name = self.merge_field(
            'first_name',
            primary_player.first_name,
            secondary_player.first_name,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        last_name = self.merge_field(
            'last_name',
            primary_player.last_name,
            secondary_player.last_name,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        known_name = self.merge_field(
            'known_name',
            primary_player.known_name,
            secondary_player.known_name,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Birth date
        birth_date = self.merge_field(
            'birth_date',
            primary_player.birth_date,
            secondary_player.birth_date,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Position
        position = self.merge_field(
            'position',
            primary_player.position,
            secondary_player.position,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        detailed_position = self.merge_field(
            'detailed_position',
            primary_player.detailed_position,
            secondary_player.detailed_position,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Nationality
        nationality = self.merge_field(
            'nationality',
            getattr(primary_player, 'nationality', None),
            getattr(secondary_player, 'nationality', None),
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Height/Weight
        height_cm = self.merge_field(
            'height_cm',
            getattr(primary_player, 'height_cm', None),
            getattr(secondary_player, 'height_cm', None),
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        weight_kg = self.merge_field(
            'weight_kg',
            getattr(primary_player, 'weight_kg', None),
            getattr(secondary_player, 'weight_kg', None),
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Preferred foot
        preferred_foot = self.merge_field(
            'preferred_foot',
            getattr(primary_player, 'preferred_foot', None),
            getattr(secondary_player, 'preferred_foot', None),
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Merge provider data
        provider_data = self.merge_provider_data(
            primary_player,
            secondary_player,
            primary_provider,
            secondary_provider
        )

        # Merge provider IDs
        provider_ids = self.merge_provider_ids(
            primary_player,
            secondary_player,
            primary_provider,
            secondary_provider
        )

        # Build quality metadata
        data_quality = self.build_quality_metadata(
            primary_player,
            secondary_player,
            primary_provider,
            secondary_provider
        )

        # Create merged player
        merged_player = ScoutProPlayer(
            id=merged_id,
            external_id=primary_player.external_id,
            provider='canonical',
            name=name,
            first_name=first_name,
            last_name=last_name,
            known_name=known_name,
            birth_date=birth_date,
            position=position,
            detailed_position=detailed_position,
            nationality=nationality,
            height_cm=height_cm,
            weight_kg=weight_kg,
            preferred_foot=preferred_foot,
            provider_ids=provider_ids,
            provider_data=provider_data,
            data_quality=data_quality,
            created_at=primary_player.created_at,
            updated_at=datetime.now()
        )

        return merged_player

    # ========================================
    # PLAYER-SPECIFIC HELPERS
    # ========================================

    def normalize_player_name(self, name: str) -> str:
        """
        Normalize player name for comparison

        Args:
            name: Player name

        Returns:
            Normalized name

        Example:
            normalize_player_name('Mohamed Salah') → 'mohamed salah'
            normalize_player_name('Mo Salah') → 'mo salah'
        """
        return name.lower().strip()

    def are_names_similar(
        self,
        name1: str,
        name2: str,
        threshold: float = 0.8
    ) -> bool:
        """
        Check if two player names are similar

        Uses fuzzy matching to handle:
        - 'Mohamed' vs 'Mohammed'
        - 'Mo Salah' vs 'Mohamed Salah'
        - Different spellings

        Args:
            name1: First name
            name2: Second name
            threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            True if names are similar, False otherwise

        Example:
            are_names_similar('Mohamed Salah', 'Mo Salah') → True
            are_names_similar('Cristiano Ronaldo', 'Lionel Messi') → False
        """
        # Exact match
        if self.normalize_player_name(name1) == self.normalize_player_name(name2):
            return True

        # Check if one name is a substring of the other (common nickname case)
        norm1 = self.normalize_player_name(name1)
        norm2 = self.normalize_player_name(name2)

        if norm1 in norm2 or norm2 in norm1:
            return True

        # TODO: Add Levenshtein distance or other fuzzy matching
        # For now, simple substring matching

        return False
