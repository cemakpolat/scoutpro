"""
ingest_f24_all.py

Parses every f24_115_2019_<matchID> file under data/opta/2019/ and
bulk-upserts the events into the match_events MongoDB collection.

Also updates each match document to status='finished' when the F24 file
contains a full-time end_period event.

Usage (run inside Docker):
    docker cp scripts/ingest_f24_all.py scoutpro-mongo:/tmp/
    docker exec -it scoutpro-mongo python3 /tmp/ingest_f24_all.py

Or with env overrides:
    MONGODB_URL=... DATA_ROOT=... python3 scripts/ingest_f24_all.py
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, UpdateOne

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ingest_f24_all")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MONGODB_URL = os.environ.get(
    "MONGODB_URL",
    "mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin",
)
DB_NAME = os.environ.get("MONGODB_DATABASE", "scoutpro")

_script_dir = Path(__file__).resolve().parent
DATA_ROOT = Path(os.environ.get("DATA_ROOT", str(_script_dir.parent / "data")))
OPTA_2019  = DATA_ROOT / "opta" / "2019"

# Opta F24 type_id → human name
TYPE_MAP: Dict[int, str] = {
    1: "pass", 2: "offside_pass", 3: "take_on", 4: "foul", 5: "out",
    6: "corner_awarded", 7: "tackle", 8: "interception", 9: "turnover",
    10: "save", 11: "claim", 12: "clearance", 13: "miss", 14: "post",
    15: "attempt_saved", 16: "goal", 17: "card", 18: "player_off",
    19: "player_on", 20: "player_changed_position", 21: "player_retired",
    22: "player_returns", 23: "player_becomes_goalkeeper",
    24: "goalkeeper_becomes_player", 25: "condition_change",
    27: "start_delay", 28: "end_delay", 30: "end", 32: "start_period",
    34: "end_period", 35: "stop_page_play", 37: "resume", 38: "temp_goal",
    40: "goal_confirmed", 41: "ball_recovery", 43: "blocked_pass",
    44: "pre_match", 45: "formation", 48: "punch", 49: "good_skill",
    50: "deleted_event", 51: "fifty_fifty", 52: "failed_to_block",
    53: "pre_match_pass", 54: "aerial_lost", 55: "challenge",
    56: "ball_touch", 57: "error", 58: "dispossessed", 59: "fifty_fifty",
    60: "keeper_pickup", 61: "chance_missed", 63: "keeper_saves",
    64: "possession", 65: "good_skill", 67: "blocked_pass",
    68: "attempt_blocked", 70: "goalkeeper_save", 71: "good_skill",
    73: "block", 74: "blocked_shot", 75: "dribble", 76: "error",
    77: "keeper_sweeper",
}

GOAL_TYPE_IDS = {16}  # type_id 16 = goal

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _int(v) -> Optional[int]:
    try:
        return int(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _float(v) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_qualifiers(raw_q) -> Dict[str, str]:
    """Convert Q list [ {"@attributes": {"qualifier_id": "X", "value": "Y"}} ] to dict."""
    if not raw_q:
        return {}
    if isinstance(raw_q, dict):
        raw_q = [raw_q]
    result: Dict[str, str] = {}
    for q in raw_q:
        attrs = q.get("@attributes", {})
        qid = str(attrs.get("qualifier_id", ""))
        val = attrs.get("value", "")
        if qid:
            result[qid] = val
    return result


def _parse_f24_file(path: Path) -> tuple[str, List[Dict[str, Any]]]:
    """
    Returns (match_id, [normalized_event_doc, ...])
    """
    # Extract match ID from filename:  f24_115_2019_1081234
    m = re.search(r"f24_\d+_\d+_(\d+)$", path.name)
    if not m:
        return "", []
    match_id = m.group(1)

    try:
        raw = json.loads(path.read_bytes())
    except Exception as e:
        log.warning(f"Cannot parse {path.name}: {e}")
        return match_id, []

    # Navigate: {"Games": {"Game": {"Event": [...], "@attributes": {...}}}}
    game = raw.get("Games", {}).get("Game", {})
    if not game:
        return match_id, []

    raw_events = game.get("Event", [])
    if isinstance(raw_events, dict):
        raw_events = [raw_events]

    docs: List[Dict[str, Any]] = []
    for ev in raw_events:
        attrs = ev.get("@attributes", {})
        type_id = _int(attrs.get("type_id"))
        if type_id is None:
            continue

        type_name = TYPE_MAP.get(type_id, f"type_{type_id}")
        event_id  = str(attrs.get("id", ""))
        player_id = _int(attrs.get("player_id"))
        team_id   = _int(attrs.get("team_id"))
        minute    = _int(attrs.get("min")) or 0
        second    = _int(attrs.get("sec")) or 0
        period    = _int(attrs.get("period_id")) or 0
        outcome   = attrs.get("outcome")
        is_succ   = outcome == "1" if outcome is not None else None
        x_raw     = _float(attrs.get("x"))
        y_raw     = _float(attrs.get("y"))
        is_goal   = type_id in GOAL_TYPE_IDS

        location = {"x": x_raw, "y": y_raw} if x_raw is not None and y_raw is not None else None
        qualifiers = _parse_qualifiers(ev.get("Q", []))

        raw_event_payload = {
            "event_id":  event_id,
            "match_id":  match_id,
            "player_id": str(player_id) if player_id is not None else None,
            "team_id":   str(team_id)   if team_id   is not None else None,
            "minute":    minute,
            "second":    second,
            "period":    period,
            "type_name": type_name,
            "provider":  "opta",
            "location":  location,
            "qualifiers": qualifiers,
            "is_goal":   is_goal,
            "is_successful": is_succ,
        }

        doc = {
            "event_id":   event_id,
            "matchID":    match_id,
            "match_id":   match_id,
            "player_id":  player_id,
            "team_id":    team_id,
            "minute":     minute,
            "second":     second,
            "period":     period,
            "type_name":  type_name,
            "type_id":    type_id,
            "provider":   "opta",
            "location":   location,
            "qualifiers": qualifiers,
            "is_goal":    is_goal,
            "is_successful": is_succ,
            "timestamp_seconds": minute * 60 + second,
            "timestamp":  minute * 60 + second,
            "ingested_at": _now(),
            "raw_event":   raw_event_payload,
        }
        docs.append(doc)

    return match_id, docs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log.info(f"Connecting to MongoDB…")
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=8000)
    db = client[DB_NAME]
    try:
        client.admin.command("ping")
        log.info("MongoDB OK")
    except Exception as e:
        log.error(f"Cannot connect: {e}")
        sys.exit(1)

    events_col  = db["match_events"]
    matches_col = db["matches"]

    # Discover all f24 files
    f24_files = sorted(OPTA_2019.glob("f24_115_2019_*"))
    # Also pick up the 2017 file in data/opta/
    extra_dir = DATA_ROOT / "opta" / "f24_115_2017_935592"
    if extra_dir.is_file():
        f24_files = list(f24_files) + [extra_dir]

    log.info(f"Found {len(f24_files)} F24 files in {OPTA_2019}")

    total_events = 0
    total_new    = 0
    matches_updated = 0

    for path in f24_files:
        match_id, docs = _parse_f24_file(path)
        if not match_id or not docs:
            log.debug(f"  {path.name}: no events, skipping")
            continue

        # Bulk upsert events
        ops = [
            UpdateOne(
                {"matchID": match_id, "event_id": d["event_id"]},
                {"$set": d},
                upsert=True,
            )
            for d in docs
        ]
        r = events_col.bulk_write(ops, ordered=False)
        new = r.upserted_count
        total_new    += new
        total_events += len(docs)

        # Determine whether this match has a full-time end_period (period 2, type_id 30 or 34)
        has_ft = any(
            d["type_id"] in (30, 34) and d["period"] == 2
            for d in docs
        )
        status = "finished" if has_ft else "live"

        # Count goals per team
        home_score = away_score = None
        team_ids = list({d["team_id"] for d in docs if d["team_id"] is not None})

        # Update match doc status (don't overwrite scores if already set from F1)
        match_update: Dict[str, Any] = {"status": status, "updatedAt": _now()}
        matches_col.update_one(
            {"uID": match_id},
            {"$set": match_update},
        )
        matches_updated += 1

        log.info(f"  {path.name}: {len(docs)} events ({new} new), status={status}")

    log.info("=" * 60)
    log.info(f"Done. Files processed: {len(f24_files)}")
    log.info(f"Total events written:  {total_events} ({total_new} inserted, rest updated)")
    log.info(f"Matches status synced: {matches_updated}")
    client.close()


if __name__ == "__main__":
    main()
