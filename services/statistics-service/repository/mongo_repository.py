"""
MongoDB implementation of Statistics Repository
"""
import re
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
    ]

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

        # Normalise field aliases so downstream consumers get consistent keys
        doc.setdefault('appearances', doc.get('matches_played', 0))
        doc.setdefault('goals', doc.get('goals', 0))
        doc.setdefault('assists', doc.get('goal_assist') or doc.get('assists') or 0)
        doc.setdefault('total_shots', doc.get('total_shots') or doc.get('shots') or 0)
        doc.setdefault('total_tackles', doc.get('total_tackles') or doc.get('tackles') or 0)
        doc.setdefault('total_interceptions',
                       doc.get('total_interceptions') or doc.get('interceptions') or 0)
        doc.setdefault('total_clearances',
                       doc.get('total_clearances') or doc.get('clearances') or 0)
        doc.setdefault('total_passes', doc.get('total_passes') or doc.get('passes') or 0)

        # Pass accuracy
        total_p = doc.get('passes') or doc.get('total_passes') or 0
        succ_p = doc.get('passes_successful') or 0
        if total_p > 0:
            doc['pass_accuracy'] = round(succ_p / total_p * 100, 2)
            doc['pass_success_rate'] = doc['pass_accuracy']
        else:
            doc['pass_accuracy'] = 0.0
            doc['pass_success_rate'] = 0.0

        doc['data_source'] = 'player_statistics_aggregate'
        return doc

    _TEAM_SUM_FIELDS = [
        'passes', 'passes_successful', 'shots', 'goals', 'tackles',
        'interceptions', 'clearances', 'fouls', 'yellow_cards', 'red_cards',
        'total_events', 'total_xg',
    ]

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

        total_p = doc.get('passes', 0)
        succ_p = doc.get('passes_successful', 0)
        doc['pass_accuracy'] = round(succ_p / total_p * 100, 2) if total_p else 0.0
        doc['matches_played'] = doc.get('matches_played', 0)
        doc['data_source'] = 'team_statistics_aggregate'
        return doc

    async def _build_player_statistics_from_events(self, player_id: str) -> Optional[PlayerStatistics]:
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
        }
        docs = await self.match_events_collection.find(
            self._build_player_id_query(player_id),
            projection,
        ).to_list(length=None)

        if not docs:
            return None

        appearances = set()
        goals = 0
        assists = 0
        shots = 0
        passes = 0
        completed_passes = 0
        player_name = None

        for doc in docs:
            if player_name is None:
                player_name = doc.get('player_name') or doc.get('playerName')

            match_id = doc.get('match_id') or doc.get('matchID')
            if match_id not in (None, ''):
                appearances.add(str(match_id))

            event_type = str(doc.get('type_name') or doc.get('type') or '').lower()
            if event_type == 'pass':
                passes += 1
                if doc.get('is_successful') is not False:
                    completed_passes += 1

            if doc.get('is_assist'):
                assists += 1

            if doc.get('is_goal') or event_type == 'goal':
                goals += 1

            if event_type in self.SHOT_EVENT_TYPES or doc.get('is_goal'):
                shots += 1

        stats = {
            'player_name': player_name,
            'appearances': len(appearances),
            'matches': len(appearances),
            'games_played': len(appearances),
            'goals': goals,
            'assists': assists,
            'goal_assist': assists,
            'shots': shots,
            'passes': passes,
            'completed_passes': completed_passes,
            'pass_accuracy': round((completed_passes / passes) * 100, 2) if passes else 0.0,
            'data_source': 'match_events_fallback',
        }

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
            return await self._find_match_projection_doc(self.match_statistics_collection, match_id)
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
        """Get player rankings by statistic, enriched with player names via $lookup."""
        try:
            query = {}
            if competition_id:
                query['competitionID'] = competition_id

            cursor = self.player_stats_collection.find(query).sort(stat_name, -1).limit(limit)
            docs = await cursor.to_list(length=limit)

            # Batch-resolve player names from the players collection.
            # player_stats.playerID is from the F24 event namespace;
            # but some stats may share IDs with F9/F40 players.uID (both numeric).
            player_ids = [str(doc.get('playerID', '')) for doc in docs if doc.get('playerID')]
            player_map = {}
            if player_ids:
                try:
                    players_cursor = self.db['players'].find(
                        {'uID': {'$in': player_ids}},
                        {'uID': 1, 'name': 1, 'position': 1, 'club': 1, 'nationality': 1}
                    )
                    async for p in players_cursor:
                        player_map[str(p.get('uID', ''))] = p
                except Exception as e:
                    logger.warning(f"Player name lookup failed: {e}")

            rankings = []
            for idx, doc in enumerate(docs, 1):
                if '_id' in doc:
                    doc.pop('_id')
                doc['rank'] = idx
                pid = str(doc.get('playerID', ''))
                player_info = player_map.get(pid, {})
                doc['player_name'] = player_info.get('name') or None
                doc['player_position'] = player_info.get('position') or None
                doc['player_team'] = player_info.get('club') or None
                rankings.append(doc)

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
        """Get team rankings by statistic, enriched with team names via $lookup."""
        try:
            query = {}
            if competition_id:
                query['competitionID'] = competition_id

            cursor = self.team_stats_collection.find(query).sort(stat_name, -1).limit(limit)
            docs = await cursor.to_list(length=limit)

            # Batch-resolve team names from teams collection
            team_ids = [str(doc.get('teamID', '')) for doc in docs if doc.get('teamID')]
            team_map = {}
            if team_ids:
                try:
                    teams_cursor = self.db['teams'].find(
                        {'uID': {'$in': team_ids}},
                        {'uID': 1, 'name': 1, 'country': 1}
                    )
                    async for t in teams_cursor:
                        team_map[str(t.get('uID', ''))] = t
                except Exception as e:
                    logger.warning(f"Team name lookup failed: {e}")

            rankings = []
            for idx, doc in enumerate(docs, 1):
                if '_id' in doc:
                    doc.pop('_id')
                doc['rank'] = idx
                tid = str(doc.get('teamID', ''))
                team_info = team_map.get(tid, {})
                doc['team_name'] = team_info.get('name') or None
                doc['team_country'] = team_info.get('country') or None
                rankings.append(doc)

            return rankings
        except Exception as e:
            logger.error(f"Error getting team rankings: {e}")
            return []

    async def get_player_comparison(
        self,
        player_ids: List[str],
        stat_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple players"""
        try:
            all_values: List[Any] = []
            for pid in player_ids:
                raw = str(pid).strip()
                all_values.append(raw)
                if raw.isdigit():
                    all_values.append(int(raw))
                elif raw.lower().startswith('p') and raw[1:].isdigit():
                    all_values.append(int(raw[1:]))
            query = {'$or': [
                {'playerID': {'$in': all_values}},
                {'player_id': {'$in': all_values}},
            ]}

            cursor = self.player_stats_collection.find(query)
            docs = await cursor.to_list(length=len(player_ids))

            comparison = {
                'players': []
            }

            for doc in docs:
                if '_id' in doc:
                    doc.pop('_id')

                # Filter to specific categories if requested
                if stat_categories:
                    filtered_doc = {k: v for k, v in doc.items() if k in stat_categories or k == 'playerID'}
                    comparison['players'].append(filtered_doc)
                else:
                    comparison['players'].append(doc)

            return comparison
        except Exception as e:
            logger.error(f"Error comparing players: {e}")
            return {'players': []}

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
