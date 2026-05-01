"""
Match Merger

Merges match data from multiple providers into canonical ScoutProMatch format.
Handles score discrepancies, date/time conflicts, and lineup merging.
"""

from typing import Optional
from datetime import datetime

from shared.domain.models import ScoutProMatch, MatchStatus
from shared.merger.base_merger import BaseMerger


class MatchMerger(BaseMerger):
    """
    Merges match data from multiple providers

    This merger handles:
    - Score reconciliation (critical conflicts)
    - Date/time normalization
    - Status mapping
    - Team ID resolution
    - Competition/season merging

    Usage:
        merger = MatchMerger()

        merged_match = merger.merge(
            opta_match,
            statsbomb_match,
            primary_provider='opta',
            secondary_provider='statsbomb'
        )
    """

    def get_entity_type(self) -> str:
        return "match"

    def merge(
        self,
        primary_match: ScoutProMatch,
        secondary_match: ScoutProMatch,
        primary_provider: str = 'primary',
        secondary_provider: str = 'secondary'
    ) -> ScoutProMatch:
        """
        Merge two ScoutProMatch instances

        Args:
            primary_match: Match from primary provider
            secondary_match: Match from secondary provider
            primary_provider: Primary provider name
            secondary_provider: Secondary provider name

        Returns:
            Merged ScoutProMatch

        Example:
            opta_match = ScoutProMatch(
                id='match_opta_123',
                home_score=2,
                away_score=1,
                provider='opta'
            )

            sb_match = ScoutProMatch(
                id='match_sb_456',
                home_score=2,
                away_score=1,
                provider='statsbomb'
            )

            merged = merger.merge(opta_match, sb_match, 'opta', 'statsbomb')
        """
        # Use primary match ID as base
        merged_id = primary_match.id

        # Context for conflict logging
        context = {
            'match_id': merged_id,
            'competition_id': primary_match.competition_id,
            'season_id': primary_match.season_id
        }

        # Merge each field using configured strategy
        home_team_id = self.merge_field(
            'home_team_id',
            primary_match.home_team_id,
            secondary_match.home_team_id,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        away_team_id = self.merge_field(
            'away_team_id',
            primary_match.away_team_id,
            secondary_match.away_team_id,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # CRITICAL: Scores must match (or log critical conflict)
        home_score = self.merge_field(
            'home_score',
            primary_match.home_score,
            secondary_match.home_score,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        away_score = self.merge_field(
            'away_score',
            primary_match.away_score,
            secondary_match.away_score,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Date/time
        date = self.merge_field(
            'date',
            primary_match.date,
            secondary_match.date,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Status
        status = self.merge_field(
            'status',
            primary_match.status,
            secondary_match.status,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Competition and season
        competition_id = self.merge_field(
            'competition_id',
            primary_match.competition_id,
            secondary_match.competition_id,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        season_id = self.merge_field(
            'season_id',
            primary_match.season_id,
            secondary_match.season_id,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Venue
        venue = self.merge_field(
            'venue',
            getattr(primary_match, 'venue', None),
            getattr(secondary_match, 'venue', None),
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Attendance
        attendance = self.merge_field(
            'attendance',
            getattr(primary_match, 'attendance', None),
            getattr(secondary_match, 'attendance', None),
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Referee
        referee = self.merge_field(
            'referee',
            getattr(primary_match, 'referee', None),
            getattr(secondary_match, 'referee', None),
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Merge provider data
        provider_data = self.merge_provider_data(
            primary_match,
            secondary_match,
            primary_provider,
            secondary_provider
        )

        # Merge provider IDs
        provider_ids = self.merge_provider_ids(
            primary_match,
            secondary_match,
            primary_provider,
            secondary_provider
        )

        # Build quality metadata
        data_quality = self.build_quality_metadata(
            primary_match,
            secondary_match,
            primary_provider,
            secondary_provider
        )

        # Create merged match
        merged_match = ScoutProMatch(
            id=merged_id,
            external_id=primary_match.external_id,  # Keep primary external ID
            provider='canonical',  # Mark as canonical merged
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            competition_id=competition_id,
            season_id=season_id,
            date=date,
            status=status,
            home_score=home_score,
            away_score=away_score,
            venue=venue,
            attendance=attendance,
            referee=referee,
            provider_ids=provider_ids,
            provider_data=provider_data,
            data_quality=data_quality,
            created_at=primary_match.created_at,
            updated_at=datetime.now()
        )

        return merged_match

    # ========================================
    # MATCH-SPECIFIC HELPERS
    # ========================================

    def validate_score_consistency(
        self,
        primary_match: ScoutProMatch,
        secondary_match: ScoutProMatch
    ) -> bool:
        """
        Validate that scores match between providers

        Args:
            primary_match: Match from primary provider
            secondary_match: Match from secondary provider

        Returns:
            True if scores match, False otherwise

        Example:
            valid = merger.validate_score_consistency(opta_match, sb_match)
        """
        if primary_match.home_score != secondary_match.home_score:
            return False
        if primary_match.away_score != secondary_match.away_score:
            return False
        return True

    def determine_result_consistency(
        self,
        primary_match: ScoutProMatch,
        secondary_match: ScoutProMatch
    ) -> bool:
        """
        Check if match results are consistent (same winner/draw)

        Even if scores differ slightly, check if outcome is consistent.

        Args:
            primary_match: Match from primary provider
            secondary_match: Match from secondary provider

        Returns:
            True if results are consistent, False otherwise
        """
        def get_result(match: ScoutProMatch) -> str:
            if match.home_score is None or match.away_score is None:
                return 'unknown'
            if match.home_score > match.away_score:
                return 'home_win'
            elif match.away_score > match.home_score:
                return 'away_win'
            else:
                return 'draw'

        return get_result(primary_match) == get_result(secondary_match)
