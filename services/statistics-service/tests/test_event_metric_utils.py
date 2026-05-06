from pathlib import Path
import sys


STATS_SERVICE_ROOT = Path(__file__).resolve().parents[1]
SERVICES_ROOT = Path(__file__).resolve().parents[2]

for path in (STATS_SERVICE_ROOT, SERVICES_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)


from services.event_metric_utils import EventMetricAccumulator


def test_event_metric_accumulator_builds_rich_pass_and_shot_increments():
    pass_event = {
        'type_name': 'pass',
        'is_successful': True,
        'progressive_pass': True,
        'entered_final_third': True,
        'entered_box': True,
        'is_cross': True,
        'is_key_pass': True,
        'is_assist': True,
        'pass_length': 34.5,
        'analytical_xa': 0.27,
    }
    shot_event = {
        'type_name': 'shot',
        'is_goal': True,
        'is_on_target': True,
        'is_big_chance': True,
        'location': {'x': 88, 'y': 50},
    }

    pass_increments = EventMetricAccumulator.build_increments(pass_event)
    shot_increments = EventMetricAccumulator.build_increments(shot_event)

    assert pass_increments['passes'] == 1
    assert pass_increments['passes_completed'] == 1
    assert pass_increments['progressive_passes'] == 1
    assert pass_increments['final_third_entries'] == 1
    assert pass_increments['passes_into_box'] == 1
    assert pass_increments['crosses'] == 1
    assert pass_increments['key_passes'] == 1
    assert pass_increments['assists'] == 1
    assert pass_increments['xA'] == 0.27
    assert pass_increments['xa_total'] == 0.27

    assert shot_increments['shots'] == 1
    assert shot_increments['shots_on_target'] == 1
    assert shot_increments['goals'] == 1
    assert shot_increments['big_chances'] == 1
    assert shot_increments['big_chances_scored'] == 1
    assert shot_increments['xg_total'] > 0
    assert shot_increments['shots_with_xg'] == 1