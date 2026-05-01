from pathlib import Path
import importlib.util
import sys
import types


SERVICE_ROOT = Path(__file__).resolve().parents[1]

for path in (SERVICE_ROOT, SERVICE_ROOT.parent):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def _load_match_stream_processor():
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
    shared_messaging.EventType = types.SimpleNamespace(
        MATCH_CREATED="match_created",
        MATCH_UPDATED="match_updated",
    )
    shared_messaging.create_event = lambda **kwargs: types.SimpleNamespace(dict=lambda: kwargs)
    shared_messaging.get_kafka_producer = lambda: None
    sys.modules["shared.messaging"] = shared_messaging

    shared_utils_database = types.ModuleType("shared.utils.database")
    shared_utils_database.DatabaseManager = object
    sys.modules["shared.utils.database"] = shared_utils_database

    stream_handler_path = SERVICE_ROOT / "services" / "stream_handler.py"
    spec = importlib.util.spec_from_file_location("match_stream_handler", stream_handler_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.MatchStreamProcessor


def test_normalize_event_doc_preserves_enriched_event_fields():
    MatchStreamProcessor = _load_match_stream_processor()
    processor = MatchStreamProcessor.__new__(MatchStreamProcessor)

    raw_event = {
        "event_id": "evt-1",
        "player_id": "51521",
        "team_id": "2137",
        "minute": 10,
        "second": 5,
        "period": 1,
        "type_name": "pass",
        "provider": "opta",
        "location": {"x": 49.9, "y": 49.9},
        "end_location": {"x": 84.0, "y": 50.0},
        "qualifiers": {"140": "84.0", "141": "50.0", "210": ""},
        "is_goal": False,
        "is_successful": True,
        "timestamp_seconds": 605,
        "field_zone": "middle_third",
        "lane": "center",
        "end_field_zone": "attacking_third",
        "end_lane": "center",
        "pass_type": "through_ball",
        "pass_length": 34.1,
        "pass_angle": 2.6,
        "progressive_distance": 34.1,
        "progressive_pass": True,
        "entered_final_third": True,
        "entered_box": True,
        "is_assist": True,
        "is_key_pass": True,
    }

    doc = processor._normalize_event_doc("1080974", raw_event)

    assert doc["event_id"] == "evt-1"
    assert doc["matchID"] == "1080974"
    assert doc["match_id"] == "1080974"
    assert doc["timestamp_seconds"] == 605
    assert doc["location"] == {"x": 49.9, "y": 49.9}
    assert doc["end_location"] == {"x": 84.0, "y": 50.0}
    assert doc["field_zone"] == "middle_third"
    assert doc["lane"] == "center"
    assert doc["end_field_zone"] == "attacking_third"
    assert doc["end_lane"] == "center"
    assert doc["pass_type"] == "through_ball"
    assert doc["progressive_pass"] is True
    assert doc["entered_final_third"] is True
    assert doc["entered_box"] is True
    assert doc["is_assist"] is True
    assert doc["is_key_pass"] is True
    assert doc["is_successful"] is True
    assert doc["raw_event"]["progressive_pass"] is True