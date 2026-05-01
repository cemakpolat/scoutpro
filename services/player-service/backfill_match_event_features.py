#!/usr/bin/env python3

import argparse
import math
import os
from datetime import datetime, timezone

from pymongo import MongoClient, UpdateOne


FINAL_THIRD_X = 66.7
BOX_X_MIN = 83.0
BOX_Y_MIN = 21.0
BOX_Y_MAX = 79.0
PROGRESSIVE_PASS_MIN_X = 15.0
BACKFILL_VERSION = "2026-04-30-match-event-features-v1"


def optional_float(value):
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return False


def normalize_qualifiers(value):
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def normalize_location(value):
    if isinstance(value, dict):
        x_value = optional_float(value.get("x"))
        y_value = optional_float(value.get("y"))
        if x_value is None or y_value is None:
            return None
        return {"x": round(x_value, 2), "y": round(y_value, 2)}

    if isinstance(value, (list, tuple)) and len(value) >= 2:
        x_value = optional_float(value[0])
        y_value = optional_float(value[1])
        if x_value is None or y_value is None:
            return None
        return {"x": round(x_value, 2), "y": round(y_value, 2)}

    return None


def field_zone(x_value):
    if x_value is None:
        return None
    if x_value < 33.3:
        return "defensive_third"
    if x_value < FINAL_THIRD_X:
        return "middle_third"
    return "attacking_third"


def lane(y_value):
    if y_value is None:
        return None
    if y_value < 33.3:
        return "left"
    if y_value > 66.7:
        return "right"
    return "center"


def in_box(location):
    if not location:
        return False
    return (
        location["x"] >= BOX_X_MIN
        and BOX_Y_MIN <= location["y"] <= BOX_Y_MAX
    )


def body_part_from_qualifiers(qualifiers):
    if "15" in qualifiers:
        return "head"
    if "72" in qualifiers:
        return "left_foot"
    if "20" in qualifiers:
        return "right_foot"
    if "21" in qualifiers:
        return "other"
    return None


def coordinate_from_qualifiers(qualifiers):
    x_value = optional_float(qualifiers.get("140"))
    y_value = optional_float(qualifiers.get("141"))
    if x_value is None or y_value is None:
        return None
    return {"x": round(x_value, 2), "y": round(y_value, 2)}


def pass_length(start_location, end_location, qualifiers):
    qualifier_length = optional_float(qualifiers.get("212"))
    if qualifier_length is not None:
        return round(qualifier_length, 2)
    if not start_location or not end_location:
        return None
    distance = math.sqrt(
        ((end_location["x"] - start_location["x"]) ** 2)
        + ((end_location["y"] - start_location["y"]) ** 2)
    )
    return round(distance, 2)


def pass_angle(start_location, end_location, qualifiers):
    qualifier_angle = optional_float(qualifiers.get("213"))
    if qualifier_angle is not None:
        return round(qualifier_angle, 2)
    if not start_location or not end_location:
        return None
    angle_value = math.degrees(
        math.atan2(
            end_location["y"] - start_location["y"],
            end_location["x"] - start_location["x"],
        )
    )
    return round(angle_value, 2)


def distance_to_goal(location):
    if not location:
        return None
    dx = ((100.0 - location["x"]) / 100.0) * 105.0
    dy = ((50.0 - location["y"]) / 100.0) * 68.0
    return round(math.sqrt((dx ** 2) + (dy ** 2)), 2)


def angle_to_goal(location):
    if not location:
        return None
    dx = max(100.0 - location["x"], 0.1)
    return round(math.degrees(math.atan2(abs(location["y"] - 50.0), dx)), 2)


def analytical_xg(location, body_part, shot_type):
    shot_distance = distance_to_goal(location)
    if shot_distance is None:
        return None
    base_xg = 0.35 * math.exp(-0.1 * max(shot_distance, 1.0))
    if body_part and "head" in body_part:
        base_xg *= 0.6
    if shot_type == "penalty":
        base_xg = 0.76
    return round(base_xg, 4)


def derive_pass_type(raw_event, qualifiers):
    pass_type = str(raw_event.get("pass_type") or "").lower()
    if pass_type:
        return pass_type
    if "2" in qualifiers:
        return "cross"
    if "4" in qualifiers or "266" in qualifiers:
        return "through_ball"
    if "196" in qualifiers:
        return "switch"
    if "1" in qualifiers:
        return "long_ball"
    if "6" in qualifiers:
        return "corner"
    if "5" in qualifiers:
        return "free_kick"
    if "107" in qualifiers:
        return "throw_in"
    return "short"


def derive_shot_type(raw_event, qualifiers):
    shot_type = str(raw_event.get("shot_type") or "").lower()
    if shot_type:
        return shot_type
    if "9" in qualifiers:
        return "penalty"
    if "26" in qualifiers or "97" in qualifiers:
        return "free_kick"
    if "25" in qualifiers or "96" in qualifiers:
        return "corner"
    return "open_play"


def derive_doc_updates(doc):
    raw_event = doc.get("raw_event") if isinstance(doc.get("raw_event"), dict) else {}
    qualifiers = normalize_qualifiers(doc.get("qualifiers") or raw_event.get("qualifiers"))
    start_location = normalize_location(doc.get("location") or raw_event.get("location"))
    end_location = normalize_location(doc.get("end_location") or raw_event.get("end_location") or coordinate_from_qualifiers(qualifiers))

    minute = int(doc.get("minute") or raw_event.get("minute") or 0)
    second = int(doc.get("second") or raw_event.get("second") or 0)
    period = int(doc.get("period") or raw_event.get("period") or 1)
    timestamp_seconds = optional_float(doc.get("timestamp_seconds"))
    if timestamp_seconds is None:
        timestamp_seconds = optional_float(raw_event.get("timestamp_seconds"))
    if timestamp_seconds is None:
        timestamp_seconds = float((minute * 60) + second)

    updates = {
        "match_id": str(doc.get("match_id") or doc.get("matchID") or raw_event.get("match_id") or ""),
        "timestamp_seconds": timestamp_seconds,
        "feature_backfill_version": BACKFILL_VERSION,
        "feature_backfilled_at": datetime.now(timezone.utc).isoformat(),
    }

    if start_location:
        updates["location"] = start_location
        updates["field_zone"] = field_zone(start_location["x"])
        updates["lane"] = lane(start_location["y"])

    if end_location:
        updates["end_location"] = end_location
        updates["end_field_zone"] = field_zone(end_location["x"])
        updates["end_lane"] = lane(end_location["y"])

    type_name = str(doc.get("type_name") or raw_event.get("type_name") or "").lower()

    if type_name == "pass":
        is_successful = raw_event.get("is_successful")
        if is_successful is None:
            is_successful = doc.get("is_successful")
        if is_successful is not None:
            updates["is_successful"] = bool(is_successful)

        updates["pass_type"] = derive_pass_type(raw_event, qualifiers)
        updates["recipient_id"] = raw_event.get("recipient_id")
        updates["pass_length"] = pass_length(start_location, end_location, qualifiers)
        updates["pass_angle"] = pass_angle(start_location, end_location, qualifiers)
        updates["is_cross"] = truthy(raw_event.get("is_cross")) or ("2" in qualifiers)
        updates["is_through_ball"] = truthy(raw_event.get("is_through_ball")) or ("4" in qualifiers) or ("266" in qualifiers)
        updates["is_long_ball"] = truthy(raw_event.get("is_long_ball")) or ("1" in qualifiers)
        updates["is_switch"] = truthy(raw_event.get("is_switch")) or ("196" in qualifiers)
        updates["is_cutback"] = truthy(raw_event.get("is_cutback")) or ("195" in qualifiers)
        updates["is_key_pass"] = truthy(raw_event.get("is_key_pass")) or truthy(raw_event.get("assist_potential")) or ("154" in qualifiers) or ("210" in qualifiers)
        updates["is_assist"] = truthy(raw_event.get("is_assist")) or ("210" in qualifiers)
        updates["is_second_assist"] = truthy(raw_event.get("is_second_assist")) or ("218" in qualifiers)
        updates["is_set_piece"] = truthy(raw_event.get("is_set_piece")) or any(key in qualifiers for key in ("5", "6", "107", "241", "279"))

        if start_location and end_location:
            progressive_distance = round(end_location["x"] - start_location["x"], 2)
            updates["progressive_distance"] = progressive_distance
            successful_pass = bool(updates.get("is_successful"))
            updates["progressive_pass"] = truthy(raw_event.get("progressive_pass")) or (successful_pass and progressive_distance >= PROGRESSIVE_PASS_MIN_X)
            updates["entered_final_third"] = truthy(raw_event.get("entered_final_third")) or (successful_pass and start_location["x"] < FINAL_THIRD_X <= end_location["x"])
            updates["entered_box"] = truthy(raw_event.get("entered_box")) or (successful_pass and (not in_box(start_location)) and in_box(end_location))

    if type_name in {"shot", "chance_missed"}:
        shot_type = derive_shot_type(raw_event, qualifiers)
        shot_body_part = str(raw_event.get("body_part") or body_part_from_qualifiers(qualifiers) or "foot")
        updates["shot_type"] = shot_type
        updates["body_part"] = shot_body_part
        updates["xg_value"] = optional_float(doc.get("xg_value")) or optional_float(raw_event.get("xg_value"))
        updates["shot_distance"] = distance_to_goal(start_location)
        updates["shot_angle"] = angle_to_goal(start_location)
        updates["analytical_xg"] = analytical_xg(start_location, shot_body_part, shot_type)
        updates["is_big_chance"] = truthy(raw_event.get("is_big_chance")) or ("214" in qualifiers)
        updates["is_first_time"] = truthy(raw_event.get("is_first_time")) or ("328" in qualifiers)
        updates["is_assisted"] = truthy(raw_event.get("is_assisted")) or any(key in qualifiers for key in ("29", "154", "210", "217"))
        updates["is_set_piece"] = truthy(raw_event.get("is_set_piece")) or shot_type != "open_play"
        updates["from_corner"] = shot_type == "corner"
        updates["from_free_kick"] = shot_type == "free_kick"
        updates["is_penalty"] = shot_type == "penalty"
        if doc.get("is_goal"):
            updates["is_on_target"] = True

    if type_name in {"interception", "tackle", "clearance"}:
        high_regain = truthy(raw_event.get("high_regain"))
        if not high_regain and start_location:
            high_regain = start_location["x"] >= FINAL_THIRD_X
        updates["high_regain"] = high_regain

    if type_name == "ball_control":
        action_type = str(raw_event.get("action_type") or doc.get("action_type") or "")
        if action_type:
            updates["action_type"] = action_type
        if action_type == "recovery":
            updates["high_regain"] = truthy(raw_event.get("high_regain")) or bool(start_location and start_location["x"] >= FINAL_THIRD_X)

    return {key: value for key, value in updates.items() if value is not None}


def run_backfill(limit=None, match_id=None, dry_run=False):
    mongo_uri = (
        os.getenv("MONGODB_URL")
        or os.getenv("MONGO_URI")
        or f"mongodb://root:scoutpro123@{os.getenv('MONGODB_HOST', 'localhost')}:{os.getenv('MONGODB_PORT', '27017')}/{os.getenv('MONGODB_DATABASE', 'scoutpro')}?authSource=admin"
    )
    mongo_database = os.getenv("MONGODB_DATABASE") or os.getenv("MONGO_DATABASE") or "scoutpro"

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client[mongo_database]
    collection = db["match_events"]

    query = {}
    if match_id:
        query["$or"] = [
            {"matchID": match_id},
            {"matchID": int(match_id)} if str(match_id).isdigit() else {"matchID": match_id},
            {"match_id": match_id},
        ]

    cursor = collection.find(query)
    if limit:
        cursor = cursor.limit(limit)

    processed = 0
    changed = 0
    operations = []

    for doc in cursor:
        processed += 1
        updates = derive_doc_updates(doc)
        payload = {key: value for key, value in updates.items() if doc.get(key) != value}
        if not payload:
            continue

        changed += 1
        if not dry_run:
            operations.append(UpdateOne({"_id": doc["_id"]}, {"$set": payload}))
            if len(operations) >= 500:
                collection.bulk_write(operations, ordered=False)
                operations.clear()

    if operations:
        collection.bulk_write(operations, ordered=False)

    print(f"Processed: {processed}")
    print(f"Changed: {changed}")
    print(f"Dry run: {dry_run}")

    if not dry_run:
        print("Updated feature coverage:")
        print(f"  timestamp_seconds: {collection.count_documents({'timestamp_seconds': {'$exists': True, '$ne': None}})}")
        print(f"  field_zone: {collection.count_documents({'field_zone': {'$exists': True, '$ne': None}})}")
        print(f"  end_location: {collection.count_documents({'end_location': {'$exists': True, '$ne': None}})}")
        print(f"  progressive_pass: {collection.count_documents({'progressive_pass': True})}")
        print(f"  entered_final_third: {collection.count_documents({'entered_final_third': True})}")
        print(f"  entered_box: {collection.count_documents({'entered_box': True})}")
        print(f"  high_regain: {collection.count_documents({'high_regain': True})}")
        print(f"  analytical_xg: {collection.count_documents({'analytical_xg': {'$exists': True, '$ne': None}})}")


def parse_args():
    parser = argparse.ArgumentParser(description="Backfill tactical event features into match_events.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of processed documents.")
    parser.add_argument("--match-id", type=str, default=None, help="Only backfill one match.")
    parser.add_argument("--dry-run", action="store_true", help="Compute updates without writing them.")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run_backfill(limit=arguments.limit, match_id=arguments.match_id, dry_run=arguments.dry_run)