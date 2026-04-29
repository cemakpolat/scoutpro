"""
Opta Event Taxonomy

Maps Opta F24 event type IDs to ScoutPro canonical event types.
Based on the event_taxonomy.yaml configuration.
"""

from typing import Optional, Dict
from shared.domain.models import EventType


class OptaEventTaxonomy:
    """
    Maps Opta event types and qualifiers to canonical format

    Opta F24 events have:
    - type_id: Main event classification
    - outcome: 1 = successful, 0 = unsuccessful
    - qualifiers: Additional event metadata (200+ possible qualifiers)
    """

    # ============================================
    # OPTA EVENT TYPE MAPPINGS
    # ============================================
    # Maps Opta type_id → ScoutPro EventType

    OPTA_TO_SCOUTPRO_MAP: Dict[int, Dict] = {
        # === PASSES (type_id: 1) ===
        1: {
            'canonical_type': EventType.PASS_COMPLETED,
            'requires_outcome': 1,
            'alt_outcome': EventType.PASS_INCOMPLETE  # If outcome=0
        },

        # === OFFSIDE PASS (type_id: 2) ===
        2: {
            'canonical_type': EventType.PASS_INCOMPLETE,
            'note': 'Offside passes are always incomplete'
        },

        # === TAKE ON / DRIBBLE (type_id: 3) ===
        3: {
            'canonical_type': EventType.DRIBBLE_COMPLETED,
            'requires_outcome': 1,
            'alt_outcome': EventType.DRIBBLE_INCOMPLETE
        },

        # === FOUL (type_id: 4) ===
        4: {
            'canonical_type': EventType.FOUL_COMMITTED
        },

        # === CORNER (type_id: 6) ===
        6: {
            'canonical_type': EventType.CORNER
        },

        # === TACKLE (type_id: 7) ===
        7: {
            'canonical_type': EventType.TACKLE_WON,
            'requires_outcome': 1,
            'alt_outcome': EventType.TACKLE_LOST
        },

        # === INTERCEPTION (type_id: 8) ===
        8: {
            'canonical_type': EventType.INTERCEPTION
        },

        # === SAVE (type_id: 9, 11) ===
        9: {
            'canonical_type': EventType.SAVE
        },

        # === BLOCKED SHOT (type_id: 10) ===
        10: {
            'canonical_type': EventType.SHOT_BLOCKED
        },

        # === SMOTHER (type_id: 11) ===
        11: {
            'canonical_type': EventType.SMOTHER
        },

        # === CLEARANCE (type_id: 12) ===
        12: {
            'canonical_type': EventType.CLEARANCE
        },

        # === MISS (type_id: 13) ===
        13: {
            'canonical_type': EventType.SHOT_OFF_TARGET
        },

        # === POST (type_id: 14) ===
        14: {
            'canonical_type': EventType.SHOT_OFF_TARGET,
            'note': 'Hit post/crossbar'
        },

        # === ATTEMPT SAVED (type_id: 15) ===
        15: {
            'canonical_type': EventType.SHOT_ON_TARGET
        },

        # === GOAL (type_id: 16) ===
        16: {
            'canonical_type': EventType.GOAL
        },

        # === CARD (type_id: 17) ===
        17: {
            'canonical_type': EventType.YELLOW_CARD,  # Default to yellow
            'qualifier_check': {
                32: EventType.YELLOW_CARD,  # Q32 = yellow
                33: EventType.RED_CARD      # Q33 = red
            }
        },

        # === SUBSTITUTION OFF (type_id: 18) ===
        18: {
            'canonical_type': EventType.SUBSTITUTION
        },

        # === SUBSTITUTION ON (type_id: 19) ===
        19: {
            'canonical_type': EventType.SUBSTITUTION
        },

        # === AERIAL (type_id: 44) ===
        44: {
            'canonical_type': EventType.AERIAL_DUEL_WON,
            'requires_outcome': 1,
            'alt_outcome': EventType.AERIAL_DUEL_LOST
        },

        # === OFFSIDE (type_id: 51) ===
        51: {
            'canonical_type': EventType.OFFSIDE
        },
    }

    # ============================================
    # OPTA QUALIFIERS
    # ============================================
    # Important F24 qualifiers and their meanings

    QUALIFIER_MEANINGS = {
        # Pass qualifiers
        1: 'long_ball',
        2: 'cross',
        3: 'head_pass',
        5: 'through_ball',
        6: 'flick_on',
        107: 'throw_in',
        123: 'launch',
        124: 'flick_on',
        140: 'pass_end_x',
        141: 'pass_end_y',
        154: 'key_pass',
        155: 'receiver_player_id',
        156: 'chipped_pass',
        168: 'assist',
        169: 'assist_2nd',
        196: 'corner_taken',
        210: 'goal_assist',
        212: 'length_of_pass',

        # Shot qualifiers
        9: 'penalty',
        20: 'shot_from_inside_box',
        22: 'volley',
        26: 'head',
        72: 'overhead_kick',
        82: 'blocked_by_defender',
        94: 'deflected_shot',
        96: 'saved_off_line',
        97: 'swerve',
        107: 'no_touch',
        139: 'swerve_left',
        155: 'related_player',

        # Card qualifiers
        31: 'second_yellow',
        32: 'yellow_card',
        33: 'red_card',

        # Pressure
        212: 'under_pressure',

        # Body parts
        72: 'left_foot',
        20: 'right_foot',
        15: 'head',
        21: 'other_body_part',

        # General
        30: 'deleted_event',
        44: 'injury',
        173: 'offside',
        233: 'penalty_area',
    }

    @classmethod
    def map_event_type(
        cls,
        type_id: int,
        outcome: int = 1,
        qualifiers: Optional[Dict[int, str]] = None
    ) -> Optional[EventType]:
        """
        Map Opta event type to canonical EventType

        Args:
            type_id: Opta event type ID
            outcome: Event outcome (1=success, 0=failure)
            qualifiers: Dict of qualifier_id → value

        Returns:
            Canonical EventType or None if unmapped

        Example:
            map_event_type(1, 1) → EventType.PASS_COMPLETED
            map_event_type(1, 0) → EventType.PASS_INCOMPLETE
            map_event_type(17, qualifiers={32: ""}) → EventType.YELLOW_CARD
        """
        if type_id not in cls.OPTA_TO_SCOUTPRO_MAP:
            return None

        mapping = cls.OPTA_TO_SCOUTPRO_MAP[type_id]

        # Check if mapping depends on qualifiers (e.g., card type)
        if 'qualifier_check' in mapping and qualifiers:
            for qualifier_id, event_type in mapping['qualifier_check'].items():
                if qualifier_id in qualifiers:
                    return event_type

        # Check if mapping depends on outcome
        if 'requires_outcome' in mapping:
            if outcome == mapping['requires_outcome']:
                return mapping['canonical_type']
            elif 'alt_outcome' in mapping:
                return mapping['alt_outcome']
            else:
                return mapping['canonical_type']

        return mapping['canonical_type']

    @classmethod
    def is_pass_event(cls, type_id: int) -> bool:
        """Check if event type is a pass"""
        return type_id in [1, 2]

    @classmethod
    def is_shot_event(cls, type_id: int) -> bool:
        """Check if event type is a shot/goal"""
        return type_id in [13, 14, 15, 16]

    @classmethod
    def is_defensive_event(cls, type_id: int) -> bool:
        """Check if event type is defensive"""
        return type_id in [7, 8, 10, 12]  # Tackle, interception, block, clearance

    @classmethod
    def extract_pass_end_location(cls, qualifiers: Dict[int, str]) -> tuple:
        """
        Extract pass end location from qualifiers

        Args:
            qualifiers: Dict of qualifier_id → value

        Returns:
            Tuple of (end_x, end_y) or (None, None)
        """
        end_x = qualifiers.get(140)  # Pass end X
        end_y = qualifiers.get(141)  # Pass end Y

        if end_x is not None and end_y is not None:
            try:
                return (float(end_x), float(end_y))
            except (ValueError, TypeError):
                return (None, None)

        return (None, None)

    @classmethod
    def is_key_pass(cls, qualifiers: Dict[int, str]) -> bool:
        """Check if pass is a key pass"""
        return 154 in qualifiers or 210 in qualifiers  # Key pass or assist

    @classmethod
    def is_assist(cls, qualifiers: Dict[int, str]) -> bool:
        """Check if pass is an assist"""
        return 210 in qualifiers  # Goal assist

    @classmethod
    def is_penalty(cls, qualifiers: Dict[int, str]) -> bool:
        """Check if shot is a penalty"""
        return 9 in qualifiers

    @classmethod
    def is_under_pressure(cls, qualifiers: Dict[int, str]) -> bool:
        """Check if action was under pressure"""
        return 212 in qualifiers

    @classmethod
    def get_body_part(cls, qualifiers: Dict[int, str]) -> Optional[str]:
        """
        Extract body part used for event

        Returns:
            'right_foot', 'left_foot', 'head', 'other', or None
        """
        if 72 in qualifiers:
            return 'left_foot'
        elif 20 in qualifiers:
            return 'right_foot'
        elif 15 in qualifiers or 26 in qualifiers:
            return 'head'
        elif 21 in qualifiers:
            return 'other'
        return None

    @classmethod
    def is_from_set_piece(cls, qualifiers: Dict[int, str]) -> bool:
        """Check if event was from a set piece"""
        set_piece_qualifiers = [
            6,    # Corner
            107,  # Throw-in
            9,    # Penalty
            5,    # Free kick
        ]
        return any(q in qualifiers for q in set_piece_qualifiers)
