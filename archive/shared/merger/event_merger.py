"""
Event Merger

Merges event data from multiple providers into canonical ScoutProEvent format.
Handles event correlation, coordinate normalization, and attribute enrichment.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from dataclasses import replace

from shared.domain.models import ScoutProEvent, EventQuality
from shared.domain.models.attributes import PassAttributes, ShotAttributes, DefensiveAttributes
from shared.merger.base_merger import BaseMerger


class EventMerger(BaseMerger):
    """
    Merges event data from multiple providers

    This merger handles:
    - Event correlation (matching events across providers)
    - Coordinate merging and normalization
    - Rich attribute enrichment (pass, shot, defensive)
    - Quality scoring

    Event correlation is challenging because:
    - Different providers may have slightly different timestamps
    - Coordinates may differ
    - Event types may be classified differently
    - Some events may exist in one provider but not another

    Usage:
        merger = EventMerger()

        # Correlate and merge two event lists
        merged_events = merger.merge_event_lists(
            opta_events,
            statsbomb_events,
            primary_provider='opta',
            secondary_provider='statsbomb'
        )

        # Merge two correlated events
        merged_event = merger.merge(
            opta_event,
            statsbomb_event,
            primary_provider='opta',
            secondary_provider='statsbomb'
        )
    """

    def __init__(
        self,
        correlation_time_threshold: int = 5,  # seconds
        correlation_distance_threshold: float = 10.0,  # meters
        **kwargs
    ):
        """
        Initialize event merger

        Args:
            correlation_time_threshold: Max time difference (seconds) to consider events correlated
            correlation_distance_threshold: Max distance (meters) to consider events correlated
            **kwargs: Additional args passed to BaseMerger
        """
        super().__init__(**kwargs)
        self.correlation_time_threshold = correlation_time_threshold
        self.correlation_distance_threshold = correlation_distance_threshold

    def get_entity_type(self) -> str:
        return "event"

    def merge(
        self,
        primary_event: ScoutProEvent,
        secondary_event: ScoutProEvent,
        primary_provider: str = 'primary',
        secondary_provider: str = 'secondary'
    ) -> ScoutProEvent:
        """
        Merge two ScoutProEvent instances

        Args:
            primary_event: Event from primary provider
            secondary_event: Event from secondary provider
            primary_provider: Primary provider name
            secondary_provider: Secondary provider name

        Returns:
            Merged ScoutProEvent

        Example:
            opta_event = ScoutProEvent(
                id='evt_opta_123',
                event_type=EventType.PASS_COMPLETED,
                x=65.2,
                y=48.7,
                provider='opta'
            )

            sb_event = ScoutProEvent(
                id='evt_sb_456',
                event_type=EventType.PASS_COMPLETED,
                x=67.5,
                y=50.1,
                provider='statsbomb'
            )

            merged = merger.merge(opta_event, sb_event, 'opta', 'statsbomb')
        """
        # Use primary event ID as base
        merged_id = primary_event.id

        # Context for conflict logging
        context = {
            'event_id': merged_id,
            'match_id': primary_event.match_id,
            'minute': primary_event.minute
        }

        # Merge basic fields
        event_type = self.merge_field(
            'event_type',
            primary_event.event_type,
            secondary_event.event_type,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        minute = self.merge_field(
            'minute',
            primary_event.minute,
            secondary_event.minute,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        second = self.merge_field(
            'second',
            primary_event.second,
            secondary_event.second,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        period = self.merge_field(
            'period',
            primary_event.period,
            secondary_event.period,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        timestamp_seconds = self.merge_field(
            'timestamp_seconds',
            primary_event.timestamp_seconds,
            secondary_event.timestamp_seconds,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Merge coordinates (important for analytics)
        x = self.merge_field(
            'x',
            primary_event.x,
            secondary_event.x,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        y = self.merge_field(
            'y',
            primary_event.y,
            secondary_event.y,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        end_x = self.merge_field(
            'end_x',
            primary_event.end_x,
            secondary_event.end_x,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        end_y = self.merge_field(
            'end_y',
            primary_event.end_y,
            secondary_event.end_y,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Player and team
        player_id = self.merge_field(
            'player_id',
            primary_event.player_id,
            secondary_event.player_id,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        team_id = self.merge_field(
            'team_id',
            primary_event.team_id,
            secondary_event.team_id,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Outcome
        successful = self.merge_field(
            'successful',
            primary_event.successful,
            secondary_event.successful,
            primary_provider,
            secondary_provider,
            entity_id=merged_id,
            context=context
        )

        # Merge rich attributes
        pass_attrs = self._merge_pass_attributes(
            primary_event.pass_attrs,
            secondary_event.pass_attrs,
            primary_provider,
            secondary_provider
        )

        shot_attrs = self._merge_shot_attributes(
            primary_event.shot_attrs,
            secondary_event.shot_attrs,
            primary_provider,
            secondary_provider
        )

        defensive_attrs = self._merge_defensive_attributes(
            primary_event.defensive_attrs,
            secondary_event.defensive_attrs,
            primary_provider,
            secondary_provider
        )

        # Determine quality level
        quality_level = self._determine_quality_level(
            primary_event.quality_level,
            secondary_event.quality_level
        )

        # Merge provider data
        provider_data = self.merge_provider_data(
            primary_event,
            secondary_event,
            primary_provider,
            secondary_provider
        )

        # Merge provider IDs
        provider_ids = self.merge_provider_ids(
            primary_event,
            secondary_event,
            primary_provider,
            secondary_provider
        )

        # Build quality metadata
        data_quality = self.build_quality_metadata(
            primary_event,
            secondary_event,
            primary_provider,
            secondary_provider
        )

        # Create merged event
        merged_event = ScoutProEvent(
            id=merged_id,
            match_id=primary_event.match_id,
            event_type=event_type,
            minute=minute,
            second=second,
            period=period,
            timestamp_seconds=timestamp_seconds,
            player_id=player_id,
            team_id=team_id,
            x=x,
            y=y,
            end_x=end_x,
            end_y=end_y,
            successful=successful,
            quality_level=quality_level,
            pass_attrs=pass_attrs,
            shot_attrs=shot_attrs,
            defensive_attrs=defensive_attrs,
            provider='canonical',
            external_id=primary_event.external_id,
            provider_ids=provider_ids,
            provider_data=provider_data,
            data_quality=data_quality,
            created_at=primary_event.created_at,
            updated_at=datetime.now()
        )

        return merged_event

    # ========================================
    # EVENT CORRELATION
    # ========================================

    def correlate_events(
        self,
        primary_events: List[ScoutProEvent],
        secondary_events: List[ScoutProEvent]
    ) -> List[Tuple[Optional[ScoutProEvent], Optional[ScoutProEvent]]]:
        """
        Correlate events from two providers

        This attempts to match events that represent the same real-world action.
        Correlation is based on:
        - Event type similarity
        - Timestamp proximity
        - Coordinate proximity
        - Player ID match

        Args:
            primary_events: Events from primary provider
            secondary_events: Events from secondary provider

        Returns:
            List of (primary_event, secondary_event) tuples
            - Both not None: Correlated events
            - primary None: Event only in secondary
            - secondary None: Event only in primary

        Example:
            correlations = merger.correlate_events(opta_events, sb_events)
            for primary, secondary in correlations:
                if primary and secondary:
                    merged = merger.merge(primary, secondary, 'opta', 'statsbomb')
        """
        correlated = []
        used_secondary = set()

        for primary_event in primary_events:
            # Find best matching secondary event
            best_match = None
            best_score = 0.0

            for i, secondary_event in enumerate(secondary_events):
                if i in used_secondary:
                    continue

                score = self._correlation_score(primary_event, secondary_event)

                if score > best_score and score > 0.6:  # Correlation threshold
                    best_score = score
                    best_match = (secondary_event, i)

            if best_match:
                correlated.append((primary_event, best_match[0]))
                used_secondary.add(best_match[1])
            else:
                # Primary event has no match
                correlated.append((primary_event, None))

        # Add unmatched secondary events
        for i, secondary_event in enumerate(secondary_events):
            if i not in used_secondary:
                correlated.append((None, secondary_event))

        return correlated

    def _correlation_score(
        self,
        event1: ScoutProEvent,
        event2: ScoutProEvent
    ) -> float:
        """
        Calculate correlation score between two events (0.0 to 1.0)

        Higher score = more likely to be the same event

        Args:
            event1: First event
            event2: Second event

        Returns:
            Correlation score (0.0 to 1.0)
        """
        score = 0.0

        # Event type match (weight: 0.4)
        if event1.event_type == event2.event_type:
            score += 0.4
        elif self._are_event_types_similar(event1.event_type, event2.event_type):
            score += 0.2

        # Time proximity (weight: 0.3)
        if event1.timestamp_seconds is not None and event2.timestamp_seconds is not None:
            time_diff = abs(event1.timestamp_seconds - event2.timestamp_seconds)
            if time_diff <= self.correlation_time_threshold:
                time_score = 1.0 - (time_diff / self.correlation_time_threshold)
                score += 0.3 * time_score

        # Spatial proximity (weight: 0.2)
        if event1.x is not None and event1.y is not None and event2.x is not None and event2.y is not None:
            distance = ((event1.x - event2.x) ** 2 + (event1.y - event2.y) ** 2) ** 0.5
            if distance <= self.correlation_distance_threshold:
                spatial_score = 1.0 - (distance / self.correlation_distance_threshold)
                score += 0.2 * spatial_score

        # Player ID match (weight: 0.1)
        if event1.player_id and event2.player_id and event1.player_id == event2.player_id:
            score += 0.1

        return min(score, 1.0)

    def _are_event_types_similar(self, type1, type2) -> bool:
        """Check if two event types are similar (e.g., PASS_COMPLETED vs PASS_INCOMPLETE)"""
        # Similar event type families
        similar_groups = [
            ['PASS_COMPLETED', 'PASS_INCOMPLETE'],
            ['SHOT_ON_TARGET', 'SHOT_OFF_TARGET', 'SHOT_BLOCKED', 'GOAL'],
            ['TACKLE_WON', 'TACKLE_LOST'],
            ['DRIBBLE_COMPLETED', 'DRIBBLE_INCOMPLETE'],
            ['AERIAL_DUEL_WON', 'AERIAL_DUEL_LOST']
        ]

        type1_str = type1.name if hasattr(type1, 'name') else str(type1)
        type2_str = type2.name if hasattr(type2, 'name') else str(type2)

        for group in similar_groups:
            if type1_str in group and type2_str in group:
                return True

        return False

    def merge_event_lists(
        self,
        primary_events: List[ScoutProEvent],
        secondary_events: List[ScoutProEvent],
        primary_provider: str = 'primary',
        secondary_provider: str = 'secondary'
    ) -> List[ScoutProEvent]:
        """
        Merge two lists of events

        Args:
            primary_events: Events from primary provider
            secondary_events: Events from secondary provider
            primary_provider: Primary provider name
            secondary_provider: Secondary provider name

        Returns:
            List of merged events

        Example:
            merged_events = merger.merge_event_lists(
                opta_events,
                statsbomb_events,
                'opta',
                'statsbomb'
            )
        """
        merged_events = []

        # Correlate events
        correlations = self.correlate_events(primary_events, secondary_events)

        for primary, secondary in correlations:
            if primary and secondary:
                # Both exist - merge them
                merged = self.merge(primary, secondary, primary_provider, secondary_provider)
                merged_events.append(merged)
            elif primary:
                # Only in primary - keep as is
                merged_events.append(primary)
            elif secondary:
                # Only in secondary - keep as is
                merged_events.append(secondary)

        return merged_events

    # ========================================
    # ATTRIBUTE MERGING
    # ========================================

    def _merge_pass_attributes(
        self,
        primary_attrs: Optional[PassAttributes],
        secondary_attrs: Optional[PassAttributes],
        primary_provider: str,
        secondary_provider: str
    ) -> Optional[PassAttributes]:
        """Merge pass attributes from both providers"""
        if primary_attrs is None and secondary_attrs is None:
            return None

        if primary_attrs is None:
            return secondary_attrs
        if secondary_attrs is None:
            return primary_attrs

        # Merge individual fields
        # For simplicity, prefer primary for most fields
        # In production, you'd apply field-specific merge rules

        merged = PassAttributes(
            pass_type=primary_attrs.pass_type or secondary_attrs.pass_type,
            pass_height=primary_attrs.pass_height or secondary_attrs.pass_height,
            body_part=primary_attrs.body_part or secondary_attrs.body_part,
            under_pressure=primary_attrs.under_pressure or secondary_attrs.under_pressure,
            assisted_goal=primary_attrs.assisted_goal or secondary_attrs.assisted_goal,
            key_pass=primary_attrs.key_pass or secondary_attrs.key_pass,
            pass_length_m=primary_attrs.pass_length_m or secondary_attrs.pass_length_m,
            receiver_id=primary_attrs.receiver_id or secondary_attrs.receiver_id,
            corner_kick=primary_attrs.corner_kick or secondary_attrs.corner_kick,
            free_kick=primary_attrs.free_kick or secondary_attrs.free_kick,
            throw_in=primary_attrs.throw_in or secondary_attrs.throw_in,
            opta_qualifiers=primary_attrs.opta_qualifiers,
            statsbomb_pass_type=secondary_attrs.statsbomb_pass_type,
            freeze_frame=secondary_attrs.freeze_frame  # StatsBomb exclusive
        )

        return merged

    def _merge_shot_attributes(
        self,
        primary_attrs: Optional[ShotAttributes],
        secondary_attrs: Optional[ShotAttributes],
        primary_provider: str,
        secondary_provider: str
    ) -> Optional[ShotAttributes]:
        """Merge shot attributes from both providers"""
        if primary_attrs is None and secondary_attrs is None:
            return None

        if primary_attrs is None:
            return secondary_attrs
        if secondary_attrs is None:
            return primary_attrs

        # Keep xG from both providers
        merged = ShotAttributes(
            body_part=primary_attrs.body_part or secondary_attrs.body_part,
            shot_type=primary_attrs.shot_type or secondary_attrs.shot_type,
            shot_technique=primary_attrs.shot_technique or secondary_attrs.shot_technique,
            xg=secondary_attrs.xg or primary_attrs.xg,  # Prefer StatsBomb xG
            blocked=primary_attrs.blocked or secondary_attrs.blocked,
            deflected=primary_attrs.deflected or secondary_attrs.deflected,
            one_on_one=primary_attrs.one_on_one or secondary_attrs.one_on_one,
            penalty=primary_attrs.penalty or secondary_attrs.penalty,
            opta_qualifiers=primary_attrs.opta_qualifiers,
            statsbomb_shot_data=secondary_attrs.statsbomb_shot_data,
            freeze_frame=secondary_attrs.freeze_frame
        )

        return merged

    def _merge_defensive_attributes(
        self,
        primary_attrs: Optional[DefensiveAttributes],
        secondary_attrs: Optional[DefensiveAttributes],
        primary_provider: str,
        secondary_provider: str
    ) -> Optional[DefensiveAttributes]:
        """Merge defensive attributes from both providers"""
        if primary_attrs is None and secondary_attrs is None:
            return None

        if primary_attrs is None:
            return secondary_attrs
        if secondary_attrs is None:
            return primary_attrs

        merged = DefensiveAttributes(
            action_type=primary_attrs.action_type or secondary_attrs.action_type,
            clearance_head=primary_attrs.clearance_head or secondary_attrs.clearance_head,
            blocked_shot=primary_attrs.blocked_shot or secondary_attrs.blocked_shot,
            opta_qualifiers=primary_attrs.opta_qualifiers
        )

        return merged

    def _determine_quality_level(
        self,
        primary_quality: EventQuality,
        secondary_quality: EventQuality
    ) -> EventQuality:
        """Determine merged quality level (use highest)"""
        quality_order = [
            EventQuality.MINIMAL,
            EventQuality.BASIC,
            EventQuality.STANDARD,
            EventQuality.DETAILED,
            EventQuality.COMPREHENSIVE
        ]

        primary_rank = quality_order.index(primary_quality) if primary_quality in quality_order else 0
        secondary_rank = quality_order.index(secondary_quality) if secondary_quality in quality_order else 0

        return quality_order[max(primary_rank, secondary_rank)]
