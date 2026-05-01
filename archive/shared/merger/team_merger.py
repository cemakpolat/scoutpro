"""
Team Merger

Merges team data from multiple providers into canonical ScoutProTeam format.
Handles name variations, stadium info, and squad enrichment.
"""

from typing import Optional
from datetime import datetime

from shared.domain.models import ScoutProTeam
from shared.merger.base_merger import BaseMerger


class TeamMerger(BaseMerger):
    """
    Merges team data from multiple providers

    This merger handles:
    - Team name normalization (e.g., 'Liverpool' vs 'Liverpool FC')
    - Short name/code mapping
    - Stadium information
    - Country/league information

    Usage:
        merger = TeamMerger()

        merged_team = merger.merge(
            opta_team,
            statsbomb_team,
            primary_provider='opta',
            secondary_provider='statsbomb'
        )
    """

    def get_entity_type(self) -> str:
        return "team"

    def merge(
        self,
        primary_team: ScoutProTeam,
        secondary_team: ScoutProTeam,
        primary_provider: str = 'primary',
        secondary_provider: str = 'secondary'
    ) -> ScoutProTeam:
        """
        Merge two ScoutProTeam instances

        Args:
            primary_team: Team from primary provider
            secondary_team: Team from secondary provider
            primary_provider: Primary provider name
            secondary_provider: Secondary provider name

        Returns:
            Merged ScoutProTeam

        Example:
            opta_team = ScoutProTeam(
                id='team_opta_14',
                name='Liverpool',
                country='England',
                provider='opta'
            )

            sb_team = ScoutProTeam(
                id='team_sb_123',
                name='Liverpool FC',
                country='England',
                provider='statsbomb'
            )

            merged = merger.merge(opta_team, sb_team, 'opta', 'statsbomb')
        """
        # Use primary team ID as base
        merged_id = primary_team.id

        # Context for conflict logging
        context = {
            'team_id': merged_id,
            'team_name': primary_team.name
        }

        # Merge name fields
        name = self.merge_field(
            'name',
            primary_team.name,
            secondary_team.name,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        short_name = self.merge_field(
            'short_name',
            primary_team.short_name,
            secondary_team.short_name,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        code = self.merge_field(
            'code',
            getattr(primary_team, 'code', None),
            getattr(secondary_team, 'code', None),
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Country/League
        country = self.merge_field(
            'country',
            primary_team.country,
            secondary_team.country,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        league = self.merge_field(
            'league',
            getattr(primary_team, 'league', None),
            getattr(secondary_team, 'league', None),
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Stadium
        stadium = self.merge_field(
            'stadium',
            getattr(primary_team, 'stadium', None),
            getattr(secondary_team, 'stadium', None),
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Founded year
        founded = self.merge_field(
            'founded',
            getattr(primary_team, 'founded', None),
            getattr(secondary_team, 'founded', None),
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Merge provider data
        provider_data = self.merge_provider_data(
            primary_team,
            secondary_team,
            primary_provider,
            secondary_provider
        )

        # Merge provider IDs
        provider_ids = self.merge_provider_ids(
            primary_team,
            secondary_team,
            primary_provider,
            secondary_provider
        )

        # Build quality metadata
        data_quality = self.build_quality_metadata(
            primary_team,
            secondary_team,
            primary_provider,
            secondary_provider
        )

        # Create merged team
        merged_team = ScoutProTeam(
            id=merged_id,
            external_id=primary_team.external_id,
            provider='canonical',
            name=name,
            short_name=short_name,
            code=code,
            country=country,
            league=league,
            stadium=stadium,
            founded=founded,
            provider_ids=provider_ids,
            provider_data=provider_data,
            data_quality=data_quality,
            created_at=primary_team.created_at,
            updated_at=datetime.now()
        )

        return merged_team

    # ========================================
    # TEAM-SPECIFIC HELPERS
    # ========================================

    def normalize_team_name(self, name: str) -> str:
        """
        Normalize team name for comparison

        Handles common variations:
        - 'Liverpool' vs 'Liverpool FC'
        - 'Man United' vs 'Manchester United'
        - etc.

        Args:
            name: Team name

        Returns:
            Normalized name

        Example:
            normalize_team_name('Liverpool FC') → 'liverpool'
            normalize_team_name('Man United') → 'manchester united'
        """
        # Remove common suffixes
        suffixes = [' FC', ' CF', ' AFC', ' United', ' City']
        normalized = name

        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]

        # Handle abbreviations
        abbreviations = {
            'Man United': 'Manchester United',
            'Man City': 'Manchester City',
            'Spurs': 'Tottenham',
        }

        if name in abbreviations:
            normalized = abbreviations[name]

        return normalized.lower().strip()

    def are_team_names_similar(
        self,
        name1: str,
        name2: str
    ) -> bool:
        """
        Check if two team names are similar

        Args:
            name1: First team name
            name2: Second team name

        Returns:
            True if names are similar, False otherwise

        Example:
            are_team_names_similar('Liverpool', 'Liverpool FC') → True
            are_team_names_similar('Liverpool', 'Everton') → False
        """
        norm1 = self.normalize_team_name(name1)
        norm2 = self.normalize_team_name(name2)

        # Exact match
        if norm1 == norm2:
            return True

        # Check if one is substring of other
        if norm1 in norm2 or norm2 in norm1:
            return True

        return False
