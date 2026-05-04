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


class MongoStatisticsRepository(IStatisticsRepository):
    """MongoDB implementation of statistics repository"""

    SHOT_EVENT_TYPES = {'shot', 'goal', 'miss', 'attempt_saved', 'blocked_shot', 'chance_missed', 'post'}

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
        """Get player statistics"""
        try:
            query = self._build_player_id_query(player_id)

            if competition_id:
                query['competitionID'] = competition_id
            if season_id:
                query['seasonID'] = season_id

            collection = self.player_stats_per90_collection if per_90 else self.player_stats_collection
            doc = await collection.find_one(query)

            if doc:
                if '_id' in doc:
                    doc.pop('_id')
                return PlayerStatistics(
                    player_id=str(doc.get('player_id') or doc.get('playerID') or player_id),
                    player_name=doc.get('player_name'),
                    stats=doc
                )

            if not per_90 and not competition_id and not season_id:
                fallback_stats = await self._build_player_statistics_from_events(player_id)
                if fallback_stats:
                    return fallback_stats

            return None
        except Exception as e:
            logger.error(f"Error getting player statistics: {e}")
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
        """Get team statistics"""
        try:
            query = self._build_team_id_query(team_id)

            if competition_id:
                query['competitionID'] = competition_id
            if season_id:
                query['seasonID'] = season_id

            doc = await self.team_stats_collection.find_one(query)

            if doc:
                if '_id' in doc:
                    doc.pop('_id')
                return doc

            return None
        except Exception as e:
            logger.error(f"Error getting team statistics: {e}")
            return None

    async def get_match_advanced_metrics(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            doc = await self.match_statistics_collection.find_one({"match_id": str(match_id)})
            if doc:
                doc.pop('_id', None)
            return doc
        except Exception as e:
            logger.error(f"Error getting match advanced metrics: {e}")
            return None

    async def get_match_tactical_snapshot(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            doc = await self.match_tactical_snapshot_collection.find_one({"match_id": str(match_id)})
            if doc:
                doc.pop('_id', None)
            return doc
        except Exception as e:
            logger.error(f"Error getting match tactical snapshot: {e}")
            return None

    async def get_match_pass_network(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            doc = await self.match_pass_network_collection.find_one({"match_id": str(match_id)})
            if doc:
                doc.pop('_id', None)
            return doc
        except Exception as e:
            logger.error(f"Error getting match pass network: {e}")
            return None

    async def get_match_sequence_summary(
        self,
        match_id: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            doc = await self.match_sequence_summary_collection.find_one({"match_id": str(match_id)})
            if doc:
                doc.pop('_id', None)
            return doc
        except Exception as e:
            logger.error(f"Error getting match sequence summary: {e}")
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
