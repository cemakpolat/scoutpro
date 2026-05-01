"""
Opta Mapper

Maps Opta F24 event data to ScoutPro canonical format.
Wraps existing Opta parsing logic from services/shared/parsers/parser.py
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
import uuid

from shared.adapters.base import BaseMapper
from shared.domain.models import (
    ScoutProEvent, ScoutProMatch, ScoutProPlayer, ScoutProTeam,
    EventType, EventQuality, MatchStatus
)
from shared.domain.models.attributes import PassAttributes, ShotAttributes, DefensiveAttributes
from .opta_event_taxonomy import OptaEventTaxonomy


class OptaMapper(BaseMapper):
    """
    Maps Opta data to ScoutPro canonical format

    This mapper wraps the existing Opta parsing logic and transforms
    it into the ScoutPro canonical format.

    Opta provides several feeds:
    - F1: Season schedule
    - F9: Match lineups and stats
    - F24: Event-by-event data (main feed)
    - F40: Squad lists

    This mapper focuses on F24 (events) and F9 (matches).
    """

    def get_provider_name(self) -> str:
        return "opta"

    def get_data_quality(self) -> EventQuality:
        # Opta F24 provides comprehensive data
        return EventQuality.COMPREHENSIVE

    # ========================================
    # PLAYER MAPPING
    # ========================================

    @staticmethod
    def _extract_f40_stats(raw_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract the Stat array from an F40 player node into a flat dict.

        F40 Stat format:
            [{"@value": "Cenk", "@attributes": {"Type": "first_name"}}, ...]
        Also handles F9 PersonName format for backward compatibility.
        """
        stats: Dict[str, str] = {}

        stat_list = raw_data.get('Stat', [])
        if isinstance(stat_list, dict):
            stat_list = [stat_list]

        for stat in stat_list:
            stat_type = stat.get('@attributes', {}).get('Type', '')
            stat_value = stat.get('@value', '')
            if stat_type and stat_value:
                stats[stat_type] = str(stat_value)

        # Also support legacy F9 PersonName format
        person_name = raw_data.get('PersonName', {})
        if person_name:
            if person_name.get('First'):
                stats.setdefault('first_name', person_name['First'])
            if person_name.get('Last'):
                stats.setdefault('last_name', person_name['Last'])
            if person_name.get('Known'):
                stats.setdefault('known_name', person_name['Known'])
            if person_name.get('BirthDate'):
                stats.setdefault('birth_date', person_name['BirthDate'])

        return stats

    def map_player(self, raw_data: Dict[str, Any]) -> ScoutProPlayer:
        """
        Map Opta player data → ScoutProPlayer.

        Handles both:
        - F40 format: Stat array with @attributes.Type / @value pairs
        - F9 format:  PersonName dict with First / Last / Known keys

        F40 player node injected by OptaConnector also carries:
          _team_id, _team_name, _team_attrs, _comp_attrs
        """
        attrs = raw_data.get('@attributes', {})

        player_id = attrs.get('uID', raw_data.get('uID', ''))
        position_raw = raw_data.get('Position', attrs.get('Position', ''))

        # Flatten the Stat array (F40) or PersonName dict (F9) into a dict
        stats = self._extract_f40_stats(raw_data)

        first_name = stats.get('first_name', '')
        last_name = stats.get('last_name', '')
        known_name = stats.get('known_name') or stats.get('known_name_first') or None

        # Prefer the structured Name field if Stat names are absent
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = raw_data.get('Name', '')

        # Birth date
        birth_date_val = None
        birth_date_str = stats.get('birth_date', '')
        if birth_date_str:
            try:
                birth_date_val = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        # Physical attributes
        height_raw = stats.get('height')
        weight_raw = stats.get('weight')
        height_cm: Optional[int] = None
        weight_kg: Optional[int] = None
        if height_raw and height_raw not in ('Unknown', ''):
            try:
                height_cm = int(height_raw)
            except ValueError:
                pass
        if weight_raw and weight_raw not in ('Unknown', ''):
            try:
                weight_kg = int(weight_raw)
            except ValueError:
                pass

        # Jersey number
        jersey_raw = stats.get('jersey_num', '')
        jersey_num: Optional[int] = None
        if jersey_raw and jersey_raw not in ('Unknown', ''):
            try:
                jersey_num = int(jersey_raw)
            except ValueError:
                pass

        # Club / team context (injected by OptaConnector)
        team_name = raw_data.get('_team_name', '')
        team_id = raw_data.get('_team_id', '')

        # Preferred foot normalisation
        foot_raw = stats.get('preferred_foot', '')
        foot = foot_raw.lower() if foot_raw and foot_raw not in ('Unknown', '') else None

        # Create ScoutProPlayer
        scoutpro_player = ScoutProPlayer(
            id=self.generate_scoutpro_id('player', player_id),
            external_id=player_id,
            provider='opta',
            name=full_name,
            first_name=first_name,
            last_name=last_name,
            known_name=known_name,
            birth_date=birth_date_val,
            position=self.standardize_position(position_raw),
            detailed_position=stats.get('real_position', position_raw),
            nationality=stats.get('first_nationality') or stats.get('country') or '',
            height_cm=height_cm,
            weight_kg=weight_kg,
            jersey_number=jersey_num,
            foot=foot,
            current_team_id=team_id,
            provider_ids={'opta': player_id},
            provider_data={
                'opta': {
                    'source': 'opta',
                    'last_updated': datetime.now(),
                    'data': raw_data
                }
            },
            scoutpro_metadata={
                'team_name': team_name,
                'team_id': team_id,
                'real_position_side': stats.get('real_position_side'),
                'join_date': stats.get('join_date'),
                'birth_place': stats.get('birth_place'),
            },
            data_quality={
                'completeness_score': self._calculate_player_completeness(stats),
                'data_sources': ['opta']
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        return scoutpro_player

    def _calculate_player_completeness(self, stats: Dict) -> float:
        """Calculate how complete player data is (0.0 to 1.0) based on extracted stats."""
        key_fields = ['first_name', 'last_name', 'birth_date', 'first_nationality',
                      'height', 'weight', 'preferred_foot', 'real_position']
        present = sum(1 for f in key_fields if stats.get(f) and stats[f] not in ('Unknown', ''))
        return round(present / len(key_fields), 2)

    # ========================================
    # TEAM MAPPING
    # ========================================

    def map_team(self, raw_data: Dict[str, Any]) -> ScoutProTeam:
        """
        Map Opta team data → ScoutProTeam

        Opta team format:
        {
            "@attributes": {"uID": "t14"},
            "Name": "Liverpool",
            "Country": "England",
            ...
        }
        """
        attrs = raw_data.get('@attributes', {})
        team_id = attrs.get('uID', raw_data.get('uID', ''))
        name = raw_data.get('Name', '')

        scoutpro_team = ScoutProTeam(
            id=self.generate_scoutpro_id('team', team_id),
            external_id=team_id,
            provider='opta',
            name=name,
            short_name=attrs.get('short_club_name'),
            country=attrs.get('country', raw_data.get('Country', '')),
            provider_ids={'opta': team_id},
            provider_data={
                'opta': {
                    'source': 'opta',
                    'last_updated': datetime.now(),
                    'data': raw_data
                }
            },
            data_quality={
                'completeness_score': 0.8,  # Opta team data is generally complete
                'data_sources': ['opta']
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        return scoutpro_team

    # ========================================
    # MATCH MAPPING
    # ========================================

    def map_match(self, raw_data: Dict[str, Any]) -> ScoutProMatch:
        """
        Map Opta match data → ScoutProMatch

        Opta match format (from F9 or F24):
        {
            "@attributes": {"uID": "g2187923"},
            "MatchInfo": {
                "Date": "2025-10-28T15:00:00",
                "Result": {"@attributes": {"Type": "Won"}},
                ...
            },
            "TeamData": [...]
        }
        """
        attrs = raw_data.get('@attributes', {})
        match_id = attrs.get('uID', raw_data.get('id', ''))

        # Extract match info
        match_info = raw_data.get('MatchInfo', {})
        match_date_str = match_info.get('Date', '')

        try:
            match_date = datetime.fromisoformat(match_date_str)
        except (ValueError, TypeError):
            match_date = datetime.now()

        # Extract team data and scores
        team_data_list = raw_data.get('TeamData', [])
        home_score = None
        away_score = None
        home_team_id = None
        away_team_id = None

        for team_data in team_data_list:
            td_attrs = team_data.get('@attributes', {})
            side = td_attrs.get('Side')
            team_ref = td_attrs.get('TeamRef')
            score = td_attrs.get('Score')

            if side == 'Home':
                home_team_id = team_ref
                if score:
                    home_score = int(score)
            elif side == 'Away':
                away_team_id = team_ref
                if score:
                    away_score = int(score)

        # Determine match status
        status = MatchStatus.SCHEDULED
        if match_info.get('Status') == 'Complete':
            status = MatchStatus.FINISHED
        elif match_info.get('Status') == 'Live':
            status = MatchStatus.LIVE

        scoutpro_match = ScoutProMatch(
            id=self.generate_scoutpro_id('match', match_id),
            external_id=match_id,
            provider='opta',
            home_team_id=self.generate_scoutpro_id('team', home_team_id) if home_team_id else '',
            away_team_id=self.generate_scoutpro_id('team', away_team_id) if away_team_id else '',
            competition_id='',  # Would need to be extracted from parent data
            season_id='',
            date=match_date,
            status=status,
            home_score=home_score,
            away_score=away_score,
            provider_ids={'opta': match_id},
            provider_data={
                'opta': {
                    'source': 'opta',
                    'last_updated': datetime.now(),
                    'data': raw_data
                }
            },
            data_quality={
                'completeness_score': 0.9,
                'data_sources': ['opta']
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        return scoutpro_match

    # ========================================
    # EVENT MAPPING (MAIN LOGIC)
    # ========================================

    def map_event(self, raw_data: Dict[str, Any]) -> Optional[ScoutProEvent]:
        """
        Map Opta F24 event → ScoutProEvent

        Opta F24 event format:
        {
            "@attributes": {
                "id": "evt123",
                "event_id": "1234",
                "type_id": "1",  # Event type
                "period_id": "1",
                "min": "15",
                "sec": "30",
                "team_id": "t14",
                "player_id": "p12345",
                "outcome": "1",  # 1=success, 0=failure
                "x": "65.2",
                "y": "48.7"
            },
            "Q": [  # Qualifiers
                {"@attributes": {"id": "q1", "qualifier_id": "140", "value": "82.1"}},
                {"@attributes": {"id": "q2", "qualifier_id": "141", "value": "52.3"}}
            ]
        }
        """
        attrs = raw_data.get('@attributes', {})

        # Extract basic attributes
        event_id = attrs.get('id', '')
        type_id = int(attrs.get('type_id', 0))
        outcome = int(attrs.get('outcome', 1))
        minute = int(attrs.get('min', 0))
        second = int(attrs.get('sec', 0))
        period = int(attrs.get('period_id', 1))
        x = float(attrs.get('x', 0))
        y = float(attrs.get('y', 0))
        player_id = attrs.get('player_id', '')
        team_id = attrs.get('team_id', '')

        # Extract qualifiers
        qualifiers_raw = raw_data.get('Q', [])
        qualifiers = self._parse_qualifiers(qualifiers_raw)

        # Map to canonical event type
        canonical_type = OptaEventTaxonomy.map_event_type(type_id, outcome, qualifiers)

        if canonical_type is None:
            # Unmapped event type - skip
            return None

        # Calculate timestamp
        timestamp_seconds = (minute * 60) + second

        # Extract pass end location if applicable
        end_x, end_y = None, None
        if OptaEventTaxonomy.is_pass_event(type_id):
            end_x, end_y = OptaEventTaxonomy.extract_pass_end_location(qualifiers)

        # Build rich attributes based on event type
        pass_attrs = None
        shot_attrs = None
        defensive_attrs = None

        if OptaEventTaxonomy.is_pass_event(type_id):
            pass_attrs = self._build_pass_attributes(qualifiers, end_x, end_y)

        elif OptaEventTaxonomy.is_shot_event(type_id):
            shot_attrs = self._build_shot_attributes(qualifiers)

        elif OptaEventTaxonomy.is_defensive_event(type_id):
            defensive_attrs = self._build_defensive_attributes(type_id, qualifiers)

        # Create canonical event
        scoutpro_event = ScoutProEvent(
            id=self.generate_scoutpro_id('event', event_id),
            match_id='',  # Would be set by context
            event_type=canonical_type,
            minute=minute,
            second=second,
            period=period,
            timestamp_seconds=timestamp_seconds,
            player_id=self.generate_scoutpro_id('player', player_id) if player_id else None,
            team_id=self.generate_scoutpro_id('team', team_id) if team_id else None,
            x=x,
            y=y,
            end_x=end_x,
            end_y=end_y,
            successful=(outcome == 1),
            quality_level=EventQuality.COMPREHENSIVE,
            pass_attrs=pass_attrs,
            shot_attrs=shot_attrs,
            defensive_attrs=defensive_attrs,
            provider='opta',
            external_id=event_id,
            provider_ids={'opta': event_id},
            provider_data={
                'opta': {
                    'source': 'opta',
                    'last_updated': datetime.now(),
                    'data': raw_data
                }
            },
            data_quality={
                'quality_level': EventQuality.COMPREHENSIVE.name,
                'completeness_score': 0.95,
                'data_sources': ['opta']
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        return scoutpro_event

    def map_events(self, raw_data_list: List[Dict[str, Any]]) -> List[ScoutProEvent]:
        """Map multiple Opta events"""
        events = []
        for raw_event in raw_data_list:
            event = self.map_event(raw_event)
            if event:  # Skip unmapped events
                events.append(event)
        return events

    # ========================================
    # HELPER METHODS
    # ========================================

    def _parse_qualifiers(self, qualifiers_raw: List[Dict]) -> Dict[int, str]:
        """
        Parse Opta qualifiers into dict

        Args:
            qualifiers_raw: List of qualifier objects

        Returns:
            Dict of qualifier_id → value
        """
        qualifiers = {}

        if isinstance(qualifiers_raw, list):
            for q in qualifiers_raw:
                attrs = q.get('@attributes', {})
                qualifier_id = int(attrs.get('qualifier_id', 0))
                value = attrs.get('value', '')
                qualifiers[qualifier_id] = value
        elif isinstance(qualifiers_raw, dict):
            # Single qualifier
            attrs = qualifiers_raw.get('@attributes', {})
            qualifier_id = int(attrs.get('qualifier_id', 0))
            value = attrs.get('value', '')
            qualifiers[qualifier_id] = value

        return qualifiers

    def _build_pass_attributes(
        self,
        qualifiers: Dict[int, str],
        end_x: Optional[float],
        end_y: Optional[float]
    ) -> PassAttributes:
        """Build PassAttributes from Opta qualifiers"""
        return PassAttributes(
            pass_type=self._determine_pass_type(qualifiers),
            pass_height=self._determine_pass_height(qualifiers),
            body_part=OptaEventTaxonomy.get_body_part(qualifiers),
            under_pressure=OptaEventTaxonomy.is_under_pressure(qualifiers),
            assisted_goal=OptaEventTaxonomy.is_assist(qualifiers),
            key_pass=OptaEventTaxonomy.is_key_pass(qualifiers),
            pass_length_m=self._get_pass_length(qualifiers),
            receiver_id=qualifiers.get(155),  # Q155 = receiver player ID
            corner_kick=6 in qualifiers,
            free_kick=5 in qualifiers,
            throw_in=107 in qualifiers,
            opta_qualifiers=qualifiers  # Preserve all qualifiers
        )

    def _build_shot_attributes(self, qualifiers: Dict[int, str]) -> ShotAttributes:
        """Build ShotAttributes from Opta qualifiers"""
        return ShotAttributes(
            body_part=OptaEventTaxonomy.get_body_part(qualifiers),
            shot_type='penalty' if OptaEventTaxonomy.is_penalty(qualifiers) else 'open_play',
            shot_technique='volley' if 22 in qualifiers else 'normal',
            blocked=82 in qualifiers,  # Q82 = blocked
            deflected=94 in qualifiers,  # Q94 = deflected
            one_on_one=214 in qualifiers,
            penalty=OptaEventTaxonomy.is_penalty(qualifiers),
            opta_qualifiers=qualifiers
        )

    def _build_defensive_attributes(
        self,
        type_id: int,
        qualifiers: Dict[int, str]
    ) -> DefensiveAttributes:
        """Build DefensiveAttributes from Opta qualifiers"""
        action_map = {
            7: 'tackle',
            8: 'interception',
            10: 'block',
            12: 'clearance'
        }

        return DefensiveAttributes(
            action_type=action_map.get(type_id),
            clearance_head=26 in qualifiers if type_id == 12 else None,
            blocked_shot=type_id == 10,
            opta_qualifiers=qualifiers
        )

    def _determine_pass_type(self, qualifiers: Dict[int, str]) -> Optional[str]:
        """Determine pass type from qualifiers"""
        if 2 in qualifiers:
            return 'cross'
        elif 5 in qualifiers:
            return 'through_ball'
        elif 1 in qualifiers:
            return 'long_ball'
        elif 6 in qualifiers:
            return 'flick_on'
        return 'short'

    def _determine_pass_height(self, qualifiers: Dict[int, str]) -> Optional[str]:
        """Determine pass height from qualifiers"""
        if 1 in qualifiers or 156 in qualifiers:
            return 'high'
        return 'ground'

    def _get_pass_length(self, qualifiers: Dict[int, str]) -> Optional[float]:
        """Extract pass length from qualifiers"""
        length_str = qualifiers.get(212)  # Q212 = pass length
        if length_str:
            try:
                return float(length_str)
            except (ValueError, TypeError):
                pass
        return None
