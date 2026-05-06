from pathlib import Path
import copy
import sys
import types
import unittest


STATS_SERVICE_ROOT = Path(__file__).resolve().parents[1]
SERVICES_ROOT = Path(__file__).resolve().parents[2]

for path in (STATS_SERVICE_ROOT, SERVICES_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)


services_package = types.ModuleType('services')
services_package.__path__ = [str(STATS_SERVICE_ROOT / 'services')]
sys.modules['services'] = services_package

motor_module = types.ModuleType('motor')
motor_asyncio_module = types.ModuleType('motor.motor_asyncio')
motor_asyncio_module.AsyncIOMotorDatabase = object
motor_module.motor_asyncio = motor_asyncio_module
sys.modules.setdefault('motor', motor_module)
sys.modules.setdefault('motor.motor_asyncio', motor_asyncio_module)

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


shared_models_base_module.PlayerStatistics = PlayerStatistics
shared_models_module.base = shared_models_base_module
shared_module.models = shared_models_module
sys.modules.setdefault('shared', shared_module)
sys.modules.setdefault('shared.models', shared_models_module)
sys.modules.setdefault('shared.models.base', shared_models_base_module)


from repository.mongo_repository import MongoStatisticsRepository


def get_nested_value(doc, path):
    current = doc
    for part in path.split('.'):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def matches_query(doc, query):
    if not query:
        return True

    for key, value in query.items():
        if key == '$or':
            if not any(matches_query(doc, clause) for clause in value):
                return False
            continue

        actual = get_nested_value(doc, key)
        if isinstance(value, dict):
            if '$in' in value:
                if actual not in value['$in']:
                    return False
            else:
                return False
        elif actual != value:
            return False

    return True


def apply_projection(doc, projection):
    if not projection:
        return copy.deepcopy(doc)

    include_keys = [key for key, enabled in projection.items() if enabled]
    if include_keys:
        projected = {}
        for key in include_keys:
            if key in doc:
                projected[key] = copy.deepcopy(doc[key])
        return projected

    projected = copy.deepcopy(doc)
    for key, enabled in projection.items():
        if enabled == 0:
            projected.pop(key, None)
    return projected


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, key, order):
        self.docs.sort(key=lambda doc: get_nested_value(doc, key) or 0, reverse=order < 0)
        return self

    def limit(self, count):
        self.docs = self.docs[:count]
        return self

    async def to_list(self, length=None):
        if length is None:
            return copy.deepcopy(self.docs)
        return copy.deepcopy(self.docs[:length])

    def __aiter__(self):
        self._iter = iter(self.docs)
        return self

    async def __anext__(self):
        try:
            return copy.deepcopy(next(self._iter))
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeCollection:
    def __init__(self, docs):
        self.docs = list(docs)

    def find(self, query=None, projection=None):
        docs = [apply_projection(doc, projection) for doc in self.docs if matches_query(doc, query or {})]
        return FakeCursor(docs)

    async def find_one(self, query=None, projection=None):
        for doc in self.docs:
            if matches_query(doc, query or {}):
                return apply_projection(doc, projection)
        return None


class FakeDatabase:
    def __init__(self, collections):
        self.collections = {name: FakeCollection(docs) for name, docs in collections.items()}

    def __getitem__(self, name):
        return self.collections[name]


class RepositoryRichOutputTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.repo = MongoStatisticsRepository(
            FakeDatabase(
                {
                    'player_statistics': [
                        {
                            'player_id': '10',
                            'match_id': 'm1',
                            'scoutpro_player_id': 'sp10',
                            'competition_id': 1,
                            'passes': 30,
                            'passes_successful': 27,
                            'goals': 1,
                            'assists': 0,
                            'shots': 3,
                            'shots_on_target': 2,
                            'total_xg': 0.8,
                            'total_xa': 0.2,
                            'key_passes': 2,
                            'progressive_passes': 6,
                            'minutes_played': 90,
                        },
                        {
                            'player_id': '10',
                            'match_id': 'm2',
                            'scoutpro_player_id': 'sp10',
                            'competition_id': 1,
                            'passes': 20,
                            'passes_successful': 18,
                            'goals': 0,
                            'assists': 1,
                            'shots': 1,
                            'shots_on_target': 1,
                            'total_xg': 0.3,
                            'total_xa': 0.4,
                            'key_passes': 3,
                            'progressive_passes': 4,
                            'minutes_played': 90,
                        },
                        {
                            'player_id': '20',
                            'match_id': 'm1',
                            'scoutpro_player_id': 'sp20',
                            'competition_id': 1,
                            'passes': 25,
                            'passes_successful': 18,
                            'goals': 2,
                            'assists': 0,
                            'shots': 4,
                            'shots_on_target': 2,
                            'total_xg': 1.1,
                            'total_xa': 0.1,
                            'key_passes': 1,
                            'progressive_passes': 2,
                            'minutes_played': 90,
                        },
                    ],
                    'player_statistics_per90': [],
                    'team_statistics': [
                        {
                            'team_id': '1',
                            'match_id': 'm1',
                            'scoutpro_team_id': 'st1',
                            'competition_id': 1,
                            'goals': 2,
                            'goals_against': 1,
                            'total_xg': 1.4,
                            'total_xg_against': 0.8,
                            'passes': 420,
                            'passes_successful': 353,
                            'passes_against': 390,
                            'shots': 10,
                            'shots_on_target': 5,
                            'key_passes': 9,
                            'progressive_passes': 24,
                            'high_regains': 8,
                        },
                        {
                            'team_id': '1',
                            'match_id': 'm2',
                            'scoutpro_team_id': 'st1',
                            'competition_id': 1,
                            'goals': 3,
                            'goals_against': 1,
                            'total_xg': 1.8,
                            'total_xg_against': 0.9,
                            'passes': 440,
                            'passes_successful': 370,
                            'passes_against': 380,
                            'shots': 13,
                            'shots_on_target': 6,
                            'key_passes': 11,
                            'progressive_passes': 26,
                            'high_regains': 10,
                        },
                        {
                            'team_id': '2',
                            'match_id': 'm1',
                            'scoutpro_team_id': 'st2',
                            'competition_id': 1,
                            'goals': 1,
                            'goals_against': 2,
                            'total_xg': 0.9,
                            'total_xg_against': 1.4,
                            'passes': 390,
                            'passes_successful': 300,
                            'passes_against': 420,
                            'shots': 8,
                            'shots_on_target': 3,
                            'key_passes': 5,
                            'progressive_passes': 14,
                            'high_regains': 4,
                        },
                    ],
                    'match_events': [
                        {'match_id': '100', 'team_id': '1', 'player_id': '10', 'type_name': 'pass', 'minute': 5},
                        {'match_id': '100', 'team_id': '1', 'player_id': '10', 'type_name': 'goal', 'minute': 15, 'is_goal': True},
                        {'match_id': '100', 'team_id': '2', 'player_id': '20', 'type_name': 'shot', 'minute': 30},
                    ],
                    'match_statistics': [
                        {
                            'match_id': '100',
                            'competition_id': 1,
                            'season_id': 2025,
                            'home_team_id': '1',
                            'away_team_id': '2',
                            'home_goals': 2,
                            'away_goals': 1,
                            'home_shots': 10,
                            'away_shots': 8,
                            'home_shots_on_target': 5,
                            'away_shots_on_target': 3,
                            'home_xg': 1.4,
                            'away_xg': 0.9,
                            'home_passes': 420,
                            'away_passes': 390,
                            'home_passes_successful': 353,
                            'away_passes_successful': 300,
                            'home_pass_accuracy': 84.05,
                            'away_pass_accuracy': 76.92,
                            'total_events': 3,
                            'updated_at': '2026-05-06T00:00:00',
                        }
                    ],
                    'match_tactical_snapshot': [],
                    'match_pass_network': [],
                    'match_sequence_summary': [],
                    'players': [
                        {'uID': '10', 'provider_ids': {'opta': 'p10'}, 'scoutpro_id': 'sp10', 'name': 'Alpha', 'position': 'Forward', 'club': 'City', 'nationality': 'A', 'age': 24},
                        {'uID': '20', 'provider_ids': {'opta': 'p20'}, 'scoutpro_id': 'sp20', 'name': 'Beta', 'position': 'Midfielder', 'club': 'United', 'nationality': 'B', 'age': 27},
                    ],
                    'teams': [
                        {'uID': '1', 'provider_ids': {'opta': 't1'}, 'scoutpro_id': 'st1', 'name': 'Home FC', 'country': 'X'},
                        {'uID': '2', 'provider_ids': {'opta': 't2'}, 'scoutpro_id': 'st2', 'name': 'Away FC', 'country': 'Y'},
                    ],
                    'matches': [
                        {'uID': '100', 'homeTeamID': '1', 'awayTeamID': '2', 'homeTeamName': 'Home FC', 'awayTeamName': 'Away FC'}
                    ],
                }
            )
        )

    async def test_player_rankings_use_season_aggregates_and_rich_aliases(self):
        rankings = await self.repo.get_player_rankings('passAccuracy', competition_id=1, limit=10)

        self.assertEqual(rankings[0]['player_name'], 'Alpha')
        self.assertEqual(rankings[0]['player_id'], 'sp10')
        self.assertAlmostEqual(rankings[0]['passAccuracy'], 90.0)
        self.assertEqual(rankings[0]['keyPasses'], 5)
        self.assertEqual(rankings[0]['matchesPlayed'], 2)

    async def test_team_rankings_use_derived_team_metrics(self):
        rankings = await self.repo.get_team_rankings('xGPerMatch', competition_id=1, limit=10)

        self.assertEqual(rankings[0]['team_name'], 'Home FC')
        self.assertEqual(rankings[0]['team_id'], 'st1')
        self.assertAlmostEqual(rankings[0]['xGPerMatch'], 1.6)
        self.assertGreater(rankings[0]['passAccuracy'], rankings[1]['passAccuracy'])

    async def test_player_comparison_returns_normalized_players_and_metrics(self):
        comparison = await self.repo.get_player_comparison(['sp10', 'sp20'])

        self.assertEqual(len(comparison['players']), 2)
        self.assertEqual(comparison['players'][0]['player']['name'], 'Alpha')
        self.assertAlmostEqual(comparison['players'][0]['summary']['passAccuracy'], 90.0)
        metric_lookup = {metric['metric']: metric['values'] for metric in comparison['metrics']}
        self.assertIn('xG', metric_lookup)
        self.assertEqual(metric_lookup['goals'], [1.0, 2.0])

    async def test_match_advanced_metrics_merge_flat_stats_with_timeline(self):
        payload = await self.repo.get_match_advanced_metrics('100')

        self.assertIsNotNone(payload)
        self.assertEqual(payload['flat_stats']['home_xg'], 1.4)
        self.assertEqual(payload['metrics']['home_shots'], 10)
        self.assertTrue(payload['minuteTimeline'])
        self.assertEqual(payload['match']['homeTeamName'], 'Home FC')


if __name__ == '__main__':
    unittest.main()