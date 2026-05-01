#!/usr/bin/env python3
"""
seed_players_from_f40.py

Reads the Opta F40 squad file and upserts full player profile data into
MongoDB's `players` collection.  Replaces the broken sync-pipeline path
that previously left height, weight, nationality, birth_date, preferred_foot
and other fields unpopulated.

Usage (from repo root):
    python3 scripts/seed_players_from_f40.py

Environment variables (all optional, sensible defaults for Docker Compose):
    F40_FILE         Path to the F40 JSON file
    MONGODB_URL      MongoDB connection string
    MONGODB_DATABASE MongoDB database name
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

from pymongo import MongoClient, UpdateOne

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

F40_FILE = Path(os.environ.get(
    "F40_FILE",
    str(REPO_ROOT / "data" / "opta" / "2019" / "f40_115_2019"),
))

MONGODB_URL = os.environ.get(
    "MONGODB_URL",
    "mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin",
)
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "scoutpro")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_stats(stat_list) -> dict:
    """Flatten F40 Stat array into {Type: value} dict."""
    if isinstance(stat_list, dict):
        stat_list = [stat_list]
    stats: dict = {}
    for s in (stat_list or []):
        t = s.get("@attributes", {}).get("Type", "")
        v = s.get("@value", "")
        if t and v:
            stats[t] = str(v)
    return stats


def _safe_int(value: str | None) -> int | None:
    if not value or value in ("Unknown", ""):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_date(value: str | None) -> str | None:
    if not value or value in ("Unknown", ""):
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        return None


def parse_players(f40_path: Path) -> list[dict]:
    """Parse the F40 file and return a flat list of player profile dicts."""
    with open(f40_path, encoding="utf-8") as fh:
        data = json.load(fh)

    doc = data.get("SoccerFeed", {}).get("SoccerDocument", {})
    comp_attrs = doc.get("@attributes", {})
    competition_id = comp_attrs.get("competition_id", "")
    season_id = comp_attrs.get("season_id", "")

    teams = doc.get("Team", [])
    if isinstance(teams, dict):
        teams = [teams]

    players: list[dict] = []
    for team in teams:
        team_attrs = team.get("@attributes", {})
        team_uid = team_attrs.get("uID", "")
        team_name = team.get("Name", "")
        team_country = team_attrs.get("country", "")

        raw_players = team.get("Player", [])
        if isinstance(raw_players, dict):
            raw_players = [raw_players]

        for p in raw_players:
            p_attrs = p.get("@attributes", {})
            uid = p_attrs.get("uID", "")
            if not uid:
                continue

            stats = _extract_stats(p.get("Stat", []))

            first_name = stats.get("first_name", "")
            last_name = stats.get("last_name", "")
            known_name = stats.get("known_name") or None
            full_name = f"{first_name} {last_name}".strip() or p.get("Name", "")

            position_raw = p.get("Position", "")

            # Normalise position to match Player model enum
            pos_map = {
                "Goalkeeper": "Goalkeeper",
                "Defender": "Defender",
                "Midfielder": "Midfielder",
                "Forward": "Forward",
            }
            position = pos_map.get(position_raw, position_raw)

            # Preferred foot
            foot_raw = stats.get("preferred_foot", "")
            foot = foot_raw.lower() if foot_raw and foot_raw not in ("Unknown", "") else None

            doc_out = {
                # Primary key used by player-service
                "uID": uid,

                # Names
                "name": full_name,
                "first": first_name,
                "last": last_name,
                "knownName": known_name,

                # Profile — height/weight stored as strings to match Player model
                "position": position,
                "detailedPosition": stats.get("real_position", position_raw),
                "positionSide": stats.get("real_position_side"),
                "nationality": stats.get("first_nationality") or stats.get("country") or "",
                "birthDate": _parse_date(stats.get("birth_date")),
                "birthPlace": stats.get("birth_place"),
                "height": str(_safe_int(stats.get("height"))) if _safe_int(stats.get("height")) else None,
                "weight": str(_safe_int(stats.get("weight"))) if _safe_int(stats.get("weight")) else None,
                "preferredFoot": foot,
                "shirtNumber": _safe_int(stats.get("jersey_num")),

                # Team context
                "teamID": team_uid,
                "teamName": team_name,
                "club": team_name,
                "teamCountry": team_country,

                # Competition context
                "competitionID": competition_id,
                "seasonID": season_id,

                # Data provenance
                "provider": "opta",
                "squadStatus": "active",
                "joinDate": _parse_date(stats.get("join_date")),
                "leaveDate": _parse_date(stats.get("leave_date")),
                "updatedAt": datetime.utcnow().isoformat(),
            }

            # Remove None-valued fields to keep documents clean
            doc_out = {k: v for k, v in doc_out.items() if v is not None}
            players.append(doc_out)

    return players


def seed(players: list[dict], mongo_url: str, db_name: str) -> None:
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=8000)
    db = client[db_name]
    collection = db["players"]

    ops = [
        UpdateOne({"uID": p["uID"]}, {"$set": p}, upsert=True)
        for p in players
    ]

    if not ops:
        print("No players to insert.")
        return

    result = collection.bulk_write(ops, ordered=False)
    print(
        f"Seeded {len(players)} players → "
        f"inserted: {result.upserted_count}, "
        f"updated: {result.modified_count}"
    )
    client.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not F40_FILE.is_file():
        print(f"ERROR: F40 file not found at {F40_FILE}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing F40: {F40_FILE}")
    players = parse_players(F40_FILE)
    print(f"Found {len(players)} players across all teams")

    # Print a quick sample
    if players:
        s = players[0]
        print(
            f"  Sample → {s['name']} | {s.get('position')} | "
            f"{s.get('nationality')} | h={s.get('height')} w={s.get('weight')} "
            f"foot={s.get('preferredFoot')} | club={s.get('club')}"
        )

    print(f"\nConnecting to {MONGODB_URL}")
    seed(players, MONGODB_URL, MONGODB_DATABASE)
    print("Done.")
