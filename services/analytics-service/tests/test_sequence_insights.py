from pathlib import Path
import asyncio
import sys


SERVICE_ROOT = Path(__file__).resolve().parents[1]
SERVICES_ROOT = SERVICE_ROOT.parent

for path in (SERVICE_ROOT, SERVICES_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from services.analytics_handler import AnalyticsHandler  # noqa: E402


async def _build_sequence_payload():
    handler = AnalyticsHandler.__new__(AnalyticsHandler)
    handler.match_service_url = 'http://match-service:8000'

    async def fake_get_json(url, params=None):
        return {
            'data': {
                'id': '1080974',
                'home_team_id': 2137,
                'away_team_id': 378,
                'home_team_name': 'Home FC',
                'away_team_name': 'Away FC',
            }
        }

    async def fake_get_events_from_mongodb(match_id):
        return [
            {
                'event_id': '1',
                'team_id': 2137,
                'player_id': 10,
                'period': 1,
                'minute': 0,
                'second': 1,
                'type_name': 'pass',
                'provider': 'opta',
                'location': {'x': 20, 'y': 50},
                'end_location': {'x': 35, 'y': 50},
            },
            {
                'event_id': '2',
                'team_id': 2137,
                'player_id': 8,
                'period': 1,
                'minute': 0,
                'second': 5,
                'type_name': 'pass',
                'provider': 'opta',
                'location': {'x': 35, 'y': 50},
                'end_location': {'x': 72, 'y': 48},
            },
            {
                'event_id': '3',
                'team_id': 2137,
                'player_id': 9,
                'period': 1,
                'minute': 0,
                'second': 9,
                'type_name': 'shot',
                'provider': 'opta',
                'location': {'x': 82, 'y': 50},
                'is_goal': False,
            },
            {
                'event_id': '4',
                'team_id': 378,
                'player_id': 5,
                'period': 1,
                'minute': 0,
                'second': 12,
                'type_name': 'pass',
                'provider': 'opta',
                'location': {'x': 58, 'y': 42},
                'end_location': {'x': 48, 'y': 40},
            },
            {
                'event_id': '5',
                'team_id': 2137,
                'player_id': 6,
                'period': 1,
                'minute': 0,
                'second': 17,
                'type_name': 'pass',
                'provider': 'opta',
                'location': {'x': 65, 'y': 45},
                'end_location': {'x': 86, 'y': 47},
            },
            {
                'event_id': '6',
                'team_id': 2137,
                'player_id': 7,
                'period': 1,
                'minute': 0,
                'second': 20,
                'type_name': 'pass',
                'provider': 'opta',
                'location': {'x': 86, 'y': 47},
                'end_location': {'x': 91, 'y': 50},
            },
            {
                'event_id': '7',
                'team_id': 2137,
                'player_id': 11,
                'period': 1,
                'minute': 0,
                'second': 23,
                'type_name': 'shot',
                'provider': 'opta',
                'location': {'x': 90, 'y': 51},
                'is_goal': True,
            },
        ]

    handler._get_json = fake_get_json
    handler._get_events_from_mongodb = fake_get_events_from_mongodb

    return await handler.get_sequence_insights('1080974')


def test_sequence_insights_builds_team_summaries_and_rapid_regains():
    payload = asyncio.run(_build_sequence_payload())

    assert payload['matchId'] == '1080974'
    assert payload['matchLabel'] == 'Home FC vs Away FC'
    assert payload['providers'] == ['opta']
    assert len(payload['teamSummaries']) == 2

    home_summary = next(summary for summary in payload['teamSummaries'] if summary['teamId'] == '2137')
    assert home_summary['directAttacks'] == 2
    assert home_summary['boxEntries'] == 1
    assert home_summary['rapidRegains'] == 1

    top_sequence = payload['topSequences'][0]
    assert top_sequence['teamName'] == 'Home FC'
    assert top_sequence['endedWithGoal'] is True


async def _build_player_sequence_payload():
    handler = AnalyticsHandler.__new__(AnalyticsHandler)

    async def fake_get_player_dashboard(player_id, season=None):
        return {
            'player_id': player_id,
            'player': {
                'id': player_id,
                'name': 'Sequence Midfielder',
                'position': 'CM',
                'club': 'Home FC',
                'uID': '10',
            },
            'summary': {},
        }

    async def fake_get_recent_player_matches(player_id, player, limit=6):
        return [
            {
                'id': '1080974',
                'home_team_id': 2137,
                'away_team_id': 378,
                'home_team_name': 'Home FC',
                'away_team_name': 'Away FC',
                'date': '2024-01-01T12:00:00',
            }
        ]

    async def fake_get_events_from_mongodb(match_id):
        return [
            {
                'event_id': '1',
                'matchID': '1080974',
                'team_id': 2137,
                'player_id': 10,
                'period': 1,
                'minute': 0,
                'second': 1,
                'type_name': 'pass',
                'provider': 'opta',
                'location': {'x': 20, 'y': 50},
                'end_location': {'x': 35, 'y': 50},
            },
            {
                'event_id': '2',
                'matchID': '1080974',
                'team_id': 2137,
                'player_id': 8,
                'period': 1,
                'minute': 0,
                'second': 5,
                'type_name': 'pass',
                'provider': 'opta',
                'location': {'x': 35, 'y': 50},
                'end_location': {'x': 72, 'y': 48},
            },
            {
                'event_id': '3',
                'matchID': '1080974',
                'team_id': 2137,
                'player_id': 9,
                'period': 1,
                'minute': 0,
                'second': 9,
                'type_name': 'shot',
                'provider': 'opta',
                'location': {'x': 82, 'y': 50},
                'is_goal': False,
            },
            {
                'event_id': '4',
                'matchID': '1080974',
                'team_id': 378,
                'player_id': 5,
                'period': 1,
                'minute': 0,
                'second': 12,
                'type_name': 'pass',
                'provider': 'opta',
                'location': {'x': 58, 'y': 42},
                'end_location': {'x': 48, 'y': 40},
            },
            {
                'event_id': '5',
                'matchID': '1080974',
                'team_id': 2137,
                'player_id': '10',
                'period': 1,
                'minute': 0,
                'second': 17,
                'type_name': 'pass',
                'provider': 'opta',
                'location': {'x': 65, 'y': 45},
                'end_location': {'x': 86, 'y': 47},
            },
            {
                'event_id': '6',
                'matchID': '1080974',
                'team_id': 2137,
                'player_id': 7,
                'period': 1,
                'minute': 0,
                'second': 20,
                'type_name': 'pass',
                'provider': 'opta',
                'location': {'x': 86, 'y': 47},
                'end_location': {'x': 91, 'y': 50},
            },
            {
                'event_id': '7',
                'matchID': '1080974',
                'team_id': 2137,
                'player_id': 11,
                'period': 1,
                'minute': 0,
                'second': 23,
                'type_name': 'shot',
                'provider': 'opta',
                'location': {'x': 90, 'y': 51},
                'is_goal': True,
            },
        ]

    handler.get_player_dashboard = fake_get_player_dashboard
    handler._get_recent_player_matches = fake_get_recent_player_matches
    handler._get_events_from_mongodb = fake_get_events_from_mongodb

    return await handler.get_player_sequence_insights('10')


def test_player_sequence_insights_summarize_recent_involvement():
    payload = asyncio.run(_build_player_sequence_payload())

    assert payload['player_id'] == '10'
    assert payload['player']['name'] == 'Sequence Midfielder'
    assert payload['summary']['matchesAnalyzed'] == 1
    assert payload['summary']['totalSequences'] == 2
    assert payload['summary']['boxEntries'] == 1
    assert payload['summary']['goals'] == 1
    assert payload['summary']['totalPlayerActions'] == 2

    top_sequence = payload['topSequences'][0]
    assert top_sequence['matchLabel'] == 'Home FC vs Away FC'
    assert top_sequence['endedWithGoal'] is True
    assert top_sequence['playerActions'] == 1


async def _build_player_sequence_coverage_payload():
    handler = AnalyticsHandler.__new__(AnalyticsHandler)

    async def fake_get_player_sequence_insights(player_id, match_limit=6):
        if player_id == '10':
            return {
                'player_id': '10',
                'player': {'name': 'Sequence Midfielder'},
                'summary': {
                    'matchesAnalyzed': 2,
                    'totalSequences': 5,
                    'shotEndings': 2,
                    'goals': 1,
                },
            }

        return {
            'player_id': player_id,
            'player': {'name': 'Profile Only Winger'},
            'summary': {
                'matchesAnalyzed': 0,
                'totalSequences': 0,
                'shotEndings': 0,
                'goals': 0,
            },
        }

    handler.get_player_sequence_insights = fake_get_player_sequence_insights

    return await handler.get_player_sequence_coverage(['10', '11'])


def test_player_sequence_coverage_flags_sequence_ready_players():
    payload = asyncio.run(_build_player_sequence_coverage_payload())

    assert len(payload['items']) == 2

    ready = next(item for item in payload['items'] if item['player_id'] == '10')
    assert ready['hasCoverage'] is True
    assert ready['coverageState'] == 'sequence-ready'
    assert ready['totalSequences'] == 5

    profile_only = next(item for item in payload['items'] if item['player_id'] == '11')
    assert profile_only['hasCoverage'] is False
    assert profile_only['coverageState'] == 'profile-only'