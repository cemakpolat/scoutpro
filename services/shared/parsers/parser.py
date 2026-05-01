"""
Parser — New Architecture

Replaces the legacy src.restapi / src.events / src.utils parser chain.
Reads Opta JSON feed files from disk and normalises them into plain dicts
that the rest of the system (repositories, Kafka producers) can consume.

Supported feeds
---------------
f1   – Season schedule
f9   – Match lineups & summary stats
f24  – Event-by-event data  (primary feed)
f40  – Squad lists
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Canonical feed-name shortcuts
FEED_NAME_MAP: Dict[str, str] = {
    "feed40": "f40", "f40": "f40",
    "feed1":  "f1",  "f1":  "f1",
    "feed9":  "f9",  "f9":  "f9",
    "feed24": "f24", "f24": "f24",
}

DATA_ROOT = os.environ.get(
    "DATA_ROOT",
    os.path.join(os.path.dirname(__file__), "../../../../data"),
)


class Feeds:
    """Feed-name constants kept for backward compatibility."""
    f1  = "f1";  f9  = "f9";  f24 = "f24"; f40 = "f40"
    feed1  = "feed1";  feed9  = "feed9"
    feed24 = "feed24"; feed40 = "feed40"


# Opta F24 numeric type_id → human-readable event name
# Source: Opta F24 event type documentation
OPTA_F24_TYPE_MAP: Dict[int, str] = {
    1:  "pass",
    2:  "offside_pass",
    3:  "take_on",
    4:  "foul",
    5:  "out",
    6:  "corner_awarded",
    7:  "tackle",
    8:  "interception",
    9:  "turnover",
    10: "save",
    11: "claim",
    12: "clearance",
    13: "miss",
    14: "post",
    15: "attempt_saved",
    16: "goal",
    17: "card",
    18: "player_off",
    19: "player_on",
    20: "player_changed_position",
    21: "player_retired",
    22: "player_returns",
    23: "player_becomes_goalkeeper",
    24: "goalkeeper_becomes_player",
    25: "condition_change",
    27: "start_delay",
    28: "end_delay",
    30: "end",
    32: "start_period",
    34: "end_period",
    35: "stop_page_play",
    37: "resume",
    38: "temp_goal",
    40: "goal_confirmed",
    41: "ball_recovery",
    43: "blocked_pass",
    44: "pre_match",
    45: "formation",
    48: "punch",
    49: "good_skill",
    50: "deleted_event",
    51: "fifty_fifty",
    52: "failed_to_block",
    53: "pre_match_pass",
    54: "aerial_lost",
    55: "challenge",
    56: "ball_touch",
    57: "error",
    58: "dispossessed",
    59: "fifty_fifty",
    60: "keeper_pickup",
    61: "chance_missed",
    63: "keeper_saves",
    64: "possession",
    65: "good_skill",
    67: "blocked_pass",
    68: "attempt_blocked",
    70: "goalkeeper_save",
    71: "good_skill",
    73: "block",
    74: "blocked_shot",
    75: "dribble",
    76: "error",
    77: "keeper_sweeper",
}


class Parser:
    """Static helpers for locating and loading Opta feed files."""

    Feeds = Feeds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def parseFeed(
        feed_name: str,
        competition_id: int,
        season_id: int,
        game_id: Optional[int] = None,
        online: bool = False,
    ) -> Dict[str, Any]:
        """
        Load an Opta feed.

        When *online* is False (default) the feed is read from the local
        data directory.  Live / API access is handled by the
        live-ingestion-service and is out of scope here.
        """
        if online:
            logger.warning(
                "Online feed fetch requested but not implemented in the new "
                "architecture — use live-ingestion-service instead."
            )
            return {}

        return Parser._load_local(feed_name, competition_id, season_id, game_id)

    # ------------------------------------------------------------------
    # F24 helpers (events)
    # ------------------------------------------------------------------

    @staticmethod
    def extract_events(raw_feed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten Opta F24 JSON into a list of normalised event dicts.

        The Opta JSON wraps everything like:
          { "Games": { "Game": { "@attributes": {...}, "Event": [...] } } }

        Each event dict will have at minimum:
          id, type_id, period_id, min, sec, player_id, team_id,
          outcome, x, y, timestamp + qualifiers list
        """
        game_node = (
            raw_feed.get("Games", {})
                    .get("Game", raw_feed.get("Game", {}))
        )

        game_attrs = game_node.get("@attributes", {})
        raw_events = game_node.get("Event", [])

        # Opta sometimes returns a single event as a dict, not a list
        if isinstance(raw_events, dict):
            raw_events = [raw_events]

        events: List[Dict[str, Any]] = []
        for raw_ev in raw_events:
            attrs = raw_ev.get("@attributes", raw_ev)
            type_id = _int(attrs.get("type_id"))
            event: Dict[str, Any] = {
                "id":         attrs.get("id"),
                "event_id":   attrs.get("event_id", attrs.get("id")),
                "type_id":    type_id,
                "type_name":  OPTA_F24_TYPE_MAP.get(type_id, f"type_{type_id}") if type_id is not None else None,
                "period_id":  _int(attrs.get("period_id")),
                "min":        _int(attrs.get("min")),
                "sec":        _int(attrs.get("sec")),
                "player_id":  attrs.get("player_id"),
                "team_id":    attrs.get("team_id"),
                "outcome":    _int(attrs.get("outcome")),
                "x":          _float(attrs.get("x")),
                "y":          _float(attrs.get("y")),
                "timestamp":  attrs.get("timestamp"),
                "game_id":    game_attrs.get("id"),
                "competition_id": game_attrs.get("competition_id"),
                "season_id":  game_attrs.get("season_id"),
                "qualifiers": Parser._parse_qualifiers(raw_ev.get("Q", [])),
            }
            events.append(event)

        return events

    @staticmethod
    def extract_game_meta(raw_feed: Dict[str, Any]) -> Dict[str, Any]:
        """Return the top-level game attributes from an F24 / F9 feed."""
        game_node = (
            raw_feed.get("Games", {})
                    .get("Game", raw_feed.get("Game", {}))
        )
        return game_node.get("@attributes", {})

    # ------------------------------------------------------------------
    # F1 helpers (season schedule)
    # ------------------------------------------------------------------

    @staticmethod
    def extract_schedule(raw_feed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Opta F1 (season schedule) feed.

        Returns a dict with:
          competition: {uID, name, country}
          teams: [{uID, name}]
          matches: [{uID, date, tz, match_day, match_type, period, venue_id,
                     match_winner, home_team_id, away_team_id,
                     home_score, away_score, home_ht_score, away_ht_score,
                     goals: [{player_ref, period, type, min, sec, assist}],
                     referee: {first, last, uID}}]
        """
        doc = (
            raw_feed.get("SoccerFeed", {})
                    .get("SoccerDocument", raw_feed)
        )

        # --- Competition ---
        comp_raw = doc.get("Competition", {})
        competition: Dict[str, Any] = {
            "uID":     comp_raw.get("@attributes", {}).get("uID"),
            "name":    comp_raw.get("Name"),
            "country": comp_raw.get("Country"),
        }
        for s in (comp_raw.get("Stat") or []):
            if isinstance(s, dict):
                competition[s.get("@attributes", {}).get("Type", "unknown")] = s.get("@value")

        # --- Teams ---
        raw_teams = doc.get("Team", [])
        if isinstance(raw_teams, dict):
            raw_teams = [raw_teams]
        teams = [
            {"uID": t.get("@attributes", {}).get("uID"), "name": t.get("Name")}
            for t in raw_teams
        ]

        # --- Matches ---
        raw_matches = doc.get("MatchData", [])
        if isinstance(raw_matches, dict):
            raw_matches = [raw_matches]

        matches: List[Dict[str, Any]] = []
        for m in raw_matches:
            attrs = m.get("@attributes", {})
            uid = attrs.get("uID", "").lstrip("g")

            mi = m.get("MatchInfo", {})
            mi_attrs = mi.get("@attributes", {})

            # Parse team data (home/away scores)
            home_team_id = away_team_id = None
            home_score = away_score = None
            home_ht = away_ht = None
            goals: List[Dict[str, Any]] = []

            raw_td = m.get("TeamData", [])
            if isinstance(raw_td, dict):
                raw_td = [raw_td]

            for td in raw_td:
                ta = td.get("@attributes", {})
                team_ref = ta.get("TeamRef", "").lstrip("t")
                side = ta.get("Side", "").lower()
                score = _int(ta.get("Score"))
                ht = _int(ta.get("HalfScore"))

                if side == "home":
                    home_team_id = team_ref
                    home_score = score
                    home_ht = ht
                elif side == "away":
                    away_team_id = team_ref
                    away_score = score
                    away_ht = ht

                # Goals
                raw_goals = td.get("Goal", [])
                if isinstance(raw_goals, dict):
                    raw_goals = [raw_goals]
                for g in raw_goals:
                    ga = g.get("@attributes", {})
                    goal: Dict[str, Any] = {
                        "player_ref": ga.get("PlayerRef", "").lstrip("p"),
                        "period":     ga.get("Period"),
                        "type":       ga.get("Type"),
                        "min":        _int(ga.get("Min")),
                        "sec":        _int(ga.get("Sec")),
                        "team_id":    team_ref,
                        "side":       side,
                    }
                    if "Assist" in g:
                        assist_attrs = g["Assist"].get("@attributes", {})
                        goal["assist"] = {
                            "player_ref": assist_attrs.get("PlayerRef", "").lstrip("p"),
                        }
                    goals.append(goal)

            # Referee
            referee: Optional[Dict[str, Any]] = None
            raw_off = m.get("MatchOfficials", {})
            if raw_off:
                off_list = raw_off.get("MatchOfficial", [])
                if isinstance(off_list, dict):
                    off_list = [off_list]
                for off in off_list:
                    if off.get("@attributes", {}).get("Type", "").lower() == "referee":
                        referee = {
                            "uID":   off.get("@attributes", {}).get("uID"),
                            "first": off.get("@attributes", {}).get("FirstName"),
                            "last":  off.get("@attributes", {}).get("LastName"),
                        }
                        break

            match: Dict[str, Any] = {
                "uID":           uid,
                "date":          mi.get("Date"),
                "tz":            mi.get("TZ"),
                "match_day":     _int(mi_attrs.get("MatchDay")),
                "match_type":    mi_attrs.get("MatchType"),
                "period":        mi_attrs.get("Period"),
                "venue_id":      mi_attrs.get("Venue_id"),
                "match_winner":  mi_attrs.get("MatchWinner", "").lstrip("t") or None,
                "home_team_id":  home_team_id,
                "away_team_id":  away_team_id,
                "home_score":    home_score,
                "away_score":    away_score,
                "home_ht_score": home_ht,
                "away_ht_score": away_ht,
                "goals":         goals,
                "referee":       referee,
                "last_modified": attrs.get("last_modified"),
            }
            matches.append(match)

        return {"competition": competition, "teams": teams, "matches": matches}

    # ------------------------------------------------------------------
    # F9 helpers (match summary / lineups)
    # ------------------------------------------------------------------

    @staticmethod
    def extract_match_summary(raw_feed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Opta F9 (match summary) feed.

        Returns a dict with:
          match_id: str (from doc uID, e.g. "f1081234" → stripped to "1081234")
          competition: {uID, name, country, season_id, season_name, match_day}
          match_info: {period, match_type, timestamp, additional_info}
          match_time: int (current match minute)
          stats: {type: value}  (match-level stats)
          referee: {uID, first, last}
          assistant_officials: [{uID, first, last, type}]
          teams: [{team_ref, side, score, half_score,
                   goals: [...], bookings: [...], substitutions: [...],
                   lineup: [{player_ref, position, shirt_number, status,
                             is_captain, stats: {type: value}}],
                   team_stats: [{type, value, fh, sh}]}]
        """
        doc = (
            raw_feed.get("SoccerFeed", {})
                    .get("SoccerDocument", raw_feed)
        )

        doc_attrs = doc.get("@attributes", {})
        match_id = doc_attrs.get("uID", "").lstrip("f")

        # --- Competition ---
        comp_raw = doc.get("Competition", {})
        competition: Dict[str, Any] = {
            "uID":     comp_raw.get("@attributes", {}).get("uID"),
            "name":    comp_raw.get("Name"),
            "country": comp_raw.get("Country"),
        }
        for s in (comp_raw.get("Stat") or []):
            if isinstance(s, dict):
                competition[s.get("@attributes", {}).get("Type", "unknown")] = s.get("@value")

        mdata = doc.get("MatchData", {})
        mi = mdata.get("MatchInfo", {})
        mi_attrs = mi.get("@attributes", {})

        match_info = {
            "period":          mi_attrs.get("Period"),
            "match_type":      mi_attrs.get("MatchType"),
            "timestamp":       mi_attrs.get("TimeStamp"),
            "additional_info": mi_attrs.get("AdditionalInfo"),
            "date":            mi.get("Date"),
        }

        # Match-level stats (match_time, first_half_start, etc.)
        raw_stats = mdata.get("Stat", [])
        if isinstance(raw_stats, dict):
            raw_stats = [raw_stats]
        stats: Dict[str, Any] = {}
        for s in raw_stats:
            stats[s.get("@attributes", {}).get("Type", "unknown")] = s.get("@value")

        # --- Referee ---
        referee: Optional[Dict[str, Any]] = None
        raw_ref = mdata.get("MatchOfficial", {})
        if raw_ref:
            on = raw_ref.get("OfficialName", {})
            referee = {
                "uID":   raw_ref.get("@attributes", {}).get("uID"),
                "first": on.get("First"),
                "last":  on.get("Last"),
            }

        # --- Assistant Officials ---
        asst_officials: List[Dict[str, Any]] = []
        raw_asst = mdata.get("AssistantOfficials", {}).get("AssistantOfficial", [])
        if isinstance(raw_asst, dict):
            raw_asst = [raw_asst]
        for ao in raw_asst:
            a = ao.get("@attributes", {})
            asst_officials.append({
                "uID":   a.get("uID"),
                "first": a.get("FirstName"),
                "last":  a.get("LastName"),
                "type":  a.get("Type"),
            })

        # --- TeamData ---
        raw_td_list = mdata.get("TeamData", [])
        if isinstance(raw_td_list, dict):
            raw_td_list = [raw_td_list]

        teams: List[Dict[str, Any]] = []
        for td in raw_td_list:
            ta = td.get("@attributes", {})
            team_ref = ta.get("TeamRef", "").lstrip("t")
            side = ta.get("Side", "").lower()

            # Goals
            goals = Parser._parse_f9_goals(td.get("Goal", []))

            # Bookings
            bookings: List[Dict[str, Any]] = []
            raw_bk = td.get("Booking", [])
            if isinstance(raw_bk, dict):
                raw_bk = [raw_bk]
            for bk in raw_bk:
                ba = bk.get("@attributes", {})
                bookings.append({
                    "player_ref": ba.get("PlayerRef", "").lstrip("p"),
                    "card":       ba.get("Card"),
                    "card_type":  ba.get("CardType"),
                    "reason":     ba.get("Reason"),
                    "period":     ba.get("Period"),
                    "min":        _int(ba.get("Min")),
                    "sec":        _int(ba.get("Sec")),
                    "event_id":   ba.get("EventID"),
                })

            # Substitutions
            substitutions: List[Dict[str, Any]] = []
            raw_subs = td.get("Substitution", [])
            if isinstance(raw_subs, dict):
                raw_subs = [raw_subs]
            for sub in raw_subs:
                sa = sub.get("@attributes", {})
                substitutions.append({
                    "sub_on":    sa.get("SubOn", "").lstrip("p"),
                    "sub_off":   sa.get("SubOff", "").lstrip("p"),
                    "period":    sa.get("Period"),
                    "min":       _int(sa.get("Min")),
                    "sec":       _int(sa.get("Sec")),
                    "reason":    sa.get("Reason"),
                    "event_id":  sa.get("EventID"),
                })

            # Lineup
            lineup: List[Dict[str, Any]] = []
            raw_lineup = td.get("PlayerLineUp", {})
            if raw_lineup:
                raw_players = raw_lineup.get("MatchPlayer", [])
                if isinstance(raw_players, dict):
                    raw_players = [raw_players]
                for mp in raw_players:
                    mpa = mp.get("@attributes", {})
                    player_stats: Dict[str, Any] = {}
                    raw_pstats = mp.get("Stat", [])
                    if isinstance(raw_pstats, dict):
                        raw_pstats = [raw_pstats]
                    for ps in raw_pstats:
                        player_stats[ps.get("@attributes", {}).get("Type", "?")] = ps.get("@value")
                    lineup.append({
                        "player_ref":   mpa.get("PlayerRef", "").lstrip("p"),
                        "position":     mpa.get("Position"),
                        "shirt_number": _int(mpa.get("ShirtNumber")),
                        "status":       mpa.get("Status"),
                        "is_captain":   mpa.get("Captain") == "True",
                        "stats":        player_stats,
                    })

            # Team-level stats
            team_stats: List[Dict[str, Any]] = []
            raw_ts = td.get("Stat", [])
            if isinstance(raw_ts, dict):
                raw_ts = [raw_ts]
            for ts in raw_ts:
                tsa = ts.get("@attributes", {})
                team_stats.append({
                    "type":  tsa.get("Type"),
                    "value": ts.get("@value"),
                    "fh":    tsa.get("FH"),
                    "sh":    tsa.get("SH"),
                })

            teams.append({
                "team_ref":     team_ref,
                "side":         side,
                "score":        _int(ta.get("Score")),
                "half_score":   _int(ta.get("HalfScore")),
                "goals":        goals,
                "bookings":     bookings,
                "substitutions": substitutions,
                "lineup":       lineup,
                "team_stats":   team_stats,
            })

        return {
            "match_id":           match_id,
            "competition":        competition,
            "match_info":         match_info,
            "stats":              stats,
            "referee":            referee,
            "assistant_officials": asst_officials,
            "teams":              teams,
        }

    @staticmethod
    def _parse_f9_goals(raw_goals) -> List[Dict[str, Any]]:
        if isinstance(raw_goals, dict):
            raw_goals = [raw_goals]
        goals: List[Dict[str, Any]] = []
        for g in raw_goals:
            ga = g.get("@attributes", {})
            goal: Dict[str, Any] = {
                "player_ref": ga.get("PlayerRef", "").lstrip("p"),
                "period":     ga.get("Period"),
                "type":       ga.get("Type"),
                "min":        _int(ga.get("Min")),
                "sec":        _int(ga.get("Sec")),
                "event_id":   ga.get("EventID"),
            }
            if "Assist" in g:
                assist_attrs = g["Assist"].get("@attributes", g["Assist"])
                goal["assist"] = {
                    "player_ref": assist_attrs.get("PlayerRef", "").lstrip("p"),
                    "event_id":   assist_attrs.get("EventID"),
                }
            goals.append(goal)
        return goals

    # ------------------------------------------------------------------
    # F40 helpers (squad lists)
    # ------------------------------------------------------------------

    @staticmethod
    def extract_squads(raw_feed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Opta F40 (squad list) feed.

        Returns a dict with:
          teams: [{uID, name, country, manager,
                   players: [{uID, name, first, last, known,
                              position, nationality, birth_date,
                              height, weight, preferred_foot,
                              shirt_number, real_position, status}]}]
        """
        doc = (
            raw_feed.get("SoccerFeed", {})
                    .get("SoccerDocument", raw_feed)
        )

        raw_teams = doc.get("Team", [])
        if isinstance(raw_teams, dict):
            raw_teams = [raw_teams]

        teams: List[Dict[str, Any]] = []
        for t in raw_teams:
            ta = t.get("@attributes", {})
            team_uid = ta.get("uID", "").lstrip("t")

            # Manager
            manager: Optional[str] = None
            raw_off = t.get("TeamOfficial", {})
            if isinstance(raw_off, list):
                raw_off = raw_off[0] if raw_off else {}
            if raw_off:
                pn = raw_off.get("PersonName", {})
                manager = f"{pn.get('First', '')} {pn.get('Last', '')}".strip() or None

            # Players
            raw_players = t.get("Player", [])
            if isinstance(raw_players, dict):
                raw_players = [raw_players]

            players: List[Dict[str, Any]] = []
            for p in raw_players:
                pa = p.get("@attributes", {})
                pn = p.get("PersonName", p.get("Name", {}))
                if isinstance(pn, str):
                    name_str = pn
                    first = last = known = None
                else:
                    first = pn.get("First") or pn.get("first")
                    last = pn.get("Last") or pn.get("last")
                    known = pn.get("Known") or pn.get("known")
                    name_str = known or f"{first or ''} {last or ''}".strip()

                # Stats (height, weight, preferredFoot, birthDate, etc.)
                raw_stats_list = p.get("Stat", [])
                if isinstance(raw_stats_list, dict):
                    raw_stats_list = [raw_stats_list]
                pstats: Dict[str, Any] = {}
                for s in raw_stats_list:
                    pstats[s.get("@attributes", {}).get("Type", "?")] = s.get("@value")

                players.append({
                    "uID":           pa.get("uID", "").lstrip("p"),
                    "name":          p.get("Name") or name_str,
                    "first":         first,
                    "last":          last,
                    "known":         known,
                    "position":      pa.get("Position"),
                    "nationality":   pstats.get("nationality") or pstats.get("Nationality"),
                    "birth_date":    pstats.get("birth_date") or pstats.get("BirthDate"),
                    "height":        _int(pstats.get("height") or pstats.get("Height")),
                    "weight":        _int(pstats.get("weight") or pstats.get("Weight")),
                    "preferred_foot": pstats.get("preferred_foot") or pstats.get("PreferredFoot") or pstats.get("preferredFoot"),
                    "shirt_number":  _int(pstats.get("shirt_number") or pstats.get("ShirtNumber")),
                    "real_position": pstats.get("real_position") or pstats.get("RealPosition"),
                    "status":        pa.get("Status"),
                })

            teams.append({
                "uID":     team_uid,
                "name":    t.get("Name"),
                "country": t.get("Country"),
                "manager": manager,
                "players": players,
            })

        return {"teams": teams}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_local(
        feed_name: str,
        competition_id: int,
        season_id: int,
        game_id: Optional[int],
    ) -> Dict[str, Any]:
        short = FEED_NAME_MAP.get(feed_name, feed_name)

        base   = f"{short}_{competition_id}_{season_id}"
        base_r = f"{short}_{season_id}_{competition_id}"

        stems = (
            [f"{base}_{game_id}", f"{base_r}_{game_id}"]
            if game_id is not None
            else [base, base_r]
        )

        opta_root = os.path.join(DATA_ROOT, "opta")
        search_dirs = [
            opta_root,
            os.path.join(opta_root, str(season_id)),
            os.path.join(opta_root, str(competition_id), str(season_id)),
            os.path.join(opta_root, str(season_id), str(competition_id)),
        ]

        for directory in search_dirs:
            for stem in stems:
                candidate = os.path.join(directory, stem)
                if os.path.isfile(candidate):
                    logger.debug(f"Loading feed from {candidate}")
                    return _load_json(candidate)

        logger.warning(
            f"Feed not found: {feed_name} comp={competition_id} "
            f"season={season_id} game={game_id}"
        )
        return {}

    @staticmethod
    def _parse_qualifiers(raw_q) -> List[Dict[str, Any]]:
        if isinstance(raw_q, dict):
            raw_q = [raw_q]
        qualifiers = []
        for q in (raw_q or []):
            a = q.get("@attributes", q)
            qualifiers.append({
                "qualifier_id": _int(a.get("qualifier_id")),
                "value":        a.get("value"),
            })
        return qualifiers


# ------------------------------------------------------------------
# Module-level convenience functions (used by Connector.getFeed callers)
# ------------------------------------------------------------------

def getFeed(
    feed_name: str,
    competition_id: int,
    season_id: int,
    game_id: Optional[int] = None,
) -> Dict[str, Any]:
    return Parser.parseFeed(feed_name, competition_id, season_id, game_id)


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _int(val) -> Optional[int]:
    try:
        return int(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _float(val) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _load_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, IOError) as exc:
        logger.error(f"Failed to load {path}: {exc}")
        return {}
