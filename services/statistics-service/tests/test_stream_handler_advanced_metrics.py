from pathlib import Path
import importlib.util
import sys
import types


SERVICES_ROOT = Path(__file__).resolve().parents[2]
STATS_SERVICE_ROOT = Path(__file__).resolve().parents[1]

for path in (SERVICES_ROOT, STATS_SERVICE_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)


from shared.adapters.opta.opta_parser import OptaParser


def _load_statistics_stream_processor():
    config_module = types.ModuleType("config")
    config_settings_module = types.ModuleType("config.settings")
    config_settings_module.get_settings = lambda: types.SimpleNamespace(
        mongodb_url="mongodb://localhost:27017",
        mongodb_database="scoutpro",
    )
    config_module.settings = config_settings_module
    sys.modules["config"] = config_module
    sys.modules["config.settings"] = config_settings_module

    shared_messaging = types.ModuleType("shared.messaging")
    shared_messaging.KafkaConsumerClient = object
    shared_messaging.EventType = types.SimpleNamespace(STATS_AGGREGATED="stats_aggregated")
    shared_messaging.create_event = lambda **kwargs: types.SimpleNamespace(dict=lambda: kwargs)
    shared_messaging.get_kafka_producer = lambda: None
    sys.modules["shared.messaging"] = shared_messaging

    shared_utils_database = types.ModuleType("shared.utils.database")
    shared_utils_database.DatabaseManager = object
    sys.modules["shared.utils.database"] = shared_utils_database

    stream_handler_path = STATS_SERVICE_ROOT / "services" / "stream_handler.py"
    spec = importlib.util.spec_from_file_location("statistics_stream_handler", stream_handler_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.StatisticsStreamProcessor


def test_stream_handler_counts_new_opta_derived_metrics():
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
                        {"@attributes": {"qualifier_id": "140", "value": "84"}},
                        {"@attributes": {"qualifier_id": "141", "value": "50"}},
                        {"@attributes": {"qualifier_id": "2"}},
                        {"@attributes": {"qualifier_id": "210"}},
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

    pass_event, shot_event, clearance_event = parsed
    StatisticsStreamProcessor = _load_statistics_stream_processor()
    processor = StatisticsStreamProcessor.__new__(StatisticsStreamProcessor)

    pass_increments = processor._build_increments(pass_event)
    shot_increments = processor._build_increments(shot_event)
    clearance_increments = processor._build_increments(clearance_event)

    assert pass_increments["passes"] == 1
    assert pass_increments["progressive_passes"] == 1
    assert pass_increments["final_third_entries"] == 1
    assert pass_increments["passes_into_box"] == 1
    assert pass_increments["crosses"] == 1
    assert pass_increments["key_passes"] == 1
    assert pass_increments["assists"] == 1

    assert shot_increments["shots"] == 1
    assert shot_increments["big_chances"] == 1
    assert shot_increments["xG"] > 0
    assert shot_increments["xg_total"] == shot_increments["xG"]

    assert clearance_increments["clearances"] == 1
    assert clearance_increments["high_regains"] == 1