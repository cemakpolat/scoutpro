"""
Statistics Service - Business Logic Layer
"""
import asyncio
import math
from typing import Optional, List, Dict, Any
import json
import logging
from redis import Redis
from aiokafka import AIOKafkaProducer
import sys
sys.path.append('/app')
from shared.models.base import PlayerStatistics
from repository.interfaces import IStatisticsRepository
from services.batch_aggregator import BatchAggregator
from services.match_projection_builder import MatchProjectionBuilder

logger = logging.getLogger(__name__)


class StatisticsService:
    """Statistics service with caching and aggregation"""

    def __init__(
        self,
        repository: IStatisticsRepository,
        redis_client: Redis,
        kafka_producer: Optional[AIOKafkaProducer] = None,
        cache_ttl: int = 180
    ):
        self.repository = repository
        self.redis = redis_client
        self.kafka = kafka_producer
        self.cache_ttl = cache_ttl

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        if value in (None, '', 'None'):
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _safe_rate(cls, numerator: Any, denominator: Any) -> float:
        denominator_value = cls._to_float(denominator)
        if denominator_value <= 0:
            return 0.0
        return round(cls._to_float(numerator) / denominator_value * 100, 2)

    @classmethod
    def _per_90(cls, value: Any, minutes_played: Any) -> float:
        minute_total = cls._to_float(minutes_played)
        if minute_total <= 0:
            return 0.0
        return round(cls._to_float(value) * 90.0 / minute_total, 2)

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
        return max(minimum, min(maximum, value))

    @staticmethod
    def _poisson_probability(expected_goals: float, goals: int) -> float:
        if goals < 0:
            return 0.0
        return math.exp(-expected_goals) * (expected_goals ** goals) / math.factorial(goals)

    def _build_player_prediction_payload(
        self,
        player_id: str,
        player_name: Optional[str],
        stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        minutes_played = self._to_float(stats.get('minutes_played'))
        matches_played = self._to_float(stats.get('matches_played') or stats.get('games_played') or stats.get('appearances'))
        goals = self._to_float(stats.get('goals'))
        assists = self._to_float(stats.get('assists') or stats.get('total_assists') or stats.get('goal_assist'))
        total_xg = self._to_float(stats.get('total_xg') or stats.get('xg_total'))
        key_passes = self._to_float(stats.get('key_passes'))
        progressive_passes = self._to_float(stats.get('progressive_passes'))
        pass_accuracy = self._to_float(stats.get('pass_accuracy') or stats.get('pass_success_rate'))
        shot_accuracy = self._to_float(stats.get('shot_accuracy'))
        big_chance_conversion = self._to_float(stats.get('big_chance_conversion_rate'))
        take_on_success = self._to_float(stats.get('take_on_success_rate'))
        duel_success = self._to_float(stats.get('duel_success_rate'))
        aerial_success = self._to_float(stats.get('aerial_duel_success_rate'))
        recoveries = self._to_float(stats.get('ball_recoveries') or stats.get('recoveries') or stats.get('total_ball_recovery'))
        interceptions = self._to_float(stats.get('interceptions') or stats.get('total_interceptions'))
        tackles = self._to_float(stats.get('tackles') or stats.get('total_tackles'))

        goals_per_90 = self._per_90(goals, minutes_played)
        assists_per_90 = self._per_90(assists, minutes_played)
        xg_per_90 = self._per_90(total_xg, minutes_played)
        key_passes_per_90 = self._per_90(key_passes, minutes_played)
        progressive_passes_per_90 = self._per_90(progressive_passes, minutes_played)
        defensive_actions_per_90 = self._per_90(recoveries + interceptions + tackles, minutes_played)

        attacking_score = self._clamp(
            xg_per_90 * 28
            + goals_per_90 * 18
            + shot_accuracy * 0.22
            + big_chance_conversion * 0.12,
        )
        creative_score = self._clamp(
            key_passes_per_90 * 8.5
            + assists_per_90 * 18
            + progressive_passes_per_90 * 2.5
            + pass_accuracy * 0.35,
        )
        defensive_score = self._clamp(
            defensive_actions_per_90 * 6.0
            + take_on_success * 0.12
            + duel_success * 0.18
            + aerial_success * 0.12,
        )
        form_index = round(attacking_score * 0.45 + creative_score * 0.30 + defensive_score * 0.25, 2)
        projected_goal_involvements_next90 = round(
            max(0.05, xg_per_90 * 0.85 + assists_per_90 * 0.9 + key_passes_per_90 * 0.06),
            2,
        )
        sample_confidence = round(min(100.0, matches_played * 12.5), 1)

        return {
            'player_id': player_id,
            'player_name': player_name,
            'sample': {
                'matches_played': int(matches_played),
                'minutes_played': round(minutes_played, 1),
                'confidence': sample_confidence,
            },
            'components': {
                'attacking_score': round(attacking_score, 2),
                'creative_score': round(creative_score, 2),
                'defensive_score': round(defensive_score, 2),
                'form_index': form_index,
            },
            'projection': {
                'projected_goal_involvements_next90': projected_goal_involvements_next90,
                'goals_per_90': goals_per_90,
                'assists_per_90': assists_per_90,
                'xg_per_90': xg_per_90,
                'key_passes_per_90': key_passes_per_90,
                'progressive_passes_per_90': progressive_passes_per_90,
                'finishing_delta_vs_xg': round(goals - total_xg, 2),
            },
        }

    def _build_team_prediction_payload(
        self,
        team_id: str,
        stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        matches_played = self._to_float(stats.get('matches_played'))
        goals = self._to_float(stats.get('goals'))
        goals_against = self._to_float(stats.get('goals_against'))
        total_xg = self._to_float(stats.get('total_xg') or stats.get('xg_total'))
        total_xg_against = self._to_float(stats.get('total_xg_against'))
        shots = self._to_float(stats.get('shots'))
        shots_on_target = self._to_float(stats.get('shots_on_target'))
        pass_accuracy = self._to_float(stats.get('pass_accuracy'))
        possession = self._to_float(stats.get('possession_percentage'))
        progressive_passes = self._to_float(stats.get('progressive_passes'))
        key_passes = self._to_float(stats.get('key_passes'))
        high_regains = self._to_float(stats.get('high_regains'))
        recoveries = self._to_float(stats.get('recoveries') or stats.get('ball_recoveries'))
        duels_won = self._to_float(stats.get('duels_won'))
        duels = self._to_float(stats.get('duels'))

        goals_per_match = round(goals / matches_played, 2) if matches_played else 0.0
        goals_against_per_match = round(goals_against / matches_played, 2) if matches_played else 0.0
        xg_per_match = round(total_xg / matches_played, 2) if matches_played else 0.0
        xg_against_per_match = round(total_xg_against / matches_played, 2) if matches_played else 0.0
        shots_per_match = round(shots / matches_played, 2) if matches_played else 0.0
        key_passes_per_match = round(key_passes / matches_played, 2) if matches_played else 0.0
        progressive_passes_per_match = round(progressive_passes / matches_played, 2) if matches_played else 0.0
        shot_accuracy = self._safe_rate(shots_on_target, shots)
        duel_success = self._safe_rate(duels_won, duels)

        attack_rating = self._clamp(
            goals_per_match * 18
            + xg_per_match * 20
            + shot_accuracy * 0.25
            + key_passes_per_match * 4.5,
        )
        control_rating = self._clamp(
            pass_accuracy * 0.45
            + possession * 0.30
            + progressive_passes_per_match * 4.5
            + key_passes_per_match * 3.5,
        )
        defensive_rating = self._clamp(
            100.0
            - goals_against_per_match * 22
            - xg_against_per_match * 12
            + round((recoveries / matches_played), 2) * 2.5 if matches_played else 55.0,
        )
        defensive_rating = self._clamp(defensive_rating + high_regains * (1.0 / max(matches_played, 1.0)) * 4 + duel_success * 0.15)

        return {
            'team_id': team_id,
            'team_name': stats.get('team_name'),
            'sample': {
                'matches_played': int(matches_played),
                'confidence': round(min(100.0, matches_played * 10.0), 1),
            },
            'components': {
                'attack_rating': round(attack_rating, 2),
                'control_rating': round(control_rating, 2),
                'defensive_rating': round(defensive_rating, 2),
            },
            'projection': {
                'goals_per_match': goals_per_match,
                'goals_against_per_match': goals_against_per_match,
                'xg_per_match': xg_per_match,
                'xg_against_per_match': xg_against_per_match,
                'projected_goals_next_match': round(max(0.2, xg_per_match * 0.65 + goals_per_match * 0.35), 2),
                'projected_goals_conceded_next_match': round(max(0.15, xg_against_per_match * 0.65 + goals_against_per_match * 0.35), 2),
                'shots_per_match': shots_per_match,
                'key_passes_per_match': key_passes_per_match,
                'progressive_passes_per_match': progressive_passes_per_match,
            },
        }

    async def get_player_statistics(
        self,
        player_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
        per_90: bool = False
    ) -> Optional[PlayerStatistics]:
        """Get player statistics with caching"""
        try:
            cache_key = f"stats:player:{player_id}:{competition_id}:{season_id}:{per_90}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for player {player_id} statistics")
                return PlayerStatistics(**json.loads(cached))

            stats = await self.repository.get_player_statistics(
                player_id,
                competition_id,
                season_id,
                per_90
            )

            if stats:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    stats.json()
                )

            return stats
        except Exception as e:
            logger.error(f"Error in get_player_statistics: {e}")
            raise

    async def get_team_statistics(
        self,
        team_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get team statistics with caching"""
        try:
            cache_key = f"stats:team:{team_id}:{competition_id}:{season_id}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for team {team_id} statistics")
                return json.loads(cached)

            stats = await self.repository.get_team_statistics(
                team_id,
                competition_id,
                season_id
            )

            if stats:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(stats)
                )

            return stats
        except Exception as e:
            logger.error(f"Error in get_team_statistics: {e}")
            raise

    async def get_player_rankings(
        self,
        stat_name: str,
        position: Optional[str] = None,
        competition_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get player rankings with caching"""
        try:
            cache_key = f"stats:rankings:player:{stat_name}:{position}:{competition_id}:{limit}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for player rankings ({stat_name})")
                return json.loads(cached)

            rankings = await self.repository.get_player_rankings(
                stat_name,
                position,
                competition_id,
                limit
            )

            if rankings:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl * 2,  # Rankings change less frequently
                    json.dumps(rankings)
                )

            return rankings
        except Exception as e:
            logger.error(f"Error in get_player_rankings: {e}")
            raise

    async def get_team_rankings(
        self,
        stat_name: str,
        competition_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get team rankings with caching"""
        try:
            cache_key = f"stats:rankings:team:{stat_name}:{competition_id}:{limit}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for team rankings ({stat_name})")
                return json.loads(cached)

            rankings = await self.repository.get_team_rankings(
                stat_name,
                competition_id,
                limit
            )

            if rankings:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl * 2,
                    json.dumps(rankings)
                )

            return rankings
        except Exception as e:
            logger.error(f"Error in get_team_rankings: {e}")
            raise

    async def compare_players(
        self,
        player_ids: List[str],
        stat_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple players"""
        try:
            cache_key = f"stats:compare:{':'.join(sorted(player_ids))}:{stat_categories}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug("Cache hit for player comparison")
                return json.loads(cached)

            comparison = await self.repository.get_player_comparison(
                player_ids,
                stat_categories
            )

            if comparison:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(comparison)
                )

            return comparison
        except Exception as e:
            logger.error(f"Error in compare_players: {e}")
            raise

    async def aggregate_player_stats(
        self,
        player_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Aggregate player stats over time period"""
        try:
            aggregated = await self.repository.aggregate_player_stats(
                player_id,
                start_date,
                end_date
            )

            return aggregated
        except Exception as e:
            logger.error(f"Error in aggregate_player_stats: {e}")
            raise

    async def get_match_advanced_metrics(
        self,
        match_id: str,
        time_bucket: str = "5m",
    ) -> Optional[Dict[str, Any]]:
        try:
            cache_key = f"stats:match:advanced:{match_id}:{time_bucket}"
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

            payload = await self.repository.get_match_advanced_metrics(match_id)
            if not payload:
                return None

            minute_timeline = payload.get('minuteTimeline') or []
            bucket_digits = ''.join(ch for ch in str(time_bucket) if ch.isdigit())
            bucket_minutes = max(1, int(bucket_digits)) if bucket_digits else 5
            payload['time_bucket'] = time_bucket
            payload['timeline'] = MatchProjectionBuilder.rebucket_timeline(minute_timeline, bucket_minutes)

            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(payload))
            return payload
        except Exception as e:
            logger.error(f"Error in get_match_advanced_metrics: {e}")
            raise

    async def get_match_tactical_snapshot(self, match_id: str) -> Optional[Dict[str, Any]]:
        try:
            cache_key = f"stats:match:tactical:{match_id}"
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

            payload = await self.repository.get_match_tactical_snapshot(match_id)
            if payload:
                await self.redis.setex(cache_key, self.cache_ttl, json.dumps(payload))
            return payload
        except Exception as e:
            logger.error(f"Error in get_match_tactical_snapshot: {e}")
            raise

    async def get_match_pass_network(self, match_id: str) -> Optional[Dict[str, Any]]:
        try:
            cache_key = f"stats:match:pass-network:{match_id}"
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

            payload = await self.repository.get_match_pass_network(match_id)
            if payload:
                await self.redis.setex(cache_key, self.cache_ttl, json.dumps(payload))
            return payload
        except Exception as e:
            logger.error(f"Error in get_match_pass_network: {e}")
            raise

    async def get_match_sequence_summary(self, match_id: str) -> Optional[Dict[str, Any]]:
        try:
            cache_key = f"stats:match:sequences:{match_id}"
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

            payload = await self.repository.get_match_sequence_summary(match_id)
            if payload:
                await self.redis.setex(cache_key, self.cache_ttl, json.dumps(payload))
            return payload
        except Exception as e:
            logger.error(f"Error in get_match_sequence_summary: {e}")
            raise

    async def get_match_statistics(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get aggregated match-level statistics (box score + EventMinutes timeline)."""
        try:
            cache_key = f"stats:match:summary:{match_id}"
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

            payload = await self.repository.get_match_statistics(match_id)
            if payload:
                await self.redis.setex(cache_key, self.cache_ttl, json.dumps(payload))
            return payload
        except Exception as e:
            logger.error(f"Error in get_match_statistics: {e}")
            raise

    async def get_player_prediction(
        self,
        player_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            cache_key = f"stats:prediction:player:{player_id}:{competition_id}:{season_id}"
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

            payload = await self.get_player_statistics(player_id, competition_id, season_id, per_90=False)
            if not payload:
                return None

            stats = payload.stats if isinstance(payload, PlayerStatistics) else payload.get('stats', {})
            prediction = self._build_player_prediction_payload(player_id, payload.player_name if isinstance(payload, PlayerStatistics) else None, stats)
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(prediction))
            return prediction
        except Exception as e:
            logger.error(f"Error in get_player_prediction: {e}")
            raise

    async def get_team_prediction(
        self,
        team_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            cache_key = f"stats:prediction:team:{team_id}:{competition_id}:{season_id}"
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

            stats = await self.get_team_statistics(team_id, competition_id, season_id)
            if not stats:
                return None

            prediction = self._build_team_prediction_payload(team_id, stats)
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(prediction))
            return prediction
        except Exception as e:
            logger.error(f"Error in get_team_prediction: {e}")
            raise

    async def get_match_prediction(self, match_id: str) -> Optional[Dict[str, Any]]:
        try:
            cache_key = f"stats:prediction:match:{match_id}"
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

            match_stats = await self.get_match_statistics(match_id)
            if not match_stats:
                return None

            competition_id = match_stats.get('competition_id')
            season_id = match_stats.get('season_id')
            home_team_id = match_stats.get('home_team_id')
            away_team_id = match_stats.get('away_team_id')
            if not home_team_id or not away_team_id:
                return None

            home_team_prediction, away_team_prediction = await asyncio.gather(
                self.get_team_prediction(str(home_team_id), competition_id, season_id),
                self.get_team_prediction(str(away_team_id), competition_id, season_id),
            )
            if not home_team_prediction or not away_team_prediction:
                return None

            home_for = self._to_float(home_team_prediction['projection'].get('projected_goals_next_match'))
            home_against = self._to_float(home_team_prediction['projection'].get('projected_goals_conceded_next_match'))
            away_for = self._to_float(away_team_prediction['projection'].get('projected_goals_next_match'))
            away_against = self._to_float(away_team_prediction['projection'].get('projected_goals_conceded_next_match'))

            home_expected_goals = round(max(0.2, (home_for + away_against) / 2.0 + 0.15), 2)
            away_expected_goals = round(max(0.15, (away_for + home_against) / 2.0), 2)

            max_goals = 6
            home_win_probability = 0.0
            draw_probability = 0.0
            away_win_probability = 0.0
            scorelines = []

            for home_goals in range(max_goals + 1):
                home_prob = self._poisson_probability(home_expected_goals, home_goals)
                for away_goals in range(max_goals + 1):
                    away_prob = self._poisson_probability(away_expected_goals, away_goals)
                    score_probability = home_prob * away_prob
                    scorelines.append({
                        'home_goals': home_goals,
                        'away_goals': away_goals,
                        'probability': round(score_probability * 100, 2),
                    })
                    if home_goals > away_goals:
                        home_win_probability += score_probability
                    elif home_goals == away_goals:
                        draw_probability += score_probability
                    else:
                        away_win_probability += score_probability

            scorelines.sort(key=lambda item: item['probability'], reverse=True)
            payload = {
                'match_id': match_id,
                'home_team': home_team_prediction,
                'away_team': away_team_prediction,
                'expected_goals': {
                    'home': home_expected_goals,
                    'away': away_expected_goals,
                },
                'probabilities': {
                    'home_win': round(home_win_probability * 100, 2),
                    'draw': round(draw_probability * 100, 2),
                    'away_win': round(away_win_probability * 100, 2),
                    'both_teams_to_score': round(sum(
                        item['probability'] for item in scorelines if item['home_goals'] > 0 and item['away_goals'] > 0
                    ), 2),
                    'over_2_5_goals': round(sum(
                        item['probability'] for item in scorelines if item['home_goals'] + item['away_goals'] >= 3
                    ), 2),
                },
                'most_likely_scorelines': scorelines[:5],
            }
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(payload))
            return payload
        except Exception as e:
            logger.error(f"Error in get_match_prediction: {e}")
            raise

    async def rebuild_match_projections(
        self,
        match_id: Optional[str] = None,
        competition_id: Optional[str] = None,
        season_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            return await asyncio.to_thread(
                self._run_projection_rebuild_sync,
                match_id,
                competition_id,
                season_id,
            )
        except Exception as e:
            logger.error(f"Error in rebuild_match_projections: {e}")
            raise

    @staticmethod
    def _run_projection_rebuild_sync(
        match_id: Optional[str] = None,
        competition_id: Optional[str] = None,
        season_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        from services.event_stats_pipeline import EventStatsPipeline

        aggregator = BatchAggregator()
        pipeline = None
        try:
            projection_result = aggregator.run(
                match_id=match_id,
                competition_id=competition_id,
                season_id=season_id,
            )

            # Refresh the canonical match/player/team statistics after rebuilding
            # the tactical/pass-network projections so match_statistics keeps the
            # richer event-pipeline shape expected by the API.
            pipeline = EventStatsPipeline()
            stats_result = pipeline.run(
                match_id=match_id,
                competition_id=competition_id,
                season_id=season_id,
            )

            return {
                'player_docs': stats_result.get('player_docs', 0),
                'team_docs': stats_result.get('team_docs', 0),
                'match_docs': projection_result.get('match_docs', 0),
                'projection_rebuild': projection_result,
                'event_stats_refresh': stats_result,
            }
        finally:
            aggregator.close()
            if pipeline is not None:
                pipeline.close()
