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


async def _build_player_insights_payload():
    handler = AnalyticsHandler.__new__(AnalyticsHandler)
    handler.ml_service_url = 'http://ml-service:8000'

    async def fake_get_player_dashboard(player_id, season=None):
        return {
            'player_id': player_id,
            'player': {
                'id': player_id,
                'name': 'Sequence Midfielder',
                'position': 'CM',
                'club': 'Home FC',
                'birthDate': '2002-05-10',
            },
            'statistics': {
                'minutes_played': 2250,
                'matches_played': 28,
                'total_xg': 6.4,
                'shots': 42,
                'goals': 7,
                'goal_assist': 5,
                'key_passes': 34,
                'progressive_passes': 112,
                'entered_final_third': 86,
                'entered_box': 22,
                'pressures': 148,
                'recoveries': 169,
                'interceptions': 41,
                'tackles': 48,
                'high_regains': 21,
                'assists_from_set_play': 2,
                'assists_from_corners': 1,
                'assists_from_free_kick': 1,
                'total_free_kicks_taken': 18,
                'total_corners': 26,
                'pass_accuracy': 84.2,
            },
            'summary': {
                'goals': 7,
                'assists': 5,
                'passAccuracy': 84.2,
                'rating': 7.8,
                'age': 23,
                'position': 'CM',
            },
        }

    async def fake_get_json(url, params=None, suppress_statuses=None):
        if url.endswith('/trajectory'):
            return {
                'data': {
                    'historical_trajectory': [
                        {'cluster_name': 'Starter'},
                    ],
                    'forecast': [
                        {'predicted_cluster_name': 'Key Player'},
                    ],
                }
            }
        if url.endswith('/market-value'):
            return {
                'data': {
                    'estimateMillionEUR': 23.4,
                    'displayValue': 'EUR 23.4m',
                    'confidence': 79.0,
                    'band': 'premium-starter',
                    'factors': {'age': 23},
                }
            }
        return {}

    handler.get_player_dashboard = fake_get_player_dashboard
    handler._get_json = fake_get_json

    return await handler.get_player_insights('10')


def test_player_insights_include_scouting_profile_and_valuation():
    payload = asyncio.run(_build_player_insights_payload())

    assert payload['insights'][2]['value'] == 'EUR 23.4m'
    assert payload['scoutingProfile']['marketValue']['estimateMillionEUR'] == 23.4
    assert payload['scoutingProfile']['developmentCurve']['phase'] == 'pre-prime'
    assert payload['scoutingProfile']['developmentCurve']['nextCluster'] == 'Key Player'
    assert payload['scoutingProfile']['ballProgression']['progressivePassesPer90'] == 4.48
    assert payload['scoutingProfile']['setPieceImpact']['setPlayAssists'] == 2


async def _build_team_insights_payload():
    handler = AnalyticsHandler.__new__(AnalyticsHandler)

    async def fake_get_team_dashboard(team_id, season=None):
        return {
            'team_id': team_id,
            'team': {
                'id': team_id,
                'name': 'Home FC',
            },
            'statistics': {
                'matches_played': 30,
                'goals': 52,
                'total_xg': 54.3,
                'total_xg_against': 29.1,
                'shots': 410,
                'shots_on_target': 161,
                'pass_accuracy': 85.4,
                'possession_percentage': 58.2,
                'progressive_passes': 510,
                'entered_final_third': 392,
                'entered_box': 118,
                'pressures': 454,
                'high_regains': 172,
                'corners': 210,
                'total_free_kicks_taken': 156,
                'assists_from_set_play': 12,
                'assists_from_corners': 5,
                'assists_from_free_kick': 3,
            },
            'summary': {
                'avgGoalsFor': 1.73,
                'avgGoalsAgainst': 1.03,
                'form': ['W', 'W', 'D'],
                'squadSize': 25,
            },
        }

    handler.get_team_dashboard = fake_get_team_dashboard

    return await handler.get_team_insights('2137')


def test_team_insights_include_tactical_fingerprint_and_set_piece_profile():
    payload = asyncio.run(_build_team_insights_payload())

    assert payload['insights'][0]['value'] == 'possession-dominant'
    assert payload['scoutingProfile']['tacticalFingerprint']['primaryStyle'] == 'possession-dominant'
    assert payload['scoutingProfile']['pressingProfile']['pressIntensity'] == 'high'
    assert payload['scoutingProfile']['progressionProfile']['progressivePassesPerMatch'] == 17.0
    assert payload['scoutingProfile']['setPieceProfile']['setPlayAssists'] == 12