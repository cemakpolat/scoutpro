"""
seed_all_opta.py

Seeds MongoDB from all available Opta feed files:
  F1  → competitions, teams, matches (306 matches with real scores/dates)
  F9  → updates the match document with lineup, half-time stats, bookings
  F40 → players (upsert; skips players already seeded by seed_players_from_f40.py)
  F24 → re-labels existing events: replaces numeric type_names with English names

Run inside the mongo container or with direct network access:
  docker cp scripts/seed_all_opta.py scoutpro-mongo:/tmp/
  docker exec -it scoutpro-mongo python3 /tmp/seed_all_opta.py

Or outside Docker (if MONGODB_URL is reachable):
  MONGODB_URL="mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin" \
  DATA_ROOT=/path/to/data python3 scripts/seed_all_opta.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("seed_all_opta")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MONGODB_URL = os.environ.get(
    "MONGODB_URL",
    "mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin",
)
DB_NAME = os.environ.get("MONGODB_DATABASE", "scoutpro")

# Resolve DATA_ROOT: env var > script-relative heuristic
_script_dir = Path(__file__).resolve().parent
DATA_ROOT = Path(os.environ.get("DATA_ROOT", str(_script_dir.parent / "data")))
OPTA_ROOT = DATA_ROOT / "opta" / "2019"

COMPETITION_ID = 115
SEASON_ID      = 2019

# ---------------------------------------------------------------------------
# Opta F24 type_id → human name (mirrors parser.py OPTA_F24_TYPE_MAP)
# ---------------------------------------------------------------------------
OPTA_F24_TYPE_MAP: Dict[int, str] = {
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> Dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        log.error(f"Cannot load {path}: {exc}")
        return {}


def _int(val) -> Optional[int]:
    try:
        return int(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _find_feed(name: str) -> Optional[Path]:
    """Search OPTA_ROOT and DATA_ROOT/opta for a feed file."""
    stems = [
        f"{name}_{COMPETITION_ID}_{SEASON_ID}",
        f"{name}_{SEASON_ID}_{COMPETITION_ID}",
    ]
    search = [OPTA_ROOT, DATA_ROOT / "opta"]
    for d in search:
        for stem in stems:
            p = d / stem
            if p.is_file():
                return p
    return None


# ---------------------------------------------------------------------------
# F1 – season schedule
# ---------------------------------------------------------------------------

def _parse_f1_goals(td: Dict[str, Any], team_ref: str, side: str) -> List[Dict[str, Any]]:
    raw = td.get("Goal", [])
    if isinstance(raw, dict):
        raw = [raw]
    goals = []
    for g in raw:
        ga = g.get("@attributes", {})
        goal = {
            "player_ref": ga.get("PlayerRef", "").lstrip("p"),
            "period":     ga.get("Period"),
            "type":       ga.get("Type"),
            "min":        _int(ga.get("Min")),
            "sec":        _int(ga.get("Sec")),
            "team_id":    team_ref,
            "side":       side,
        }
        if "Assist" in g:
            a = g["Assist"].get("@attributes", {})
            goal["assist"] = {"player_ref": a.get("PlayerRef", "").lstrip("p")}
        goals.append(goal)
    return goals


def seed_f1(db: Any) -> Dict[str, int]:
    """Seed competitions, teams, and matches from F1."""
    path = _find_feed("f1")
    if not path:
        log.warning(f"F1 feed not found in {OPTA_ROOT}")
        return {"competitions": 0, "teams": 0, "matches": 0}

    log.info(f"Loading F1 from {path}")
    raw = _load_json(path)
    doc = raw.get("SoccerFeed", {}).get("SoccerDocument", raw)

    # --- Competition ---
    comp_raw = doc.get("Competition", {})
    comp_uid = comp_raw.get("@attributes", {}).get("uID", f"c{COMPETITION_ID}")
    comp_stats: Dict[str, Any] = {}
    for s in (comp_raw.get("Stat") or []):
        if isinstance(s, dict):
            comp_stats[s.get("@attributes", {}).get("Type", "x")] = s.get("@value")

    competition_doc = {
        "uID":      comp_uid,
        "name":     comp_raw.get("Name", "Unknown"),
        "country":  comp_raw.get("Country"),
        "season_id":   comp_stats.get("season_id"),
        "season_name": comp_stats.get("season_name"),
        "symid":       comp_stats.get("symid"),
        "provider":    "opta",
        "updatedAt":   _now(),
    }
    result_comp = db.competitions.update_one(
        {"uID": comp_uid},
        {"$set": competition_doc},
        upsert=True,
    )
    log.info(f"Competitions: upserted uID={comp_uid}")

    # --- Teams ---
    raw_teams = doc.get("Team", [])
    if isinstance(raw_teams, dict):
        raw_teams = [raw_teams]
    team_ops = []
    team_map: Dict[str, str] = {}  # uID (no prefix) → name
    for t in raw_teams:
        uid = t.get("@attributes", {}).get("uID", "").lstrip("t")
        name = t.get("Name", "")
        team_map[uid] = name
        team_ops.append(UpdateOne(
            {"uID": uid},
            {"$set": {
                "uID":      uid,
                "name":     name,
                "provider": "opta",
                "providerMappings": {"opta": f"t{uid}"},
                "updatedAt": _now(),
            }},
            upsert=True,
        ))
    n_teams = 0
    if team_ops:
        r = db.teams.bulk_write(team_ops, ordered=False)
        n_teams = r.upserted_count + r.modified_count
        log.info(f"Teams: {r.upserted_count} inserted, {r.modified_count} updated ({len(raw_teams)} total)")

    # --- Matches ---
    raw_matches = doc.get("MatchData", [])
    if isinstance(raw_matches, dict):
        raw_matches = [raw_matches]

    match_ops = []
    for m in raw_matches:
        attrs = m.get("@attributes", {})
        uid = attrs.get("uID", "").lstrip("g")

        mi = m.get("MatchInfo", {})
        mi_attrs = mi.get("@attributes", {})

        home_team_id = away_team_id = None
        home_score = away_score = home_ht = away_ht = None
        goals: List[Dict[str, Any]] = []

        raw_td = m.get("TeamData", [])
        if isinstance(raw_td, dict):
            raw_td = [raw_td]
        for td in raw_td:
            ta = td.get("@attributes", {})
            team_ref = ta.get("TeamRef", "").lstrip("t")
            side = ta.get("Side", "").lower()
            if side == "home":
                home_team_id = team_ref
                home_score = _int(ta.get("Score"))
                home_ht = _int(ta.get("HalfScore"))
            elif side == "away":
                away_team_id = team_ref
                away_score = _int(ta.get("Score"))
                away_ht = _int(ta.get("HalfScore"))
            goals.extend(_parse_f1_goals(td, team_ref, side))

        # Referee
        referee = None
        raw_off = m.get("MatchOfficials", {})
        if raw_off:
            off_list = raw_off.get("MatchOfficial", [])
            if isinstance(off_list, dict):
                off_list = [off_list]
            for off in off_list:
                oa = off.get("@attributes", {})
                if oa.get("Type", "").lower() in ("referee", "main"):
                    referee = {
                        "uID":   oa.get("uID"),
                        "first": oa.get("FirstName"),
                        "last":  oa.get("LastName"),
                    }
                    break

        period = mi_attrs.get("Period", "")
        status = "finished" if period == "FullTime" else ("scheduled" if not period else "live")
        match_winner = mi_attrs.get("MatchWinner", "").lstrip("t") or None

        match_doc = {
            "uID":           uid,
            "date":          mi.get("Date"),
            "tz":            mi.get("TZ"),
            "matchDay":      _int(mi_attrs.get("MatchDay")),
            "matchType":     mi_attrs.get("MatchType"),
            "period":        period,
            "status":        status,
            "venueID":       mi_attrs.get("Venue_id"),
            "matchWinner":   match_winner,
            "homeTeamID":    home_team_id,
            "awayTeamID":    away_team_id,
            "homeScore":     home_score,
            "awayScore":     away_score,
            "homeHTScore":   home_ht,
            "awayHTScore":   away_ht,
            "homeTeamName":  team_map.get(home_team_id),
            "awayTeamName":  team_map.get(away_team_id),
            "goals":         goals,
            "referee":       referee,
            "competitionID": comp_uid,
            "seasonID":      str(SEASON_ID),
            "provider":      "opta",
            "lastModified":  attrs.get("last_modified"),
            "updatedAt":     _now(),
        }
        match_ops.append(UpdateOne(
            {"uID": uid},
            {"$set": match_doc},
            upsert=True,
        ))

    n_matches = 0
    if match_ops:
        r = db.matches.bulk_write(match_ops, ordered=False)
        n_matches = r.upserted_count + r.modified_count
        log.info(f"Matches: {r.upserted_count} inserted, {r.modified_count} updated ({len(raw_matches)} total)")

    return {"competitions": 1, "teams": n_teams, "matches": n_matches}


# ---------------------------------------------------------------------------
# F9 – match summary / lineups
# ---------------------------------------------------------------------------

def seed_f9(db: Any) -> Dict[str, int]:
    """Enrich the relevant match document with F9 lineup and stats data."""
    path = _find_feed("f9")
    if not path:
        log.warning(f"F9 feed not found in {OPTA_ROOT}")
        return {"matches_updated": 0}

    log.info(f"Loading F9 from {path}")
    raw = _load_json(path)
    doc = raw.get("SoccerFeed", {}).get("SoccerDocument", raw)

    doc_attrs = doc.get("@attributes", {})
    # F9 doc uID is like "f1081234"; strip leading 'f'
    match_uid = doc_attrs.get("uID", "").lstrip("f")

    mdata = doc.get("MatchData", {})

    # Competition info (also upsert)
    comp_raw = doc.get("Competition", {})
    comp_uid = comp_raw.get("@attributes", {}).get("uID", f"c{COMPETITION_ID}")
    comp_stats: Dict[str, Any] = {}
    for s in (comp_raw.get("Stat") or []):
        if isinstance(s, dict):
            comp_stats[s.get("@attributes", {}).get("Type", "x")] = s.get("@value")
    db.competitions.update_one(
        {"uID": comp_uid},
        {"$set": {
            "uID":      comp_uid,
            "name":     comp_raw.get("Name"),
            "country":  comp_raw.get("Country"),
            "season_id":   comp_stats.get("season_id"),
            "season_name": comp_stats.get("season_name"),
            "provider":    "opta",
            "updatedAt":   _now(),
        }},
        upsert=True,
    )

    # Match-level stats
    raw_stats = mdata.get("Stat", [])
    if isinstance(raw_stats, dict):
        raw_stats = [raw_stats]
    stats: Dict[str, Any] = {}
    for s in raw_stats:
        stats[s.get("@attributes", {}).get("Type", "x")] = s.get("@value")

    # Referee
    raw_ref = mdata.get("MatchOfficial", {})
    referee = None
    if raw_ref:
        on = raw_ref.get("OfficialName", {})
        referee = {
            "uID":   raw_ref.get("@attributes", {}).get("uID"),
            "first": on.get("First"),
            "last":  on.get("Last"),
        }

    # Assistant officials
    asst_officials = []
    raw_asst = mdata.get("AssistantOfficials", {}).get("AssistantOfficial", [])
    if isinstance(raw_asst, dict):
        raw_asst = [raw_asst]
    for ao in raw_asst:
        a = ao.get("@attributes", {})
        asst_officials.append({
            "uID": a.get("uID"), "first": a.get("FirstName"),
            "last": a.get("LastName"), "type": a.get("Type"),
        })

    # TeamData: scores, lineup, goals, bookings, subs, stats
    raw_td_list = mdata.get("TeamData", [])
    if isinstance(raw_td_list, dict):
        raw_td_list = [raw_td_list]

    teams_summary = []
    for td in raw_td_list:
        ta = td.get("@attributes", {})
        team_ref = ta.get("TeamRef", "").lstrip("t")
        side = ta.get("Side", "").lower()

        # Goals
        raw_goals = td.get("Goal", [])
        if isinstance(raw_goals, dict):
            raw_goals = [raw_goals]
        goals = []
        for g in raw_goals:
            ga = g.get("@attributes", {})
            goal = {
                "player_ref": ga.get("PlayerRef", "").lstrip("p"),
                "period": ga.get("Period"),
                "type": ga.get("Type"),
                "min": _int(ga.get("Min")),
                "sec": _int(ga.get("Sec")),
                "event_id": ga.get("EventID"),
            }
            if "Assist" in g:
                a = g["Assist"].get("@attributes", {})
                goal["assist"] = {"player_ref": a.get("PlayerRef", "").lstrip("p")}
            goals.append(goal)

        # Bookings
        bookings = []
        raw_bk = td.get("Booking", [])
        if isinstance(raw_bk, dict):
            raw_bk = [raw_bk]
        for bk in raw_bk:
            ba = bk.get("@attributes", {})
            bookings.append({
                "player_ref": ba.get("PlayerRef", "").lstrip("p"),
                "card": ba.get("Card"), "card_type": ba.get("CardType"),
                "reason": ba.get("Reason"), "period": ba.get("Period"),
                "min": _int(ba.get("Min")), "sec": _int(ba.get("Sec")),
            })

        # Substitutions
        subs = []
        raw_subs = td.get("Substitution", [])
        if isinstance(raw_subs, dict):
            raw_subs = [raw_subs]
        for sub in raw_subs:
            sa = sub.get("@attributes", {})
            subs.append({
                "sub_on": sa.get("SubOn", "").lstrip("p"),
                "sub_off": sa.get("SubOff", "").lstrip("p"),
                "period": sa.get("Period"),
                "min": _int(sa.get("Min")), "sec": _int(sa.get("Sec")),
                "reason": sa.get("Reason"),
            })

        # Lineup
        lineup = []
        raw_lineup = td.get("PlayerLineUp", {})
        if raw_lineup:
            raw_players = raw_lineup.get("MatchPlayer", [])
            if isinstance(raw_players, dict):
                raw_players = [raw_players]
            for mp in raw_players:
                mpa = mp.get("@attributes", {})
                pstats: Dict[str, Any] = {}
                raw_ps = mp.get("Stat", [])
                if isinstance(raw_ps, dict):
                    raw_ps = [raw_ps]
                for ps in raw_ps:
                    pstats[ps.get("@attributes", {}).get("Type", "?")] = ps.get("@value")
                lineup.append({
                    "player_ref":   mpa.get("PlayerRef", "").lstrip("p"),
                    "position":     mpa.get("Position"),
                    "shirt_number": _int(mpa.get("ShirtNumber")),
                    "status":       mpa.get("Status"),  # "Start" or "Sub"
                    "is_captain":   mpa.get("Captain") == "True",
                    "stats":        pstats,
                })

        # Team-level match stats
        team_stats = []
        raw_ts = td.get("Stat", [])
        if isinstance(raw_ts, dict):
            raw_ts = [raw_ts]
        for ts in raw_ts:
            tsa = ts.get("@attributes", {})
            team_stats.append({
                "type": tsa.get("Type"), "value": ts.get("@value"),
                "fh": tsa.get("FH"), "sh": tsa.get("SH"),
            })

        teams_summary.append({
            "team_ref":      team_ref,
            "side":          side,
            "score":         _int(ta.get("Score")),
            "half_score":    _int(ta.get("HalfScore")),
            "goals":         goals,
            "bookings":      bookings,
            "substitutions": subs,
            "lineup":        lineup,
            "team_stats":    team_stats,
        })

    # Find the match this F9 belongs to. F9 doc uID like "f1081234" doesn't
    # directly match a match uID (those come from F1 g-prefixed UIDs).
    # Try to match by looking at team refs + competition.
    home_ref = next((t["team_ref"] for t in teams_summary if t["side"] == "home"), None)
    away_ref = next((t["team_ref"] for t in teams_summary if t["side"] == "away"), None)
    home_score = next((t["score"] for t in teams_summary if t["side"] == "home"), None)
    away_score = next((t["score"] for t in teams_summary if t["side"] == "away"), None)

    # Find existing match by team IDs
    query: Dict[str, Any] = {}
    if home_ref and away_ref:
        query = {"homeTeamID": home_ref, "awayTeamID": away_ref}
    elif match_uid:
        query = {"uID": match_uid}

    update_payload = {
        "f9_match_uid":       match_uid,
        "f9_summary":         teams_summary,
        "f9_stats":           stats,
        "f9_referee":         referee,
        "f9_asst_officials":  asst_officials,
        "f9_period":          mdata.get("MatchInfo", {}).get("@attributes", {}).get("Period"),
        "f9_updated":         _now(),
    }
    # If F9 provides reliable scores, update them
    if home_score is not None:
        update_payload["homeScore"] = home_score
    if away_score is not None:
        update_payload["awayScore"] = away_score

    result = db.matches.update_one(query, {"$set": update_payload})
    n = result.modified_count
    if n:
        log.info(f"F9: updated match {query} with lineup+stats (home {home_ref} {home_score}:{away_score} {away_ref})")
    else:
        # Insert standalone summary document if match not found in matches collection
        update_payload.update({
            "uID":        match_uid,
            "homeTeamID": home_ref,
            "awayTeamID": away_ref,
            "homeScore":  home_score,
            "awayScore":  away_score,
            "provider":   "opta",
            "updatedAt":  _now(),
        })
        db.matches.update_one({"uID": match_uid}, {"$set": update_payload}, upsert=True)
        log.info(f"F9: inserted standalone match record uID={match_uid}")
        n = 1

    return {"matches_updated": n}


# ---------------------------------------------------------------------------
# F40 – squad lists (players)
# ---------------------------------------------------------------------------

def seed_f40(db: Any) -> Dict[str, int]:
    """Upsert players from F40 squad feed."""
    path = _find_feed("f40")
    if not path:
        log.warning(f"F40 feed not found in {OPTA_ROOT}")
        return {"inserted": 0, "updated": 0}

    log.info(f"Loading F40 from {path}")
    raw = _load_json(path)
    doc = raw.get("SoccerFeed", {}).get("SoccerDocument", raw)

    raw_teams = doc.get("Team", [])
    if isinstance(raw_teams, dict):
        raw_teams = [raw_teams]

    ops = []
    for t in raw_teams:
        ta = t.get("@attributes", {})
        team_uid = ta.get("uID", "").lstrip("t")
        team_name = t.get("Name", "")

        raw_players = t.get("Player", [])
        if isinstance(raw_players, dict):
            raw_players = [raw_players]

        for p in raw_players:
            pa = p.get("@attributes", {})
            player_uid = pa.get("uID", "")

            # Name fields
            pn = p.get("PersonName", p.get("Name", {}))
            if isinstance(pn, str):
                name = pn; first = last = known = None
            else:
                first = pn.get("First") or pn.get("first")
                last  = pn.get("Last")  or pn.get("last")
                known = pn.get("Known") or pn.get("known")
                name  = p.get("Name") or known or f"{first or ''} {last or ''}".strip()

            # Stats
            raw_stats = p.get("Stat", [])
            if isinstance(raw_stats, dict):
                raw_stats = [raw_stats]
            pstats: Dict[str, Any] = {}
            for s in raw_stats:
                pstats[s.get("@attributes", {}).get("Type", "?")] = s.get("@value")

            def _pstat(key: str):
                return pstats.get(key) or pstats.get(key.capitalize()) or pstats.get(key.lower())

            height = _int(_pstat("height"))
            weight = _int(_pstat("weight"))

            player_doc = {
                "uID":          player_uid,
                "name":         name,
                "first":        first,
                "last":         last,
                "known":        known,
                "position":     pa.get("Position"),
                "nationality":  _pstat("nationality"),
                "birthDate":    _pstat("birth_date") or _pstat("birthdate"),
                "height":       height,
                "weight":       weight,
                "preferredFoot": _pstat("preferred_foot") or _pstat("preferredFoot"),
                "shirtNumber":  _int(_pstat("shirt_number") or _pstat("shirtNumber")),
                "realPosition": _pstat("real_position") or _pstat("realPosition"),
                "status":       pa.get("Status"),
                "teamID":       team_uid,
                "teamName":     team_name,
                "club":         team_name,
                "provider":     "opta",
                "updatedAt":    _now(),
            }

            ops.append(UpdateOne(
                {"uID": player_uid},
                {"$set": player_doc},
                upsert=True,
            ))

    inserted = updated = 0
    if ops:
        r = db.players.bulk_write(ops, ordered=False)
        inserted = r.upserted_count
        updated  = r.modified_count
        log.info(f"F40 players: {inserted} inserted, {updated} updated ({len(ops)} total)")

    return {"inserted": inserted, "updated": updated}


# ---------------------------------------------------------------------------
# F24 – re-label numeric type_names with English names
# ---------------------------------------------------------------------------

def relabel_f24_events(db: Any) -> Dict[str, int]:
    """
    For every match_event document where type_name is a stringified integer,
    replace it with the human-readable name from OPTA_F24_TYPE_MAP.
    """
    log.info("Scanning match_events for numeric type_names …")
    ops = []
    for doc in db.match_events.find({"type_name": {"$type": "string"}}):
        tn = doc.get("type_name", "")
        if not tn or not tn.lstrip("-").isdigit():
            continue
        type_id = int(tn)
        new_name = OPTA_F24_TYPE_MAP.get(type_id, f"type_{type_id}")
        ops.append(UpdateOne(
            {"_id": doc["_id"]},
            {"$set": {"type_name": new_name, "type_id": type_id}},
        ))

    # Also fix documents where type_name is stored as a number (not string)
    for doc in db.match_events.find({"type_name": {"$type": "int"}}):
        type_id = doc.get("type_name")
        if type_id is None:
            continue
        new_name = OPTA_F24_TYPE_MAP.get(type_id, f"type_{type_id}")
        ops.append(UpdateOne(
            {"_id": doc["_id"]},
            {"$set": {"type_name": new_name, "type_id": type_id}},
        ))

    updated = 0
    if ops:
        r = db.match_events.bulk_write(ops, ordered=False)
        updated = r.modified_count
        log.info(f"F24 events: relabelled {updated} documents")
    else:
        log.info("F24 events: no numeric type_names found")

    return {"relabelled": updated}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log.info(f"Connecting to {MONGODB_URL.split('@')[-1]} …")
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]

    # Verify connection
    try:
        client.admin.command("ping")
        log.info("MongoDB connection OK")
    except Exception as exc:
        log.error(f"Cannot connect to MongoDB: {exc}")
        sys.exit(1)

    log.info(f"DATA_ROOT = {DATA_ROOT}")
    log.info(f"OPTA_ROOT = {OPTA_ROOT}")

    results: Dict[str, Any] = {}

    log.info("=" * 60)
    log.info("Phase 1 – F1 (season schedule: matches, teams, competition)")
    log.info("=" * 60)
    results["f1"] = seed_f1(db)

    log.info("=" * 60)
    log.info("Phase 2 – F9 (match summary: lineups, half-time stats)")
    log.info("=" * 60)
    results["f9"] = seed_f9(db)

    log.info("=" * 60)
    log.info("Phase 3 – F40 (squad lists: players)")
    log.info("=" * 60)
    results["f40"] = seed_f40(db)

    log.info("=" * 60)
    log.info("Phase 4 – F24 (relabel numeric event type_names)")
    log.info("=" * 60)
    results["f24"] = relabel_f24_events(db)

    log.info("=" * 60)
    log.info("Summary:")
    for feed, r in results.items():
        log.info(f"  {feed}: {r}")
    log.info("=" * 60)
    client.close()


if __name__ == "__main__":
    main()
