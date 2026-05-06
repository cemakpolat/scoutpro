from pathlib import Path
import json
import sys
import types
import unittest
from unittest import mock


STATS_SERVICE_ROOT = Path(__file__).resolve().parents[1]
SERVICES_ROOT = Path(__file__).resolve().parents[2]

for path in (STATS_SERVICE_ROOT, SERVICES_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)


services_package = types.ModuleType('services')
services_package.__path__ = [str(STATS_SERVICE_ROOT / 'services')]
sys.modules['services'] = services_package

repository_module = types.ModuleType('repository')
repository_module.__path__ = []
repository_interfaces_module = types.ModuleType('repository.interfaces')


class IStatisticsRepository:
    pass


repository_interfaces_module.IStatisticsRepository = IStatisticsRepository
repository_module.interfaces = repository_interfaces_module
sys.modules['repository'] = repository_module
sys.modules['repository.interfaces'] = repository_interfaces_module


redis_module = types.ModuleType('redis')
redis_module.Redis = object
sys.modules.setdefault('redis', redis_module)

aiokafka_module = types.ModuleType('aiokafka')
aiokafka_module.AIOKafkaProducer = object
sys.modules.setdefault('aiokafka', aiokafka_module)

batch_aggregator_module = types.ModuleType('services.batch_aggregator')


class BatchAggregator:
    def run(self, match_id=None, competition_id=None, season_id=None):
        return {'player_docs': 0, 'team_docs': 0, 'match_docs': 0}

    def close(self):
        return None


batch_aggregator_module.BatchAggregator = BatchAggregator
sys.modules.setdefault('services.batch_aggregator', batch_aggregator_module)

match_projection_builder_module = types.ModuleType('services.match_projection_builder')


class MatchProjectionBuilder:
    @staticmethod
    def rebucket_timeline(minute_timeline, bucket_minutes):
        return minute_timeline


match_projection_builder_module.MatchProjectionBuilder = MatchProjectionBuilder
sys.modules.setdefault('services.match_projection_builder', match_projection_builder_module)

shared_module = types.ModuleType('shared')
shared_module.__path__ = []
shared_models_module = types.ModuleType('shared.models')
shared_models_module.__path__ = []
shared_models_base_module = types.ModuleType('shared.models.base')


class PlayerStatistics:
    def __init__(self, player_id, player_name=None, competition_id=None, season_id=None, stats=None):
        self.player_id = player_id
        self.player_name = player_name
        self.competition_id = competition_id
        self.season_id = season_id
        self.stats = stats or {}

    def json(self):
        return json.dumps(
            {
                'player_id': self.player_id,
                'player_name': self.player_name,
                'competition_id': self.competition_id,
                'season_id': self.season_id,
                'stats': self.stats,
            }
        )


shared_models_base_module.PlayerStatistics = PlayerStatistics
shared_models_module.base = shared_models_base_module
shared_module.models = shared_models_module
sys.modules.setdefault('shared', shared_module)
sys.modules.setdefault('shared.models', shared_models_module)
sys.modules.setdefault('shared.models.base', shared_models_base_module)


from shared.models.base import PlayerStatistics
from services.statistics_service import StatisticsService


class FakeRedis:
    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)

    async def setex(self, key, ttl, value):
        self.data[key] = value


class FakeRepository:
    async def get_player_statistics(self, player_id, competition_id=None, season_id=None, per_90=False):
        return PlayerStatistics(
            player_id=player_id,
            player_name='Test Player',
            stats={
                'matches_played': 8,
                'minutes_played': 720,
                'goals': 5,
                'assists': 2,
                'total_xg': 4.2,
                'key_passes': 18,
                'progressive_passes': 40,
                'pass_accuracy': 84.0,
                'shot_accuracy': 50.0,
                'big_chance_conversion_rate': 60.0,
                'take_on_success_rate': 58.0,
                'duel_success_rate': 56.0,
                'aerial_duel_success_rate': 48.0,
                'ball_recoveries': 28,
                'interceptions': 10,
                'tackles': 12,
            },
        )

    async def get_team_statistics(self, team_id, competition_id=None, season_id=None):
        base = {
            'matches_played': 10,
            'team_name': 'Test Team',
            'goals': 18,
            'goals_against': 10,
            'total_xg': 15.6,
            'total_xg_against': 11.8,
            'shots': 120,
            'shots_on_target': 46,
            'pass_accuracy': 83.0,
            'possession_percentage': 55.0,
            'progressive_passes': 88,
            'key_passes': 72,
            'high_regains': 24,
            'recoveries': 130,
            'duels': 180,
            'duels_won': 96,
        }
        if str(team_id) == 'away':
            base.update({
                'team_name': 'Away Team',
                'goals': 14,
                'goals_against': 12,
                'total_xg': 13.1,
                'total_xg_against': 13.6,
                'shots': 105,
                'shots_on_target': 39,
                'pass_accuracy': 79.0,
                'possession_percentage': 49.0,
                'progressive_passes': 71,
                'key_passes': 58,
                'high_regains': 18,
                'recoveries': 119,
                'duels': 170,
                'duels_won': 84,
            })
        return base

    async def get_player_rankings(self, stat_name, position=None, competition_id=None, limit=50):
        return []

    async def get_team_rankings(self, stat_name, competition_id=None, limit=50):
        return []

    async def get_player_comparison(self, player_ids, stat_categories=None):
        return {'players': []}

    async def aggregate_player_stats(self, player_id, start_date, end_date):
        return {}

    async def get_match_advanced_metrics(self, match_id):
        return None

    async def get_match_tactical_snapshot(self, match_id):
        return None

    async def get_match_pass_network(self, match_id):
        return None

    async def get_match_sequence_summary(self, match_id):
        return None

    async def get_match_statistics(self, match_id):
        return {
            'match_id': match_id,
            'home_team_id': 'home',
            'away_team_id': 'away',
            'competition_id': 1,
            'season_id': 2025,
        }


class StatisticsPredictionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.service = StatisticsService(repository=FakeRepository(), redis_client=FakeRedis())

    async def test_player_prediction_builds_expected_projection(self):
        payload = await self.service.get_player_prediction('player-1')

        self.assertIsNotNone(payload)
        self.assertGreater(payload['components']['form_index'], 0)
        self.assertGreater(payload['projection']['projected_goal_involvements_next90'], 0)
        self.assertGreater(payload['projection']['xg_per_90'], 0)

    async def test_match_prediction_returns_probability_distribution(self):
        payload = await self.service.get_match_prediction('match-1')

        self.assertIsNotNone(payload)
        total_probability = (
            payload['probabilities']['home_win']
            + payload['probabilities']['draw']
            + payload['probabilities']['away_win']
        )
        self.assertGreaterEqual(total_probability, 99.0)
        self.assertLessEqual(total_probability, 101.0)
        self.assertGreater(payload['expected_goals']['home'], 0)
        self.assertGreater(payload['expected_goals']['away'], 0)
        self.assertTrue(payload['most_likely_scorelines'])

    async def test_rebuild_match_projections_refreshes_canonical_event_stats_after_batch(self):
        call_order = []

        class FakeBatchAggregator:
            def run(self, match_id=None, competition_id=None, season_id=None):
                call_order.append(('batch', match_id, competition_id, season_id))
                return {'player_docs': 1, 'team_docs': 1, 'match_docs': 4}

            def close(self):
                call_order.append('batch_close')

        class FakeEventStatsPipeline:
            def run(self, match_id=None, competition_id=None, season_id=None):
                call_order.append(('pipeline', match_id, competition_id, season_id))
                return {'player_docs': 7, 'team_docs': 3}

            def close(self):
                call_order.append('pipeline_close')

        fake_pipeline_module = types.ModuleType('services.event_stats_pipeline')
        fake_pipeline_module.EventStatsPipeline = FakeEventStatsPipeline

        with mock.patch('services.statistics_service.BatchAggregator', FakeBatchAggregator):
            with mock.patch.dict(sys.modules, {'services.event_stats_pipeline': fake_pipeline_module}):
                payload = await self.service.rebuild_match_projections(
                    match_id='match-1',
                    competition_id='10',
                    season_id='2025',
                )

        self.assertEqual(payload['player_docs'], 7)
        self.assertEqual(payload['team_docs'], 3)
        self.assertEqual(payload['match_docs'], 4)
        self.assertEqual(payload['projection_rebuild']['match_docs'], 4)
        self.assertEqual(payload['event_stats_refresh']['player_docs'], 7)
        self.assertEqual(call_order[0], ('batch', 'match-1', '10', '2025'))
        self.assertEqual(call_order[1], ('pipeline', 'match-1', '10', '2025'))
        self.assertIn('batch_close', call_order)
        self.assertIn('pipeline_close', call_order)


if __name__ == '__main__':
    unittest.main()