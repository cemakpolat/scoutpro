"""
MongoDB implementation of Statistics Repository
"""
import re
import math
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from .interfaces import IStatisticsRepository
import sys
sys.path.append('/app')
from shared.models.base import PlayerStatistics
import logging

logger = logging.getLogger(__name__)

# Threshold above which an ID is considered a ScoutPro 64-bit ID rather than
# a short Opta F24/F7 numeric ID (Opta IDs are generally <= 9 digits).
_SCOUTPRO_ID_MIN_DIGITS = 10


class MongoStatisticsRepository(IStatisticsRepository):
    """MongoDB implementation of statistics repository"""

    SHOT_EVENT_TYPES = {'shot', 'goal', 'miss', 'attempt_saved', 'blocked_shot', 'chance_missed', 'post'}

    @staticmethod
    def _append_identifier_variants(
        string_values: List[str],
        numeric_values: List[int],
        value: Any,
        prefix: str = '',
    ) -> None:
        if value in (None, ''):
            return

        raw_value = str(value).strip()
        if not raw_value:
            return

        if raw_value not in string_values:
            string_values.append(raw_value)

        stripped_value = raw_value
        if prefix and raw_value.lower().startswith(prefix.lower()):
            stripped_value = raw_value[1:]
            if stripped_value and stripped_value not in string_values:
                string_values.append(stripped_value)

        if stripped_value.isdigit():
            numeric_value = int(stripped_value)
            if numeric_value not in numeric_values:
                numeric_values.append(numeric_value)
            if prefix:
                prefixed_value = f'{prefix}{stripped_value}'
                if prefixed_value not in string_values:
                    string_values.append(prefixed_value)

    @staticmethod
    def _build_player_id_query(player_id: str) -> Dict[str, Any]:
        raw_value = str(player_id).strip()
        numeric_values = []
        string_values = [raw_value]

        # Player profiles and analytics frequently pass canonical ScoutPro IDs
        # like `scoutpro_player_opta_p77409`, while aggregated statistics are
        # stored under the Opta forms (`p77409` / `77409`). Normalize both.
        suffix_match = re.search(r'(p\d+|\d+)$', raw_value, re.IGNORECASE)
        if suffix_match:
            suffix_value = suffix_match.group(1)
            if suffix_value not in string_values:
                string_values.append(suffix_value)
            if suffix_value.lower().startswith('p') and suffix_value[1:].isdigit():
                numeric_candidate = int(suffix_value[1:])
                numeric_values.append(numeric_candidate)
                if suffix_value[1:] not in string_values:
                    string_values.append(suffix_value[1:])

        if raw_value.isdigit():
            numeric_values.append(int(raw_value))
        elif raw_value.lower().startswith('p') and raw_value[1:].isdigit():
            numeric_values.append(int(raw_value[1:]))

        numeric_values = list(dict.fromkeys(numeric_values))
        string_values = list(dict.fromkeys(string_values))

        or_clauses = []
        for field in ('playerID', 'player_id'):
            if numeric_values:
                or_clauses.append({field: {'$in': numeric_values}})
            or_clauses.append({field: {'$in': string_values}})

        if numeric_values:
            or_clauses.append({'_id': {'$in': numeric_values}})

        return {'$or': or_clauses}

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.player_stats_collection = db['player_statistics']
        self.player_stats_per90_collection = db['player_statistics_per90']
        self.team_stats_collection = db['team_statistics']
        self.match_events_collection = db['match_events']
        self.match_statistics_collection = db['match_statistics']
        self.match_tactical_snapshot_collection = db['match_tactical_snapshot']
        self.match_pass_network_collection = db['match_pass_network']
        self.match_sequence_summary_collection = db['match_sequence_summary']

    # ------------------------------------------------------------------
    # ID resolution: ScoutPro UUID → Opta numeric ID
    # ------------------------------------------------------------------

    async def _resolve_opta_player_id(self, player_id: str) -> Optional[str]:
        """Convert any incoming player ID to the short Opta numeric ID used in
        match events and the player_statistics collection.

        Lookup chain:
        1. If the ID is already short (Opta format, ≤9 digits), return as-is.
        2. Query the *players* collection by scoutpro_id (64-bit int).
        3. Return provider_ids.opta or strip 'p' from uID.
        """
        raw = str(player_id).strip()
        numeric_raw = raw.lstrip('p')

        # Already looks like a short Opta ID
        if numeric_raw.isdigit() and len(numeric_raw) < _SCOUTPRO_ID_MIN_DIGITS:
            return numeric_raw

        # Try resolving via the players collection
        try_values: List[Any] = [raw]
        try:
            try_values.append(int(raw))
        except (ValueError, TypeError):
            pass

        try:
            doc = await self.db['players'].find_one(
                {'scoutpro_id': {'$in': try_values}},
                {'provider_ids': 1, 'uID': 1}
            )
            if doc:
                opta = (doc.get('provider_ids') or {}).get('opta')
                if opta:
                    return str(opta).lstrip('p')
                uid = str(doc.get('uID') or '').lstrip('p')
                if uid:
                    return uid
        except Exception as exc:
            logger.warning('_resolve_opta_player_id lookup failed: %s', exc)

        return None

    async def _resolve_opta_team_id(self, team_id: str) -> Optional[str]:
        """Convert any incoming team ID to the short Opta numeric ID used in
        match events and the team_statistics collection.
        """
        raw = str(team_id).strip()
        numeric_raw = raw.lstrip('t')

        if numeric_raw.isdigit() and len(numeric_raw) < _SCOUTPRO_ID_MIN_DIGITS:
            return numeric_raw

        try_values: List[Any] = [raw]
        try:
            try_values.append(int(raw))
        except (ValueError, TypeError):
            pass

        try:
            doc = await self.db['teams'].find_one(
                {'scoutpro_id': {'$in': try_values}},
                {'provider_ids': 1, 'uID': 1}
            )
            if doc:
                opta = (doc.get('provider_ids') or {}).get('opta')
                if opta:
                    return str(opta).lstrip('t')
                uid = str(doc.get('uID') or '').lstrip('t')
                if uid:
                    return uid
        except Exception as exc:
            logger.warning('_resolve_opta_team_id lookup failed: %s', exc)

        return None

    @classmethod
    def _build_match_lookup_query(cls, match_id: str) -> Dict[str, Any]:
        string_values: List[str] = []
        numeric_values: List[int] = []
        cls._append_identifier_variants(string_values, numeric_values, match_id, prefix='g')

        or_clauses: List[Dict[str, Any]] = []
        if string_values:
            or_clauses.extend([
                {'uID': {'$in': string_values}},
                {'provider_ids.opta': {'$in': string_values}},
                {'matchID': {'$in': string_values}},
                {'id': {'$in': string_values}},
                {'scoutpro_id': {'$in': string_values}},
            ])
        if numeric_values:
            or_clauses.extend([
                {'matchID': {'$in': numeric_values}},
                {'id': {'$in': numeric_values}},
                {'scoutpro_id': {'$in': numeric_values}},
            ])

        return {'$or': or_clauses} if or_clauses else {'uID': str(match_id)}

    @classmethod
    def _build_match_event_lookup_query(cls, match_id: str) -> Dict[str, Any]:
        string_values: List[str] = []
        numeric_values: List[int] = []
        cls._append_identifier_variants(string_values, numeric_values, match_id, prefix='g')

        or_clauses: List[Dict[str, Any]] = []
        for field in ('matchID', 'match_id', 'scoutpro_match_id'):
            if string_values:
                or_clauses.append({field: {'$in': string_values}})
            if numeric_values:
                or_clauses.append({field: {'$in': numeric_values}})

        return {'$or': or_clauses} if or_clauses else {'matchID': str(match_id)}

    async def _build_match_projection_lookup_query(self, match_id: str) -> Dict[str, Any]:
        opta_match_ids: List[str] = []
        scoutpro_match_ids: List[Any] = []

        def ingest_identifier(value: Any) -> None:
            if value in (None, ''):
                return

            raw_value = str(value).strip()
            if not raw_value:
                return

            if raw_value.lower().startswith('g'):
                raw_value = raw_value[1:]

            if not raw_value.isdigit():
                return

            if len(raw_value) < _SCOUTPRO_ID_MIN_DIGITS:
                if raw_value not in opta_match_ids:
                    opta_match_ids.append(raw_value)
                return

            numeric_value = int(raw_value)
            if numeric_value not in scoutpro_match_ids:
                scoutpro_match_ids.append(numeric_value)
            if raw_value not in scoutpro_match_ids:
                scoutpro_match_ids.append(raw_value)

        ingest_identifier(match_id)

        match_doc = await self.db['matches'].find_one(
            self._build_match_lookup_query(match_id),
            {'_id': 0, 'uID': 1, 'id': 1, 'scoutpro_id': 1, 'matchID': 1, 'provider_ids': 1},
        )
        if match_doc:
            ingest_identifier(match_doc.get('uID'))
            ingest_identifier(match_doc.get('matchID'))
            ingest_identifier(match_doc.get('id'))
            ingest_identifier(match_doc.get('scoutpro_id'))
            ingest_identifier((match_doc.get('provider_ids') or {}).get('opta'))

        if not opta_match_ids or not scoutpro_match_ids:
            event_doc = await self.match_events_collection.find_one(
                self._build_match_event_lookup_query(match_id),
                {'_id': 0, 'matchID': 1, 'match_id': 1, 'scoutpro_match_id': 1},
            )
            if event_doc:
                ingest_identifier(event_doc.get('matchID'))
                ingest_identifier(event_doc.get('match_id'))
                ingest_identifier(event_doc.get('scoutpro_match_id'))

        clauses: List[Dict[str, Any]] = []
        if opta_match_ids:
            clauses.append({'match_id': {'$in': opta_match_ids}})
        if scoutpro_match_ids:
            clauses.append({'scoutpro_match_id': {'$in': scoutpro_match_ids}})

        if not clauses:
            clauses.append({'match_id': str(match_id)})

        return {'$or': clauses} if len(clauses) > 1 else clauses[0]

    async def _find_match_projection_doc(
        self,
        collection,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        doc = await collection.find_one(await self._build_match_projection_lookup_query(match_id))
        if doc:
            doc.pop('_id', None)
        return doc

    # ------------------------------------------------------------------
    # Season-level aggregation (sum per-match docs)
    # ------------------------------------------------------------------

    _PLAYER_SUM_FIELDS = [
        'passes', 'passes_successful', 'crosses', 'crosses_successful',
        'shots', 'shots_on_target', 'goals', 'tackles', 'tackles_successful',
        'interceptions', 'clearances', 'aerials', 'aerials_won',
        'fouls_committed', 'yellow_cards', 'red_cards', 'ball_recoveries',
        'progressive_passes', 'entered_final_third', 'entered_box',
        'total_xg', 'high_regains', 'minutes_played', 'total_events',
        # legacy field names from older batch runs
        'total_tackles', 'total_passes', 'total_shots', 'total_interceptions',
        'total_clearances', 'goal_assist', 'assists',
        # event pipeline rich additive metrics
        'passes_total', 'passes_completed', 'passes_unsuccessful',
        'forward_passes', 'backward_passes', 'sideway_passes',
        'total_crosses', 'successful_crosses',
        'long_passes', 'successful_long_passes',
        'through_ball', 'through_balls', 'through_ball_successful', 'through_balls_successful',
        'total_corners', 'blocked_passes', 'total_free_kicks_taken',
        'passes_into_box', 'final_third_entries', 'set_piece_passes',
        'long_balls', 'switches_of_play', 'pass_length_total',
        'total_shots', 'shots_inside_box', 'shots_outside_box',
        'goals_inside_the_box', 'goals_outside_the_box',
        'headed_goals', 'headed_shots', 'goals_from_set_play',
        'goals_from_open_play', 'goals_from_penalties', 'blocked_shot',
        'non_penalty_goals', 'big_chances', 'big_chances_scored',
        'set_piece_shots', 'xg_total', 'shots_with_xg', 'shot_distance_total',
        'xA', 'xa_total', 'total_xa', 'passes_with_xa',
        'total_assists', 'intentional_assists', 'assists_from_open_play',
        'assists_from_set_play', 'assists_from_free_kick', 'assists_from_corners',
        'assists_from_throw_in', 'assists_from_goal_kick',
        'key_passes', 'key_passes_after_dribble', 'key_pass_corner',
        'key_pass_free_kick', 'assist_and_key_passes',
        'chances_created_from_open_play', 'chances_created_from_set_play',
        'total_touches', 'total_touches_in_attacking_third',
        'total_touches_in_middle_third', 'total_touches_in_defensive_third',
        'total_touches_in_box', 'turnover', 'total_successful_tackles',
        'tackle_attempts', 'last_man_tackles', 'total_ball_recovery',
        'total_recoveries_in_defensive_third', 'total_recoveries_in_middle_third',
        'total_recoveries_in_attacking_third', 'total_interceptions_in_defensive_third',
        'total_interceptions_in_middle_third', 'total_interceptions_in_attacking_third',
        'total_clearances_in_defensive_third', 'recoveries', 'pressures', 'blocks',
        'total_aerial_duels', 'aerial_duels_won', 'aerial_duels_lost',
        'aerial_duels_in_attacking_half', 'aerial_duels_in_defending_half',
        'aerial_duels_in_attacking_third', 'aerial_duels_in_middle_third',
        'aerial_duels_in_defending_third',
        'total_duels', 'duels', 'successful_duels', 'unsuccessful_duels', 'duels_won',
        'defensive_duels', 'offensive_duels', 'total_ground_duels',
        'successful_ground_duels', 'unsuccessful_ground_duels',
        'duels_in_attacking_third', 'duels_in_middle_third', 'duels_in_defending_third',
        'total_take_ons', 'take_ons', 'successful_take_ons', 'take_ons_won',
        'unsuccessful_take_ons', 'take_on_overrun', 'take_ons_in_attacking_third',
        'take_ons_in_box', 'successful_take_ons_in_box', 'times_tackled',
        'fouls', 'fouls_won', 'handball_conceded', 'penalty_conceded', 'penalty_won',
        'fouls_won_in_defending_third', 'fouls_won_in_middle_third',
        'fouls_won_in_attacking_third', 'fouls_committed_in_defending_third',
        'fouls_committed_in_middle_third', 'fouls_committed_in_attacking_third',
        'second_yellow_cards', 'card_rescinded', 'total_cards', 'cards',
        'total_dispossessed', 'total_errors', 'errors_led_to_goal',
        'errors_led_to_shot', 'caught_offside', 'ball_touches',
        'ball_controls', 'dispossessions', 'matches_played',
        'games_played', 'games_started', 'substitute_on', 'substitute_off',
        'goalkeeper_actions', 'saves', 'goals_against', 'clean_sheet',
        'gk_sweeper', 'accurate_keeper_sweeper', 'crosses_faced',
        'crosses_claimed', 'crosses_punched', 'crosses_not_claimed',
        'gk_pick_ups', 'goal_kicks', 'successful_goal_kicks', 'gk_throws',
        'successful_gk_throws', 'gk_smother', 'penalty_faced',
        'penalties_saved', 'penalties_scored', 'penalties_missed',
        'shots_against', 'shots_on_target_against', 'team_own_goals',
        'saves_from_own_player', 'save_body', 'save_caught', 'save_diving',
        'save_feet', 'save_hands', 'save_penalty', 'save_inside_box', 'save_outside_box',
    ]

    @staticmethod
    def _safe_rate(numerator: Any, denominator: Any) -> float:
        try:
            denominator_value = float(denominator or 0)
            if denominator_value <= 0:
                return 0.0
            return round(float(numerator or 0) / denominator_value * 100, 2)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _per_90(value: Any, minutes_played: Any) -> float:
        try:
            minute_total = float(minutes_played or 0)
            if minute_total <= 0:
                return 0.0
            return round(float(value or 0) * 90.0 / minute_total, 2)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _stat_value(doc: Dict[str, Any], *keys: str) -> float:
        for key in keys:
            value = doc.get(key)
            if value not in (None, ''):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return 0.0

    @classmethod
    def _apply_player_derived_metrics(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        passes = cls._stat_value(doc, 'passes', 'passes_total', 'total_passes')
        passes_successful = cls._stat_value(doc, 'passes_successful', 'passes_completed')
        shots = cls._stat_value(doc, 'shots', 'total_shots')
        shots_on_target = cls._stat_value(doc, 'shots_on_target')
        goals = cls._stat_value(doc, 'goals')
        big_chances = cls._stat_value(doc, 'big_chances')
        big_chances_scored = cls._stat_value(doc, 'big_chances_scored')
        take_ons = cls._stat_value(doc, 'take_ons', 'total_take_ons')
        take_ons_won = cls._stat_value(doc, 'take_ons_won', 'successful_take_ons')
        duels = cls._stat_value(doc, 'duels', 'total_duels')
        duels_won = cls._stat_value(doc, 'duels_won', 'successful_duels')
        aerials = cls._stat_value(doc, 'aerials', 'total_aerial_duels')
        aerials_won = cls._stat_value(doc, 'aerials_won', 'aerial_duels_won')
        tackles = cls._stat_value(doc, 'tackles', 'total_tackles')
        tackles_successful = cls._stat_value(doc, 'tackles_successful', 'total_successful_tackles')
        minutes_played = cls._stat_value(doc, 'minutes_played')
        xg_total = cls._stat_value(doc, 'total_xg', 'xg_total')
        assists = cls._stat_value(doc, 'assists', 'total_assists', 'goal_assist')
        key_passes = cls._stat_value(doc, 'key_passes')
        progressive_passes = cls._stat_value(doc, 'progressive_passes')
        recoveries = cls._stat_value(doc, 'ball_recoveries', 'total_ball_recovery', 'recoveries')
        interceptions = cls._stat_value(doc, 'interceptions', 'total_interceptions')

        doc['pass_accuracy'] = cls._safe_rate(passes_successful, passes)
        doc['pass_success_rate'] = doc['pass_accuracy']
        doc['shot_accuracy'] = cls._safe_rate(shots_on_target, shots)
        doc['conversion_rate'] = cls._safe_rate(goals, shots)
        doc['big_chance_conversion_rate'] = cls._safe_rate(big_chances_scored, big_chances)
        doc['progressive_pass_rate'] = cls._safe_rate(progressive_passes, passes)
        doc['take_on_success_rate'] = cls._safe_rate(take_ons_won, take_ons)
        doc['duel_success_rate'] = cls._safe_rate(duels_won, duels)
        doc['aerial_duel_success_rate'] = cls._safe_rate(aerials_won, aerials)
        doc['tackle_success_rate'] = cls._safe_rate(tackles_successful, tackles)
        doc['goals_per_90'] = cls._per_90(goals, minutes_played)
        doc['assists_per_90'] = cls._per_90(assists, minutes_played)
        doc['xg_per_90'] = cls._per_90(xg_total, minutes_played)
        doc['key_passes_per_90'] = cls._per_90(key_passes, minutes_played)
        doc['progressive_passes_per_90'] = cls._per_90(progressive_passes, minutes_played)
        doc['recoveries_per_90'] = cls._per_90(recoveries, minutes_played)
        doc['interceptions_per_90'] = cls._per_90(interceptions, minutes_played)
        return doc

    async def _get_player_season_aggregate(
        self,
        opta_player_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Aggregate all per-match player_statistics documents into season totals."""
        match_filter: Dict[str, Any] = {
            'player_id': {'$in': [opta_player_id, f'p{opta_player_id}', int(opta_player_id)]}
        }
        if competition_id:
            match_filter['competition_id'] = {'$in': [str(competition_id), competition_id]}
        if season_id:
            match_filter['season_id'] = {'$in': [str(season_id), season_id]}

        group_stage: Dict[str, Any] = {
            '_id': '$player_id',
            'matches_played': {'$sum': 1},
            'team_id': {'$first': '$team_id'},
            'scoutpro_player_id': {'$first': '$scoutpro_player_id'},
            'scoutpro_team_id': {'$first': '$scoutpro_team_id'},
            'competition_id': {'$first': '$competition_id'},
            'season_id': {'$first': '$season_id'},
        }
        for field in self._PLAYER_SUM_FIELDS:
            group_stage[field] = {'$sum': {'$ifNull': [f'${field}', 0]}}

        pipeline = [
            {'$match': match_filter},
            {'$group': group_stage},
        ]

        try:
            docs = await self.player_stats_collection.aggregate(pipeline).to_list(1)
        except Exception as exc:
            logger.error('_get_player_season_aggregate error: %s', exc)
            return None

        if not docs:
            return None

        doc = docs[0]
        doc.pop('_id', None)

        # Use ScoutPro ID as the canonical identifier; keep Opta ID for reference.
        sp_player_id = doc.get('scoutpro_player_id') or opta_player_id
        doc['id'] = sp_player_id
        doc['player_id'] = sp_player_id
        doc['opta_player_id'] = opta_player_id
        # Also promote team ID
        if doc.get('scoutpro_team_id'):
            doc['opta_team_id'] = doc.get('team_id')
            doc['team_id'] = doc['scoutpro_team_id']

        cls = self.__class__
        cls._finalize_player_aggregate_doc(doc)

        doc['data_source'] = 'player_statistics_aggregate'
        return doc

    _TEAM_SUM_FIELDS = [
        'passes', 'passes_successful', 'shots', 'goals', 'tackles',
        'interceptions', 'clearances', 'fouls', 'yellow_cards', 'red_cards',
        'total_events', 'total_xg',
        'passes_completed', 'progressive_passes', 'final_third_entries',
        'passes_into_box', 'crosses', 'through_balls', 'long_balls',
        'key_passes', 'assists', 'second_assists', 'set_piece_passes',
        'pass_length_total', 'shots_on_target', 'big_chances', 'big_chances_scored',
        'set_piece_shots', 'xg_total', 'shots_with_xg', 'headed_shots',
        'cards', 'duels', 'duels_won', 'aerials', 'aerials_won',
        'take_ons', 'take_ons_won', 'high_regains', 'tackles_won',
        'goalkeeper_actions', 'saves', 'recoveries', 'ball_controls',
        'dispossessions', 'blocks', 'pressures', 'corners', 'goals_against',
        'shots_against', 'shots_on_target_against', 'passes_against', 'total_xg_against',
    ]

    _PLAYER_METRIC_ALIASES = {
        'goals': ['goals'],
        'assists': ['assists', 'goal_assist', 'total_assists'],
        'passes': ['passes', 'total_passes', 'passes_total'],
        'successfulpasses': ['passes_successful', 'passes_completed', 'successful_passes', 'successfulPasses'],
        'passaccuracy': ['pass_accuracy', 'pass_success_rate', 'passAccuracy'],
        'shots': ['shots', 'total_shots'],
        'shotsontarget': ['shots_on_target', 'shotsOnTarget'],
        'xg': ['total_xg', 'xg_total', 'xG'],
        'xa': ['total_xa', 'xa_total', 'xA'],
        'keypasses': ['key_passes', 'keyPasses'],
        'progressivepasses': ['progressive_passes', 'progressivePasses'],
        'matchesplayed': ['matches_played', 'appearances', 'games_played', 'matchesPlayed'],
        'goalsper90': ['goals_per_90', 'goalsPer90'],
        'assistsper90': ['assists_per_90', 'assistsPer90'],
        'xgper90': ['xg_per_90', 'xGPer90'],
        'takeonsuccessrate': ['take_on_success_rate', 'takeOnSuccessRate'],
        'duelsuccessrate': ['duel_success_rate', 'duelSuccessRate'],
        'aerialduelsuccessrate': ['aerial_duel_success_rate', 'aerialDuelSuccessRate'],
        'recoveriesper90': ['recoveries_per_90', 'recoveriesPer90'],
        'interceptionsper90': ['interceptions_per_90', 'interceptionsPer90'],
    }

    _TEAM_METRIC_ALIASES = {
        'goals': ['goals'],
        'goalsagainst': ['goals_against', 'goalsAgainst'],
        'passes': ['passes'],
        'passaccuracy': ['pass_accuracy', 'passAccuracy'],
        'shots': ['shots'],
        'shotsontarget': ['shots_on_target', 'shotsOnTarget'],
        'xg': ['total_xg', 'xg_total', 'xG'],
        'xgagainst': ['total_xg_against', 'xGAgainst'],
        'possessionpercentage': ['possession_percentage', 'possessionPercentage'],
        'goalspermatch': ['goals_per_match', 'goalsPerMatch'],
        'xgpermatch': ['xg_per_match', 'xGPerMatch'],
        'xgagainstpermatch': ['xg_against_per_match', 'xGAgainstPerMatch'],
        'shotspermatch': ['shots_per_match', 'shotsPerMatch'],
        'shotsontargetpermatch': ['shots_on_target_per_match', 'shotsOnTargetPerMatch'],
        'keypassespermatch': ['key_passes_per_match', 'keyPassesPerMatch'],
        'progressivepassespermatch': ['progressive_passes_per_match', 'progressivePassesPerMatch'],
        'highregainspermatch': ['high_regains_per_match', 'highRegainsPerMatch'],
    }

    _DEFAULT_PLAYER_COMPARISON_METRICS = [
        'goals',
        'assists',
        'passAccuracy',
        'shots',
        'xG',
        'xA',
        'keyPasses',
        'progressivePasses',
    ]

    _MATCH_ADVANCED_FLAT_FIELDS = [
        'home_goals', 'away_goals',
        'home_shots', 'away_shots',
        'home_shots_on_target', 'away_shots_on_target',
        'home_xg', 'away_xg',
        'home_passes', 'away_passes',
        'home_passes_successful', 'away_passes_successful',
        'home_pass_accuracy', 'away_pass_accuracy',
        'home_progressive_passes', 'away_progressive_passes',
        'home_passes_into_box', 'away_passes_into_box',
        'home_key_passes', 'away_key_passes',
        'home_through_balls', 'away_through_balls',
        'home_corners', 'away_corners',
        'home_big_chances', 'away_big_chances',
        'home_tackles', 'away_tackles',
        'home_interceptions', 'away_interceptions',
        'home_clearances', 'away_clearances',
        'home_recoveries', 'away_recoveries',
        'home_high_regains', 'away_high_regains',
        'home_fouls', 'away_fouls',
        'home_yellow_cards', 'away_yellow_cards',
        'home_red_cards', 'away_red_cards',
        'total_events',
    ]

    @staticmethod
    def _build_competition_filter(competition_id: Optional[int]) -> Dict[str, Any]:
        if competition_id in (None, ''):
            return {}

        values = [competition_id, str(competition_id)]
        return {
            '$or': [
                {'competition_id': {'$in': values}},
                {'competitionID': {'$in': values}},
            ]
        }

    @staticmethod
    def _normalize_metric_name(metric_name: str) -> str:
        snake = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', str(metric_name or '').strip()).lower()
        return re.sub(r'[^a-z0-9]+', '', snake)

    @classmethod
    def _metric_candidates(cls, metric_name: str, alias_map: Dict[str, List[str]]) -> List[str]:
        raw = str(metric_name or '').strip()
        snake = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', raw).lower() if raw else ''
        candidates: List[str] = []
        for key in (raw, snake):
            if key and key not in candidates:
                candidates.append(key)
        for key in alias_map.get(cls._normalize_metric_name(metric_name), []):
            if key not in candidates:
                candidates.append(key)
        return candidates

    @classmethod
    def _metric_value(cls, doc: Dict[str, Any], metric_name: str, alias_map: Dict[str, List[str]]) -> float:
        candidates = cls._metric_candidates(metric_name, alias_map)
        return cls._stat_value(doc, *candidates) if candidates else 0.0

    @classmethod
    def _apply_player_output_aliases(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        doc['playerID'] = doc.get('playerID') or doc.get('player_id')
        doc['successful_passes'] = cls._stat_value(doc, 'successful_passes', 'passes_successful', 'passes_completed')
        doc['successfulPasses'] = doc['successful_passes']
        doc['passAccuracy'] = cls._stat_value(doc, 'pass_accuracy', 'pass_success_rate', 'passAccuracy')
        doc['shotsOnTarget'] = cls._stat_value(doc, 'shots_on_target', 'shotsOnTarget')
        doc['xG'] = round(cls._stat_value(doc, 'total_xg', 'xg_total', 'xG'), 4)
        doc['xA'] = round(cls._stat_value(doc, 'total_xa', 'xa_total', 'xA'), 4)
        doc['keyPasses'] = cls._stat_value(doc, 'key_passes', 'keyPasses')
        doc['progressivePasses'] = cls._stat_value(doc, 'progressive_passes', 'progressivePasses')
        doc['matchesPlayed'] = cls._stat_value(doc, 'matches_played', 'appearances', 'games_played', 'matchesPlayed')
        doc['goalsPer90'] = cls._stat_value(doc, 'goals_per_90', 'goalsPer90')
        doc['assistsPer90'] = cls._stat_value(doc, 'assists_per_90', 'assistsPer90')
        doc['xGPer90'] = cls._stat_value(doc, 'xg_per_90', 'xGPer90')
        doc['takeOnSuccessRate'] = cls._stat_value(doc, 'take_on_success_rate', 'takeOnSuccessRate')
        doc['duelSuccessRate'] = cls._stat_value(doc, 'duel_success_rate', 'duelSuccessRate')
        doc['aerialDuelSuccessRate'] = cls._stat_value(doc, 'aerial_duel_success_rate', 'aerialDuelSuccessRate')
        return doc

    @classmethod
    def _apply_team_output_aliases(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        doc['teamID'] = doc.get('teamID') or doc.get('opta_team_id') or doc.get('team_id')
        doc['passAccuracy'] = cls._stat_value(doc, 'pass_accuracy', 'passAccuracy')
        doc['shotsOnTarget'] = cls._stat_value(doc, 'shots_on_target', 'shotsOnTarget')
        doc['xG'] = round(cls._stat_value(doc, 'total_xg', 'xg_total', 'xG'), 4)
        doc['xGAgainst'] = round(cls._stat_value(doc, 'total_xg_against', 'xGAgainst'), 4)
        doc['possessionPercentage'] = cls._stat_value(doc, 'possession_percentage', 'possessionPercentage')
        doc['goalsPerMatch'] = cls._stat_value(doc, 'goals_per_match', 'goalsPerMatch')
        doc['xGPerMatch'] = cls._stat_value(doc, 'xg_per_match', 'xGPerMatch')
        doc['xGAgainstPerMatch'] = cls._stat_value(doc, 'xg_against_per_match', 'xGAgainstPerMatch')
        doc['shotsPerMatch'] = cls._stat_value(doc, 'shots_per_match', 'shotsPerMatch')
        doc['shotsOnTargetPerMatch'] = cls._stat_value(doc, 'shots_on_target_per_match', 'shotsOnTargetPerMatch')
        doc['keyPassesPerMatch'] = cls._stat_value(doc, 'key_passes_per_match', 'keyPassesPerMatch')
        doc['progressivePassesPerMatch'] = cls._stat_value(doc, 'progressive_passes_per_match', 'progressivePassesPerMatch')
        doc['highRegainsPerMatch'] = cls._stat_value(doc, 'high_regains_per_match', 'highRegainsPerMatch')
        return doc

    @classmethod
    def _finalize_player_aggregate_doc(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        matches_played = int(cls._stat_value(doc, 'matches_played', 'appearances', 'games_played'))
        doc['matches_played'] = matches_played
        doc['appearances'] = matches_played
        doc['games_played'] = matches_played
        doc['goals'] = cls._stat_value(doc, 'goals')
        doc['assists'] = cls._stat_value(doc, 'assists', 'goal_assist', 'total_assists')
        doc['total_shots'] = cls._stat_value(doc, 'total_shots', 'shots')
        doc['total_tackles'] = cls._stat_value(doc, 'total_tackles', 'tackles')
        doc['total_interceptions'] = cls._stat_value(doc, 'total_interceptions', 'interceptions')
        doc['total_clearances'] = cls._stat_value(doc, 'total_clearances', 'clearances')
        doc['total_passes'] = cls._stat_value(doc, 'total_passes', 'passes', 'passes_total')
        cls._apply_player_derived_metrics(doc)
        cls._apply_player_output_aliases(doc)
        return doc

    @classmethod
    def _finalize_team_aggregate_doc(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        doc['matches_played'] = int(cls._stat_value(doc, 'matches_played'))
        cls._apply_team_derived_metrics(doc)
        cls._apply_team_output_aliases(doc)
        return doc

    async def _fetch_player_metadata_map(self, player_ids: List[Any]) -> Dict[str, Dict[str, Any]]:
        metadata: Dict[str, Dict[str, Any]] = {}
        if not player_ids:
            return metadata

        string_values: List[str] = []
        numeric_values: List[int] = []
        for player_id in player_ids:
            self._append_identifier_variants(string_values, numeric_values, player_id, prefix='p')

        query_clauses: List[Dict[str, Any]] = []
        for field in ('uID', 'provider_ids.opta', 'scoutpro_id', 'id'):
            if string_values:
                query_clauses.append({field: {'$in': string_values}})
            if numeric_values and field in ('uID', 'scoutpro_id', 'id'):
                query_clauses.append({field: {'$in': numeric_values}})

        if not query_clauses:
            return metadata

        cursor = self.db['players'].find(
            {'$or': query_clauses},
            {
                '_id': 0,
                'uID': 1,
                'provider_ids': 1,
                'scoutpro_id': 1,
                'id': 1,
                'name': 1,
                'position': 1,
                'detailed_position': 1,
                'raw_position': 1,
                'club': 1,
                'team_name': 1,
                'nationality': 1,
                'age': 1,
            },
        )
        async for player in cursor:
            for key in (
                player.get('uID'),
                (player.get('provider_ids') or {}).get('opta'),
                player.get('scoutpro_id'),
                player.get('id'),
            ):
                if key not in (None, ''):
                    metadata[str(key)] = player

        return metadata

    async def _fetch_team_metadata_map(self, team_ids: List[Any]) -> Dict[str, Dict[str, Any]]:
        metadata: Dict[str, Dict[str, Any]] = {}
        if not team_ids:
            return metadata

        string_values: List[str] = []
        numeric_values: List[int] = []
        for team_id in team_ids:
            self._append_identifier_variants(string_values, numeric_values, team_id, prefix='t')

        query_clauses: List[Dict[str, Any]] = []
        for field in ('uID', 'provider_ids.opta', 'scoutpro_id', 'id'):
            if string_values:
                query_clauses.append({field: {'$in': string_values}})
            if numeric_values and field in ('uID', 'scoutpro_id', 'id'):
                query_clauses.append({field: {'$in': numeric_values}})

        if not query_clauses:
            return metadata

        cursor = self.db['teams'].find(
            {'$or': query_clauses},
            {'_id': 0, 'uID': 1, 'provider_ids': 1, 'scoutpro_id': 1, 'id': 1, 'name': 1, 'country': 1},
        )
        async for team in cursor:
            for key in (
                team.get('uID'),
                (team.get('provider_ids') or {}).get('opta'),
                team.get('scoutpro_id'),
                team.get('id'),
            ):
                if key not in (None, ''):
                    metadata[str(key)] = team

        return metadata

    @staticmethod
    def _position_matches(position_filter: Optional[str], metadata: Dict[str, Any], doc: Dict[str, Any]) -> bool:
        if not position_filter:
            return True

        normalized = str(position_filter).strip().lower()
        for candidate in (
            metadata.get('position'),
            metadata.get('detailed_position'),
            metadata.get('raw_position'),
            doc.get('player_position'),
            doc.get('position'),
        ):
            if candidate and normalized in str(candidate).lower():
                return True
        return False

    async def _aggregate_player_documents(self, competition_id: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        query = self._build_competition_filter(competition_id)
        aggregates: Dict[str, Dict[str, Any]] = {}

        cursor = self.player_stats_collection.find(query)
        async for raw_doc in cursor:
            player_key = raw_doc.get('player_id') or raw_doc.get('playerID')
            if player_key in (None, ''):
                continue

            opta_player_id = str(player_key).lstrip('p')
            bucket = aggregates.setdefault(
                opta_player_id,
                {
                    'player_id': opta_player_id,
                    'opta_player_id': opta_player_id,
                    'scoutpro_player_id': None,
                    'competition_id': raw_doc.get('competition_id') or raw_doc.get('competitionID'),
                    'season_id': raw_doc.get('season_id') or raw_doc.get('seasonID'),
                    '_match_ids': set(),
                },
            )

            if bucket.get('scoutpro_player_id') in (None, '') and raw_doc.get('scoutpro_player_id') not in (None, ''):
                bucket['scoutpro_player_id'] = str(raw_doc.get('scoutpro_player_id'))

            match_key = raw_doc.get('match_id') or raw_doc.get('matchID')
            if match_key not in (None, ''):
                bucket['_match_ids'].add(str(match_key))

            for field in self._PLAYER_SUM_FIELDS:
                value = raw_doc.get(field)
                if isinstance(value, (int, float)):
                    bucket[field] = bucket.get(field, 0) + value

        for bucket in aggregates.values():
            bucket['matches_played'] = len(bucket.pop('_match_ids', set()))
            self.__class__._finalize_player_aggregate_doc(bucket)

        return aggregates

    async def _aggregate_team_documents(self, competition_id: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        query = self._build_competition_filter(competition_id)
        aggregates: Dict[str, Dict[str, Any]] = {}

        cursor = self.team_stats_collection.find(query)
        async for raw_doc in cursor:
            team_key = raw_doc.get('team_id') or raw_doc.get('teamID')
            if team_key in (None, ''):
                continue

            opta_team_id = str(team_key).lstrip('t')
            bucket = aggregates.setdefault(
                opta_team_id,
                {
                    'team_id': opta_team_id,
                    'opta_team_id': opta_team_id,
                    'scoutpro_team_id': None,
                    'competition_id': raw_doc.get('competition_id') or raw_doc.get('competitionID'),
                    'season_id': raw_doc.get('season_id') or raw_doc.get('seasonID'),
                    '_match_ids': set(),
                },
            )

            if bucket.get('scoutpro_team_id') in (None, '') and raw_doc.get('scoutpro_team_id') not in (None, ''):
                bucket['scoutpro_team_id'] = str(raw_doc.get('scoutpro_team_id'))

            match_key = raw_doc.get('match_id') or raw_doc.get('matchID')
            if match_key not in (None, ''):
                bucket['_match_ids'].add(str(match_key))

            for field in self._TEAM_SUM_FIELDS:
                value = raw_doc.get(field)
                if isinstance(value, (int, float)):
                    bucket[field] = bucket.get(field, 0) + value

        for bucket in aggregates.values():
            bucket['matches_played'] = len(bucket.pop('_match_ids', set()))
            self.__class__._finalize_team_aggregate_doc(bucket)

        return aggregates

    @classmethod
    def _extract_match_flat_metrics(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            field: doc.get(field)
            for field in cls._MATCH_ADVANCED_FLAT_FIELDS
            if field in doc
        }

    @classmethod
    def _apply_team_derived_metrics(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        matches_played = cls._stat_value(doc, 'matches_played') or 0.0
        passes = cls._stat_value(doc, 'passes')
        passes_successful = cls._stat_value(doc, 'passes_successful', 'passes_completed')
        passes_against = cls._stat_value(doc, 'passes_against')
        shots = cls._stat_value(doc, 'shots')
        shots_on_target = cls._stat_value(doc, 'shots_on_target')
        goals = cls._stat_value(doc, 'goals')
        goals_against = cls._stat_value(doc, 'goals_against')
        big_chances = cls._stat_value(doc, 'big_chances')
        big_chances_scored = cls._stat_value(doc, 'big_chances_scored')
        progressive_passes = cls._stat_value(doc, 'progressive_passes')
        take_ons = cls._stat_value(doc, 'take_ons')
        take_ons_won = cls._stat_value(doc, 'take_ons_won')
        duels = cls._stat_value(doc, 'duels')
        duels_won = cls._stat_value(doc, 'duels_won')
        aerials = cls._stat_value(doc, 'aerials')
        aerials_won = cls._stat_value(doc, 'aerials_won')
        xg_total = cls._stat_value(doc, 'total_xg', 'xg_total')
        xg_against = cls._stat_value(doc, 'total_xg_against')

        doc['pass_accuracy'] = cls._safe_rate(passes_successful, passes)
        doc['shot_accuracy'] = cls._safe_rate(shots_on_target, shots)
        doc['conversion_rate'] = cls._safe_rate(goals, shots)
        doc['big_chance_conversion_rate'] = cls._safe_rate(big_chances_scored, big_chances)
        doc['progressive_pass_rate'] = cls._safe_rate(progressive_passes, passes)
        doc['take_on_success_rate'] = cls._safe_rate(take_ons_won, take_ons)
        doc['duel_success_rate'] = cls._safe_rate(duels_won, duels)
        doc['aerial_duel_success_rate'] = cls._safe_rate(aerials_won, aerials)
        doc['possession_percentage'] = cls._safe_rate(passes, passes + passes_against)
        doc['goals_per_match'] = round(goals / matches_played, 2) if matches_played else 0.0
        doc['goals_against_per_match'] = round(goals_against / matches_played, 2) if matches_played else 0.0
        doc['xg_per_match'] = round(xg_total / matches_played, 2) if matches_played else 0.0
        doc['xg_against_per_match'] = round(xg_against / matches_played, 2) if matches_played else 0.0
        doc['shots_per_match'] = round(shots / matches_played, 2) if matches_played else 0.0
        doc['shots_on_target_per_match'] = round(shots_on_target / matches_played, 2) if matches_played else 0.0
        doc['key_passes_per_match'] = round(cls._stat_value(doc, 'key_passes') / matches_played, 2) if matches_played else 0.0
        doc['progressive_passes_per_match'] = round(progressive_passes / matches_played, 2) if matches_played else 0.0
        doc['high_regains_per_match'] = round(cls._stat_value(doc, 'high_regains') / matches_played, 2) if matches_played else 0.0
        return doc

    async def _get_team_season_aggregate(
        self,
        opta_team_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Aggregate all per-match team_statistics documents into season totals."""
        match_filter: Dict[str, Any] = {
            'team_id': {'$in': [opta_team_id, f't{opta_team_id}', int(opta_team_id)]}
        }
        if competition_id:
            match_filter['competition_id'] = {'$in': [str(competition_id), competition_id]}
        if season_id:
            match_filter['season_id'] = {'$in': [str(season_id), season_id]}

        group_stage: Dict[str, Any] = {
            '_id': '$team_id',
            'matches_played': {'$sum': 1},
            'scoutpro_team_id': {'$first': '$scoutpro_team_id'},
            'competition_id': {'$first': '$competition_id'},
            'season_id': {'$first': '$season_id'},
        }
        for field in self._TEAM_SUM_FIELDS:
            group_stage[field] = {'$sum': {'$ifNull': [f'${field}', 0]}}

        pipeline = [
            {'$match': match_filter},
            {'$group': group_stage},
        ]

        try:
            docs = await self.team_stats_collection.aggregate(pipeline).to_list(1)
        except Exception as exc:
            logger.error('_get_team_season_aggregate error: %s', exc)
            return None

        if not docs:
            return None

        doc = docs[0]
        doc.pop('_id', None)

        # Use ScoutPro ID as the canonical identifier; keep Opta ID for reference.
        sp_team_id = doc.get('scoutpro_team_id') or opta_team_id
        doc['id'] = sp_team_id
        doc['team_id'] = sp_team_id
        doc['opta_team_id'] = opta_team_id
        self.__class__._finalize_team_aggregate_doc(doc)
        doc['data_source'] = 'team_statistics_aggregate'
        return doc

    async def _build_player_statistics_from_events(self, player_id: str) -> Optional[PlayerStatistics]:
        from services.event_metric_utils import EventMetricAccumulator

        projection = {
            'player_name': 1,
            'playerName': 1,
            'type_name': 1,
            'type': 1,
            'is_goal': 1,
            'is_assist': 1,
            'is_successful': 1,
            'match_id': 1,
            'matchID': 1,
            'location': 1,
            'raw_event': 1,
            'xg_value': 1,
            'analytical_xg': 1,
            'xa_value': 1,
            'analytical_xa': 1,
            'progressive_pass': 1,
            'entered_final_third': 1,
            'entered_box': 1,
            'is_cross': 1,
            'pass_type': 1,
            'is_through_ball': 1,
            'is_long_ball': 1,
            'is_switch': 1,
            'is_key_pass': 1,
            'assist_potential': 1,
            'is_second_assist': 1,
            'is_set_piece': 1,
            'pass_length': 1,
            'is_on_target': 1,
            'is_big_chance': 1,
            'shot_distance': 1,
            'body_part': 1,
            'card_type': 1,
            'action_type': 1,
            'high_regain': 1,
        }
        docs = await self.match_events_collection.find(
            self._build_player_id_query(player_id),
            projection,
        ).to_list(length=None)

        if not docs:
            return None

        appearances = set()
        player_name = None
        event_totals: Dict[str, Any] = {}

        for doc in docs:
            if player_name is None:
                player_name = doc.get('player_name') or doc.get('playerName')

            match_id = doc.get('match_id') or doc.get('matchID')
            if match_id not in (None, ''):
                appearances.add(str(match_id))

            increments = EventMetricAccumulator.build_increments(doc)
            for key, value in increments.items():
                if not isinstance(value, (int, float)):
                    continue
                event_totals[key] = event_totals.get(key, 0) + value

        stats = {
            'player_name': player_name,
            'appearances': len(appearances),
            'matches': len(appearances),
            'games_played': len(appearances),
            **event_totals,
            'data_source': 'match_events_fallback',
        }

        stats.setdefault('goals', event_totals.get('goals', 0))
        stats.setdefault('assists', event_totals.get('assists', 0))
        stats.setdefault('goal_assist', stats.get('assists', 0))
        stats.setdefault('shots', event_totals.get('shots', 0))
        stats.setdefault('passes', event_totals.get('passes', 0))
        stats.setdefault('passes_completed', event_totals.get('passes_completed', 0))
        self.__class__._apply_player_derived_metrics(stats)

        return PlayerStatistics(
            player_id=str(player_id),
            player_name=player_name,
            stats=stats,
        )

    async def get_player_statistics(
        self,
        player_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
        per_90: bool = False
    ) -> Optional[PlayerStatistics]:
        """Get player statistics.

        Resolution order:
        1. Resolve incoming ID (ScoutPro long ID or Opta ID) → Opta numeric ID.
        2. Aggregate all per-match player_statistics docs for that Opta ID into
           season totals.
        3. If nothing found via player_statistics, fall back to a live scan of
           match_events.
        """
        try:
            opta_id = await self._resolve_opta_player_id(player_id)
            if not opta_id:
                # Already looks like an Opta ID or direct resolution failed; use as-is
                opta_id = str(player_id).lstrip('p')

            doc = await self._get_player_season_aggregate(
                opta_id, competition_id, season_id
            )

            if doc:
                # Try to enrich with player name from players collection
                if not doc.get('player_name'):
                    try:
                        p = await self.db['players'].find_one(
                            {'$or': [
                                {'provider_ids.opta': {'$in': [opta_id, f'p{opta_id}']}},
                                {'uID': {'$in': [opta_id, f'p{opta_id}']}},
                            ]},
                            {'name': 1}
                        )
                        if p:
                            doc['player_name'] = p.get('name')
                    except Exception:
                        pass

                return PlayerStatistics(
                    player_id=player_id,
                    player_name=doc.get('player_name'),
                    stats=doc
                )

            # Fallback: compute live from match_events
            if not per_90 and not competition_id and not season_id:
                fallback_stats = await self._build_player_statistics_from_events(opta_id)
                if fallback_stats:
                    return fallback_stats

            return None
        except Exception as e:
            logger.error(f"Error getting player statistics for {player_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def _build_team_id_query(team_id: str) -> Dict[str, Any]:
        raw_value = str(team_id).strip()
        numeric_values = []
        string_values = [raw_value]
        if raw_value.isdigit():
            numeric_values.append(int(raw_value))
        or_clauses = []
        for field in ('teamID', 'team_id'):
            if numeric_values:
                or_clauses.append({field: {'$in': numeric_values}})
            or_clauses.append({field: {'$in': string_values}})
        return {'$or': or_clauses}

    async def get_team_statistics(
        self,
        team_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get team statistics, aggregated across all matches into season totals."""
        try:
            opta_id = await self._resolve_opta_team_id(team_id)
            if not opta_id:
                opta_id = str(team_id).lstrip('t')

            doc = await self._get_team_season_aggregate(
                opta_id, competition_id, season_id
            )

            if doc:
                # Enrich with team name
                if not doc.get('team_name'):
                    try:
                        t = await self.db['teams'].find_one(
                            {'$or': [
                                {'provider_ids.opta': {'$in': [opta_id, f't{opta_id}']}},
                                {'uID': {'$in': [opta_id, f't{opta_id}']}},
                            ]},
                            {'name': 1}
                        )
                        if t:
                            doc['team_name'] = t.get('name')
                    except Exception:
                        pass
                return doc

            return None
        except Exception as e:
            logger.error(f"Error getting team statistics for {team_id}: {e}", exc_info=True)
            return None

    async def get_match_advanced_metrics(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            from services.match_projection_builder import MatchProjectionBuilder

            match_stats_doc = await self._find_match_projection_doc(self.match_statistics_collection, match_id)
            match_doc = await self.db['matches'].find_one(self._build_match_lookup_query(match_id), {'_id': 0}) or {}

            advanced_payload: Optional[Dict[str, Any]] = None
            if isinstance(match_stats_doc, dict) and (match_stats_doc.get('minuteTimeline') or match_stats_doc.get('metrics')):
                advanced_payload = dict(match_stats_doc)
            else:
                events = await self.match_events_collection.find(
                    self._build_match_event_lookup_query(match_id),
                    {'_id': 0},
                ).to_list(length=None)
                if events:
                    advanced_payload = MatchProjectionBuilder.build_advanced_metrics(
                        str((match_stats_doc or {}).get('match_id') or match_id),
                        match_doc,
                        events,
                        time_bucket='5m',
                    )
                elif match_stats_doc:
                    advanced_payload = {
                        'match_id': str(match_stats_doc.get('match_id') or match_id),
                        'match': match_doc,
                        'event_count': int(match_stats_doc.get('total_events') or 0),
                        'events_available': bool(match_stats_doc.get('total_events')),
                        'metrics': {},
                        'minuteTimeline': [],
                        'timeline': [],
                        'time_bucket': '5m',
                        'last_updated': match_stats_doc.get('updated_at'),
                    }

            if not advanced_payload:
                return None

            flat_source = match_stats_doc or {}
            flat_stats = self._extract_match_flat_metrics(flat_source)
            metrics = dict(advanced_payload.get('metrics') or {})
            metrics.update({key: value for key, value in flat_stats.items() if value is not None})

            return {
                'match_id': advanced_payload.get('match_id') or str(flat_source.get('match_id') or match_id),
                'match': advanced_payload.get('match') or match_doc,
                'competition_id': flat_source.get('competition_id') or advanced_payload.get('competition_id'),
                'season_id': flat_source.get('season_id') or advanced_payload.get('season_id'),
                'home_team_id': flat_source.get('home_team_id'),
                'away_team_id': flat_source.get('away_team_id'),
                'event_count': advanced_payload.get('event_count', int(flat_source.get('total_events') or 0)),
                'events_available': advanced_payload.get('events_available', bool(advanced_payload.get('event_count') or flat_source.get('total_events'))),
                'metrics': metrics,
                'flat_stats': flat_stats,
                'minuteTimeline': advanced_payload.get('minuteTimeline') or [],
                'timeline': advanced_payload.get('timeline') or [],
                'time_bucket': advanced_payload.get('time_bucket') or '5m',
                'last_updated': advanced_payload.get('last_updated') or flat_source.get('updated_at'),
            }
        except Exception as e:
            logger.error(f"Error getting match advanced metrics: {e}")
            return None

    async def get_match_tactical_snapshot(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            return await self._find_match_projection_doc(self.match_tactical_snapshot_collection, match_id)
        except Exception as e:
            logger.error(f"Error getting match tactical snapshot: {e}")
            return None

    async def get_match_pass_network(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            return await self._find_match_projection_doc(self.match_pass_network_collection, match_id)
        except Exception as e:
            logger.error(f"Error getting match pass network: {e}")
            return None

    async def get_match_sequence_summary(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            return await self._find_match_projection_doc(self.match_sequence_summary_collection, match_id)
        except Exception as e:
            logger.error(f"Error getting match sequence summary: {e}")
            return None

    async def get_match_statistics(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get the aggregated match-level statistics document written by EventStatsPipeline."""
        try:
            doc = await self._find_match_projection_doc(self.match_statistics_collection, match_id)
            if not doc:
                return None

            # Promote ScoutPro team IDs to primary; move Opta IDs under opta_* keys.
            for prefix in ('home', 'away'):
                opta_field = f'{prefix}_team_id'
                sp_field = f'scoutpro_{prefix}_team_id'
                if doc.get(sp_field):
                    doc[f'opta_{prefix}_team_id'] = doc.get(opta_field)
                    doc[opta_field] = doc[sp_field]

            # Enrich with team names – use the saved Opta ID for the MongoDB lookup
            # (home_team_id / away_team_id now hold ScoutPro IDs after the remap above)
            for prefix, name_field in (("home", "home_team_name"), ("away", "away_team_name")):
                opta_tid = doc.get(f'opta_{prefix}_team_id') or doc.get(f'{prefix}_team_id')
                if opta_tid:
                    try:
                        t = await self.db['teams'].find_one(
                            {"$or": [
                                {"provider_ids.opta": {"$in": [opta_tid, f"t{opta_tid}"]}},
                                {"uID": {"$in": [opta_tid, f"t{opta_tid}"]}},
                            ]},
                            {"name": 1}
                        )
                        if t:
                            doc[name_field] = t.get("name")
                    except Exception:
                        pass
            return doc
        except Exception as e:
            logger.error(f"Error getting match statistics for {match_id}: {e}")
            return None

    async def get_player_rankings(
        self,
        stat_name: str,
        position: Optional[str] = None,
        competition_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get season-level player rankings using rich event-derived aggregates."""
        try:
            aggregates = await self._aggregate_player_documents(competition_id)
            metadata_map = await self._fetch_player_metadata_map(
                list(aggregates.keys()) + [doc.get('scoutpro_player_id') for doc in aggregates.values()]
            )

            rankings: List[Dict[str, Any]] = []
            for opta_player_id, aggregate in aggregates.items():
                metadata = (
                    metadata_map.get(str(aggregate.get('scoutpro_player_id') or ''))
                    or metadata_map.get(opta_player_id)
                    or {}
                )
                if not self._position_matches(position, metadata, aggregate):
                    continue

                ranking_doc = dict(aggregate)
                ranking_doc['player_id'] = str(ranking_doc.get('scoutpro_player_id') or ranking_doc.get('player_id') or opta_player_id)
                ranking_doc['opta_player_id'] = opta_player_id
                ranking_doc['player_name'] = metadata.get('name') or ranking_doc.get('player_name')
                ranking_doc['name'] = ranking_doc.get('player_name')
                ranking_doc['player_position'] = metadata.get('position') or metadata.get('detailed_position')
                ranking_doc['position'] = ranking_doc.get('player_position')
                ranking_doc['player_team'] = metadata.get('club') or metadata.get('team_name')
                ranking_doc['club'] = ranking_doc.get('player_team')
                ranking_doc['nationality'] = metadata.get('nationality')
                ranking_doc['age'] = metadata.get('age')
                ranking_doc['_sort_value'] = self._metric_value(ranking_doc, stat_name, self._PLAYER_METRIC_ALIASES)
                ranking_doc['stat_name'] = stat_name
                ranking_doc['stat_value'] = ranking_doc['_sort_value']
                rankings.append(ranking_doc)

            rankings.sort(key=lambda doc: doc.get('_sort_value', 0.0), reverse=True)
            rankings = rankings[:limit]
            for idx, doc in enumerate(rankings, 1):
                doc.pop('_sort_value', None)
                doc['rank'] = idx

            return rankings
        except Exception as e:
            logger.error(f"Error getting player rankings: {e}")
            return []

    async def get_team_rankings(
        self,
        stat_name: str,
        competition_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get season-level team rankings using rich event-derived aggregates."""
        try:
            aggregates = await self._aggregate_team_documents(competition_id)
            metadata_map = await self._fetch_team_metadata_map(
                list(aggregates.keys()) + [doc.get('scoutpro_team_id') for doc in aggregates.values()]
            )

            rankings: List[Dict[str, Any]] = []
            for opta_team_id, aggregate in aggregates.items():
                metadata = (
                    metadata_map.get(str(aggregate.get('scoutpro_team_id') or ''))
                    or metadata_map.get(opta_team_id)
                    or {}
                )

                ranking_doc = dict(aggregate)
                ranking_doc['team_id'] = str(ranking_doc.get('scoutpro_team_id') or ranking_doc.get('team_id') or opta_team_id)
                ranking_doc['opta_team_id'] = opta_team_id
                ranking_doc['team_name'] = metadata.get('name') or ranking_doc.get('team_name')
                ranking_doc['name'] = ranking_doc.get('team_name')
                ranking_doc['team_country'] = metadata.get('country')
                ranking_doc['country'] = ranking_doc.get('team_country')
                ranking_doc['_sort_value'] = self._metric_value(ranking_doc, stat_name, self._TEAM_METRIC_ALIASES)
                ranking_doc['stat_name'] = stat_name
                ranking_doc['stat_value'] = ranking_doc['_sort_value']
                rankings.append(ranking_doc)

            rankings.sort(key=lambda doc: doc.get('_sort_value', 0.0), reverse=True)
            rankings = rankings[:limit]
            for idx, doc in enumerate(rankings, 1):
                doc.pop('_sort_value', None)
                doc['rank'] = idx

            return rankings
        except Exception as e:
            logger.error(f"Error getting team rankings: {e}")
            return []

    async def get_player_comparison(
        self,
        player_ids: List[str],
        stat_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple players using the same rich season aggregates as the ranking endpoints."""
        try:
            metadata_map = await self._fetch_player_metadata_map(player_ids)
            metric_names = stat_categories or list(self._DEFAULT_PLAYER_COMPARISON_METRICS)
            aggregates = await self._aggregate_player_documents()
            comparison: Dict[str, Any] = {'players': [], 'metrics': []}

            for requested_id in player_ids:
                resolved_player_id = await self._resolve_opta_player_id(str(requested_id))
                if not resolved_player_id:
                    resolved_player_id = str(requested_id).lstrip('p')

                stats_doc = dict(aggregates.get(str(resolved_player_id), {}))
                self.__class__._apply_player_output_aliases(stats_doc)

                metadata = (
                    metadata_map.get(str(requested_id))
                    or metadata_map.get(str(stats_doc.get('scoutpro_player_id') or ''))
                    or metadata_map.get(str(stats_doc.get('opta_player_id') or ''))
                    or {}
                )

                player_name = stats_doc.get('player_name') or metadata.get('name') or f'Player {requested_id}'
                club = metadata.get('club') or metadata.get('team_name')
                position = metadata.get('position') or metadata.get('detailed_position') or stats_doc.get('player_position')
                age = metadata.get('age')

                summary = {
                    'goals': self._metric_value(stats_doc, 'goals', self._PLAYER_METRIC_ALIASES),
                    'assists': self._metric_value(stats_doc, 'assists', self._PLAYER_METRIC_ALIASES),
                    'appearances': self._metric_value(stats_doc, 'matchesPlayed', self._PLAYER_METRIC_ALIASES),
                    'matches_played': self._metric_value(stats_doc, 'matchesPlayed', self._PLAYER_METRIC_ALIASES),
                    'passes': self._metric_value(stats_doc, 'passes', self._PLAYER_METRIC_ALIASES),
                    'successful_passes': self._metric_value(stats_doc, 'successfulPasses', self._PLAYER_METRIC_ALIASES),
                    'pass_accuracy': self._metric_value(stats_doc, 'passAccuracy', self._PLAYER_METRIC_ALIASES),
                    'passAccuracy': self._metric_value(stats_doc, 'passAccuracy', self._PLAYER_METRIC_ALIASES),
                    'shots': self._metric_value(stats_doc, 'shots', self._PLAYER_METRIC_ALIASES),
                    'shots_on_target': self._metric_value(stats_doc, 'shotsOnTarget', self._PLAYER_METRIC_ALIASES),
                    'xG': self._metric_value(stats_doc, 'xG', self._PLAYER_METRIC_ALIASES),
                    'xA': self._metric_value(stats_doc, 'xA', self._PLAYER_METRIC_ALIASES),
                    'keyPasses': self._metric_value(stats_doc, 'keyPasses', self._PLAYER_METRIC_ALIASES),
                    'progressivePasses': self._metric_value(stats_doc, 'progressivePasses', self._PLAYER_METRIC_ALIASES),
                    'minutes_played': self._stat_value(stats_doc, 'minutes_played'),
                    'club': club,
                    'position': position,
                    'age': age,
                    'nationality': metadata.get('nationality'),
                    'rating': self._stat_value(stats_doc, 'rating'),
                }

                comparison['players'].append(
                    {
                        'player_id': str(requested_id),
                        'player': {
                            'id': str(requested_id),
                            'name': player_name,
                            'club': club,
                            'position': position,
                            'age': age,
                            'nationality': metadata.get('nationality'),
                        },
                        'summary': summary,
                        'stats': stats_doc,
                    }
                )

            comparison['metrics'] = [
                {
                    'metric': metric_name,
                    'values': [
                        self._metric_value(player_entry.get('stats', {}), metric_name, self._PLAYER_METRIC_ALIASES)
                        for player_entry in comparison['players']
                    ],
                }
                for metric_name in metric_names
            ]

            return comparison
        except Exception as e:
            logger.error(f"Error comparing players: {e}")
            return {'players': [], 'metrics': []}

    async def aggregate_player_stats(
        self,
        player_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Aggregate player stats over time period"""
        try:
            id_query = self._build_player_id_query(player_id)
            query = {
                **id_query,
                'date': {'$gte': start_date, '$lte': end_date},
            }

            cursor = self.player_stats_collection.find(query)
            docs = await cursor.to_list(length=None)

            if not docs:
                return {}

            # Simple aggregation - sum numeric fields
            aggregated = {}
            for doc in docs:
                for key, value in doc.items():
                    if key in ['_id', 'playerID', 'date']:
                        continue
                    if isinstance(value, (int, float)):
                        aggregated[key] = aggregated.get(key, 0) + value

            return aggregated
        except Exception as e:
            logger.error(f"Error aggregating player stats: {e}")
            return {}
