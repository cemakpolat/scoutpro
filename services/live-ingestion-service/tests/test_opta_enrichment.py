from pathlib import Path
import sys


SERVICES_ROOT = Path(__file__).resolve().parents[2]
if str(SERVICES_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICES_ROOT))


from shared.adapters.opta.opta_parser import OptaParser


def test_opta_parser_enriches_pass_shot_and_clearance_events():
    parser = OptaParser()

    parsed = parser.parse_events(
        {
            "match_id": "935592",
            "events": [
                {
                    "@attributes": {
                        "id": "1",
                        "event_id": "1",
                        "type_id": "1",
                        "period_id": "1",
                        "min": "10",
                        "sec": "5",
                        "player_id": "100",
                        "team_id": "200",
                        "outcome": "1",
                        "x": "50",
                        "y": "40",
                    },
                    "Q": [
                        {"@attributes": {"qualifier_id": "140", "value": "82"}},
                        {"@attributes": {"qualifier_id": "141", "value": "52"}},
                        {"@attributes": {"qualifier_id": "2"}},
                        {"@attributes": {"qualifier_id": "154"}},
                        {"@attributes": {"qualifier_id": "212", "value": "32.5"}},
                        {"@attributes": {"qualifier_id": "213", "value": "12.0"}},
                    ],
                },
                {
                    "@attributes": {
                        "id": "2",
                        "event_id": "2",
                        "type_id": "10",
                        "period_id": "1",
                        "min": "11",
                        "sec": "2",
                        "player_id": "101",
                        "team_id": "200",
                        "outcome": "0",
                        "x": "88",
                        "y": "47",
                    },
                    "Q": [
                        {"@attributes": {"qualifier_id": "20"}},
                        {"@attributes": {"qualifier_id": "214"}},
                    ],
                },
                {
                    "@attributes": {
                        "id": "3",
                        "event_id": "3",
                        "type_id": "12",
                        "period_id": "1",
                        "min": "11",
                        "sec": "30",
                        "player_id": "102",
                        "team_id": "200",
                        "outcome": "1",
                        "x": "75",
                        "y": "55",
                    }
                },
            ],
        }
    )

    assert len(parsed) == 3

    pass_event, shot_event, clearance_event = parsed

    assert pass_event["type_name"] == "pass"
    assert pass_event["progressive_pass"] is True
    assert pass_event["entered_final_third"] is True
    assert pass_event["is_cross"] is True
    assert pass_event["is_key_pass"] is True
    assert pass_event["pass_length"] == 32.5
    assert pass_event["pass_angle"] == 12.0

    assert shot_event["type_name"] == "shot"
    assert shot_event["shot_outcome"] == "blocked"
    assert shot_event["is_big_chance"] is True
    assert shot_event["body_part"] == "right_foot"
    assert shot_event["analytical_xg"] > 0

    assert clearance_event["type_name"] == "clearance"
    assert clearance_event["high_regain"] is True


def test_opta_parser_accepts_normalized_qualifier_payloads():
    parser = OptaParser()

    parsed = parser.parse_events(
        {
            "match_id": "935592",
            "events": [
                {
                    "id": "10",
                    "event_id": "10",
                    "type_id": 1,
                    "period_id": 1,
                    "min": 24,
                    "sec": 8,
                    "player_id": "100",
                    "team_id": "200",
                    "outcome": 1,
                    "x": 45.0,
                    "y": 33.0,
                    "game_id": "935592",
                    "qualifiers": [
                        {"qualifier_id": 140, "value": "70"},
                        {"qualifier_id": 141, "value": "44"},
                        {"qualifier_id": 154, "value": None},
                    ],
                }
            ],
        }
    )

    assert len(parsed) == 1
    assert parsed[0]["type_name"] == "pass"
    assert parsed[0]["entered_final_third"] is True
    assert parsed[0]["is_key_pass"] is True