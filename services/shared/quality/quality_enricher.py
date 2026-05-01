"""
Quality Enricher

Enriches merged entities with quality scores and completeness metrics.
Helps users understand the quality of merged data and identify gaps.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from shared.domain.models import (
    ScoutProEvent, ScoutProMatch, ScoutProPlayer, ScoutProTeam,
    EventQuality
)


class QualityEnricher:
    """
    Enriches entities with quality metadata

    This enricher calculates:
    - Completeness scores (% of fields populated)
    - Data quality levels
    - Source diversity metrics
    - Freshness scores

    Usage:
        enricher = QualityEnricher()

        # Enrich a merged player
        enricher.enrich_player(merged_player)

        # Enrich a merged event
        enricher.enrich_event(merged_event)

        # Get quality report
        report = enricher.generate_quality_report([events])
    """

    def __init__(self):
        """Initialize quality enricher"""
        pass

    # ========================================
    # EVENT ENRICHMENT
    # ========================================

    def enrich_event(self, event: ScoutProEvent) -> ScoutProEvent:
        """
        Enrich event with quality metadata

        Args:
            event: Event to enrich (modified in-place)

        Returns:
            Enriched event

        Example:
            event = ScoutProEvent(...)
            enriched = enricher.enrich_event(event)
            print(enriched.data_quality['completeness_score'])
        """
        # Calculate completeness score
        completeness = self._calculate_event_completeness(event)

        # Determine quality level
        quality_level = self._determine_event_quality_level(event)

        # Count data sources
        source_count = len(event.provider_data) if event.provider_data else 1

        # Update data_quality field
        if not event.data_quality:
            event.data_quality = {}

        event.data_quality.update({
            'completeness_score': completeness,
            'quality_level': quality_level.name if isinstance(quality_level, EventQuality) else quality_level,
            'source_count': source_count,
            'has_rich_attributes': self._has_rich_attributes(event),
            'enriched_at': datetime.now()
        })

        return event

    def _calculate_event_completeness(self, event: ScoutProEvent) -> float:
        """
        Calculate event completeness score (0.0 to 1.0)

        Based on:
        - Core fields (Tier 1): event_type, minute, successful
        - Standard fields (Tier 2): player_id, x, y
        - Detailed fields (Tier 3): end_x, end_y, second, period
        - Rich attributes (Tier 4): pass_attrs, shot_attrs, defensive_attrs

        Args:
            event: Event to analyze

        Returns:
            Completeness score (0.0 to 1.0)
        """
        total_fields = 0
        filled_fields = 0

        # Tier 1: Core fields (weight: 3)
        core_fields = [
            ('event_type', event.event_type),
            ('minute', event.minute),
            ('successful', event.successful)
        ]
        for _, value in core_fields:
            total_fields += 3
            if value is not None:
                filled_fields += 3

        # Tier 2: Standard fields (weight: 2)
        standard_fields = [
            ('player_id', event.player_id),
            ('x', event.x),
            ('y', event.y),
            ('team_id', event.team_id)
        ]
        for _, value in standard_fields:
            total_fields += 2
            if value is not None:
                filled_fields += 2

        # Tier 3: Detailed fields (weight: 1)
        detailed_fields = [
            ('end_x', event.end_x),
            ('end_y', event.end_y),
            ('second', event.second),
            ('period', event.period),
            ('timestamp_seconds', event.timestamp_seconds)
        ]
        for _, value in detailed_fields:
            total_fields += 1
            if value is not None:
                filled_fields += 1

        # Tier 4: Rich attributes (weight: 2)
        if event.pass_attrs is not None:
            filled_fields += 2
        if event.shot_attrs is not None:
            filled_fields += 2
        if event.defensive_attrs is not None:
            filled_fields += 2
        total_fields += 6  # 3 possible attribute types * 2

        if total_fields == 0:
            return 0.0

        return filled_fields / total_fields

    def _determine_event_quality_level(self, event: ScoutProEvent) -> EventQuality:
        """
        Determine event quality level based on available data

        Args:
            event: Event to analyze

        Returns:
            EventQuality level
        """
        # Use existing quality level if set
        if event.quality_level:
            return event.quality_level

        completeness = self._calculate_event_completeness(event)

        if completeness >= 0.9:
            return EventQuality.COMPREHENSIVE
        elif completeness >= 0.7:
            return EventQuality.DETAILED
        elif completeness >= 0.5:
            return EventQuality.STANDARD
        elif completeness >= 0.3:
            return EventQuality.BASIC
        else:
            return EventQuality.MINIMAL

    def _has_rich_attributes(self, event: ScoutProEvent) -> bool:
        """Check if event has rich attributes"""
        return (event.pass_attrs is not None or
                event.shot_attrs is not None or
                event.defensive_attrs is not None)

    # ========================================
    # MATCH ENRICHMENT
    # ========================================

    def enrich_match(self, match: ScoutProMatch) -> ScoutProMatch:
        """
        Enrich match with quality metadata

        Args:
            match: Match to enrich (modified in-place)

        Returns:
            Enriched match
        """
        # Calculate completeness score
        completeness = self._calculate_match_completeness(match)

        # Count data sources
        source_count = len(match.provider_data) if match.provider_data else 1

        # Update data_quality field
        if not match.data_quality:
            match.data_quality = {}

        match.data_quality.update({
            'completeness_score': completeness,
            'source_count': source_count,
            'has_score': match.home_score is not None and match.away_score is not None,
            'enriched_at': datetime.now()
        })

        return match

    def _calculate_match_completeness(self, match: ScoutProMatch) -> float:
        """Calculate match completeness score"""
        fields = [
            ('home_team_id', match.home_team_id, 3),
            ('away_team_id', match.away_team_id, 3),
            ('date', match.date, 3),
            ('competition_id', match.competition_id, 2),
            ('season_id', match.season_id, 2),
            ('home_score', match.home_score, 2),
            ('away_score', match.away_score, 2),
            ('status', match.status, 1),
            ('venue', match.venue, 1),
            ('attendance', match.attendance, 1),
            ('referee', match.referee, 1)
        ]

        total_weight = sum(weight for _, _, weight in fields)
        filled_weight = sum(weight for _, value, weight in fields if value is not None)

        return filled_weight / total_weight if total_weight > 0 else 0.0

    # ========================================
    # PLAYER ENRICHMENT
    # ========================================

    def enrich_player(self, player: ScoutProPlayer) -> ScoutProPlayer:
        """
        Enrich player with quality metadata

        Args:
            player: Player to enrich (modified in-place)

        Returns:
            Enriched player
        """
        # Calculate completeness score
        completeness = self._calculate_player_completeness(player)

        # Count data sources
        source_count = len(player.provider_data) if player.provider_data else 1

        # Update data_quality field
        if not player.data_quality:
            player.data_quality = {}

        player.data_quality.update({
            'completeness_score': completeness,
            'source_count': source_count,
            'has_biographic_data': self._has_biographic_data(player),
            'enriched_at': datetime.now()
        })

        return player

    def _calculate_player_completeness(self, player: ScoutProPlayer) -> float:
        """Calculate player completeness score"""
        fields = [
            ('name', player.name, 3),
            ('first_name', player.first_name, 2),
            ('last_name', player.last_name, 2),
            ('birth_date', player.birth_date, 2),
            ('position', player.position, 2),
            ('nationality', player.nationality, 1),
            ('height_cm', player.height_cm, 1),
            ('weight_kg', player.weight_kg, 1),
            ('preferred_foot', player.preferred_foot, 1)
        ]

        total_weight = sum(weight for _, _, weight in fields)
        filled_weight = sum(weight for _, value, weight in fields if value is not None)

        return filled_weight / total_weight if total_weight > 0 else 0.0

    def _has_biographic_data(self, player: ScoutProPlayer) -> bool:
        """Check if player has biographic data"""
        return (player.birth_date is not None or
                player.nationality is not None or
                player.height_cm is not None)

    # ========================================
    # TEAM ENRICHMENT
    # ========================================

    def enrich_team(self, team: ScoutProTeam) -> ScoutProTeam:
        """
        Enrich team with quality metadata

        Args:
            team: Team to enrich (modified in-place)

        Returns:
            Enriched team
        """
        # Calculate completeness score
        completeness = self._calculate_team_completeness(team)

        # Count data sources
        source_count = len(team.provider_data) if team.provider_data else 1

        # Update data_quality field
        if not team.data_quality:
            team.data_quality = {}

        team.data_quality.update({
            'completeness_score': completeness,
            'source_count': source_count,
            'enriched_at': datetime.now()
        })

        return team

    def _calculate_team_completeness(self, team: ScoutProTeam) -> float:
        """Calculate team completeness score"""
        fields = [
            ('name', team.name, 3),
            ('short_name', team.short_name, 2),
            ('country', team.country, 2),
            ('code', team.code, 1),
            ('league', team.league, 1),
            ('stadium', team.stadium, 1),
            ('founded', team.founded, 1)
        ]

        total_weight = sum(weight for _, _, weight in fields)
        filled_weight = sum(weight for _, value, weight in fields if value is not None)

        return filled_weight / total_weight if total_weight > 0 else 0.0

    # ========================================
    # QUALITY REPORTING
    # ========================================

    def generate_quality_report(
        self,
        events: Optional[List[ScoutProEvent]] = None,
        matches: Optional[List[ScoutProMatch]] = None,
        players: Optional[List[ScoutProPlayer]] = None,
        teams: Optional[List[ScoutProTeam]] = None
    ) -> Dict[str, Any]:
        """
        Generate quality report for entities

        Args:
            events: List of events
            matches: List of matches
            players: List of players
            teams: List of teams

        Returns:
            Quality report dict

        Example:
            report = enricher.generate_quality_report(events=events, matches=matches)
            print(f"Avg event completeness: {report['events']['avg_completeness']}")
        """
        report = {
            'generated_at': datetime.now(),
            'events': None,
            'matches': None,
            'players': None,
            'teams': None
        }

        if events:
            report['events'] = self._generate_event_report(events)

        if matches:
            report['matches'] = self._generate_match_report(matches)

        if players:
            report['players'] = self._generate_player_report(players)

        if teams:
            report['teams'] = self._generate_team_report(teams)

        return report

    def _generate_event_report(self, events: List[ScoutProEvent]) -> Dict[str, Any]:
        """Generate quality report for events"""
        if not events:
            return {}

        completeness_scores = [
            self._calculate_event_completeness(e) for e in events
        ]

        quality_levels = {}
        for event in events:
            level = self._determine_event_quality_level(event)
            level_name = level.name if isinstance(level, EventQuality) else str(level)
            quality_levels[level_name] = quality_levels.get(level_name, 0) + 1

        return {
            'total_count': len(events),
            'avg_completeness': sum(completeness_scores) / len(completeness_scores),
            'min_completeness': min(completeness_scores),
            'max_completeness': max(completeness_scores),
            'quality_distribution': quality_levels,
            'with_rich_attributes': sum(1 for e in events if self._has_rich_attributes(e))
        }

    def _generate_match_report(self, matches: List[ScoutProMatch]) -> Dict[str, Any]:
        """Generate quality report for matches"""
        if not matches:
            return {}

        completeness_scores = [
            self._calculate_match_completeness(m) for m in matches
        ]

        return {
            'total_count': len(matches),
            'avg_completeness': sum(completeness_scores) / len(completeness_scores),
            'min_completeness': min(completeness_scores),
            'max_completeness': max(completeness_scores),
            'with_scores': sum(1 for m in matches if m.home_score is not None)
        }

    def _generate_player_report(self, players: List[ScoutProPlayer]) -> Dict[str, Any]:
        """Generate quality report for players"""
        if not players:
            return {}

        completeness_scores = [
            self._calculate_player_completeness(p) for p in players
        ]

        return {
            'total_count': len(players),
            'avg_completeness': sum(completeness_scores) / len(completeness_scores),
            'min_completeness': min(completeness_scores),
            'max_completeness': max(completeness_scores),
            'with_biographic_data': sum(1 for p in players if self._has_biographic_data(p))
        }

    def _generate_team_report(self, teams: List[ScoutProTeam]) -> Dict[str, Any]:
        """Generate quality report for teams"""
        if not teams:
            return {}

        completeness_scores = [
            self._calculate_team_completeness(t) for t in teams
        ]

        return {
            'total_count': len(teams),
            'avg_completeness': sum(completeness_scores) / len(completeness_scores),
            'min_completeness': min(completeness_scores),
            'max_completeness': max(completeness_scores)
        }
