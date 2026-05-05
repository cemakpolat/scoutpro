"""
Event Statistics Pipeline
=========================
This module bridges the gap between the MongoDB ``match_events`` collection and
the shared event-processing classes in ``services/shared/events/``.

Flow:
  1. Load raw F24 events for one or more matches from ``match_events``.
  2. Wrap each MongoDB document in ``F24EventAdapter`` so it presents the
     attribute-based interface expected by the shared classes (PassEvent,
     ShotandGoalEvents, TouchEvents, etc.).
  3. For every (player, match) pair, call all relevant event handlers and
     collect the rich, field-level statistics they compute.
  4. Resolve ScoutPro IDs for players and teams via the ``players`` / ``teams``
     collections.
  5. Upsert the resulting documents into ``player_statistics`` and
     ``team_statistics``, keyed by **ScoutPro ID** so front-end pages that use
     the canonical ScoutPro ID can find them directly.

The pipeline is designed to be:
  - Called once during an initial seed / migration run.
  - Triggered per-match when a new match's events arrive.
  - Run on a periodic schedule (e.g. daily) by the APScheduler job in main.py.
"""
from __future__ import annotations

import logging
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pymongo import MongoClient, UpdateOne

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type-name → Opta typeID reverse-mapping
# (from services/shared/events/Events.py EventTypes dict)
# ---------------------------------------------------------------------------
_TYPE_NAME_TO_ID: Dict[str, int] = {
    "pass": 1,
    "offside pass": 2,
    "take on": 3,
    "foul": 4,
    "out": 5,
    "corner awarded": 6,
    "tackle": 7,
    "interception": 8,
    "turnover": 9,
    "save": 10,
    "claim": 11,
    "clearance": 12,
    "miss": 13,
    "post": 14,
    "attempt saved": 15,
    "attempt_saved": 15,
    "goal": 16,
    "card": 17,
    "player off": 18,
    "player on": 19,
    "player retired": 20,
    "player returns": 21,
    "player becomes goalkeeper": 22,
    "goalkeeper becomes player": 23,
    "condition change": 24,
    "official change": 25,
    "start delay": 27,
    "end delay": 28,
    "end": 30,
    "start": 32,
    "team set up": 34,
    "player changed position": 35,
    "player changed jersey number": 36,
    "collection end": 37,
    "temp_goal": 38,
    "temp_attempt": 39,
    "formation change": 40,
    "punch": 41,
    "good skill": 42,
    "deleted event": 43,
    "deleted_event": 43,
    "aerial": 44,
    "aerial_lost": 44,
    "challenge": 45,
    "rescinded card": 47,
    "ball recovery": 49,
    "ball_recovery": 49,
    "dispossessed": 50,
    "error": 51,
    "keeper pick-up": 52,
    "cross not claimed": 53,
    "smother": 54,
    "offside provoked": 55,
    "shield ball opp": 56,
    "foul throw-in": 57,
    "penalty faced": 58,
    "keeper sweeper": 59,
    "chance missed": 60,
    "chance_missed": 60,
    "ball touch": 61,
    "ball_touch": 61,
    "temp_save": 63,
    "resume": 64,
    "contentious referee decision": 65,
    "possession data": 66,
    "50/50": 67,
    "referee drop ball": 68,
    "failed to block": 69,
    "failed_to_block": 69,
    "injury time announcement": 70,
    "coach setup": 71,
    "caught offside": 72,
    "other ball contact": 73,
    "blocked pass": 74,
    "blocked_pass": 74,
    "delayed start": 75,
    "early end": 76,
    "player off pitch": 77,
    "coverage interruption": 79,
    "assist": 80,
    "cross": 1,           # crosses are typeID 1 pass events with qualifier 2
    "offside_pass": 2,
    "corner": 6,
    "corner_awarded": 6,
    "shot": 13,           # treat generic "shot" as a miss
    "blocked_shot": 74,
    "block": 74,
    "dribble": 3,
    "dribbled past": 50,
    "collected": 11,
    "end_delay": 28,
    "end_period": 30,
    "carries": 61,
    "ball receipt*": 61,
    "50/50": 67,
    "aerial won": 44,
}

# Card qualifier value → type
_CARD_QUALIFIER_VALUES = {
    "yellow": "yellow",
    "yellow card": "yellow",
    "second yellow": "yellow",
    "red": "red",
    "red card": "red",
    "straight red": "red",
}


# ---------------------------------------------------------------------------
# F24EventAdapter – wraps a MongoDB event dict as an attribute object
# ---------------------------------------------------------------------------

class _QEvent:
    """Minimal qualifier wrapper used by the shared event classes."""

    __slots__ = ("qualifierID", "value")

    def __init__(self, qualifier_id: int, value: str) -> None:
        self.qualifierID = qualifier_id
        self.value = value


class F24EventAdapter:
    """Presents a MongoDB match_events document as an object whose attribute
    names match the F24 event structure expected by the shared event classes.
    """

    __slots__ = (
        "typeID", "playerID", "teamID", "x", "y", "outcome",
        "qEvents", "matchID", "minute", "period", "_raw",
        # EventMinutes-compatible aliases
        "min", "sec", "periodID",
    )

    def __init__(self, doc: Dict[str, Any]) -> None:
        self._raw = doc
        type_name = str(doc.get("type_name") or "").lower().strip()
        self.typeID: int = _TYPE_NAME_TO_ID.get(type_name, 0)

        # Player / team IDs — coerce to int where possible
        pid = doc.get("player_id") or doc.get("playerID") or 0
        tid = doc.get("team_id") or doc.get("teamID") or 0
        try:
            self.playerID = int(pid)
        except (ValueError, TypeError):
            self.playerID = 0
        try:
            self.teamID = int(tid)
        except (ValueError, TypeError):
            self.teamID = 0

        loc = doc.get("location") or {}
        self.x: float = float(loc.get("x") or doc.get("x") or 0)
        self.y: float = float(loc.get("y") or doc.get("y") or 0)
        self.outcome: int = int(doc.get("outcome") or (1 if doc.get("is_successful") else 0))
        self.matchID: str = str(doc.get("matchID") or doc.get("match_id") or "")
        self.minute: int = int(doc.get("minute") or doc.get("min") or 0)
        self.period: int = int(doc.get("period") or 1)
        # EventMinutes aliases
        self.min: int = self.minute
        self.sec: int = int(doc.get("sec") or 0)
        self.periodID: int = self.period

        # Build qEvents list
        raw_qs = doc.get("qualifiers") or []
        self.qEvents: List[_QEvent] = []
        for q in raw_qs:
            if isinstance(q, dict):
                qid = q.get("qualifier_id") or q.get("qualifierID") or 0
                val = str(q.get("value") or "")
                self.qEvents.append(_QEvent(int(qid), val))


# ---------------------------------------------------------------------------
# Stats extraction helpers (use shared event classes)
# ---------------------------------------------------------------------------

def _extract_pass_stats(events: List[F24EventAdapter], player_id: int, team_id: int) -> Dict[str, Any]:
    """Run PassEvent handler and return a flat stats dict."""
    import sys
    sys.path.insert(0, "/app")
    try:
        from shared.events.PassEvent import PassEvent
        handler = PassEvent()
        handler.callEventHandler({
            "teamID": [team_id],
            "playerID": [player_id],
            "events": events,
        }, print_results=False)
        return {
            "passes_total": handler.passes_total,
            "passes_successful": handler.passes_successful,
            "passes_unsuccessful": handler.passes_unsuccessful,
            "forward_passes": handler.forward_passes,
            "backward_passes": handler.backward_passes,
            "sideway_passes": handler.sideway_passes,
            "total_crosses": handler.total_crosses,
            "successful_crosses": handler.successful_crosses,
            "long_passes": handler.long_passes,
            "successful_long_passes": handler.successful_long_passes,
            "through_ball": handler.through_ball,
            "through_ball_successful": handler.through_ball_successful,
            "total_corners": handler.total_corners,
            "pass_success_rate": handler.pass_success_rate,
            "blocked_passes": handler.blocked_passes,
            "total_free_kicks_taken": handler.total_free_kicks_taken,
            "average_pass_length": handler.average_pass_length,
        }
    except Exception as exc:
        logger.debug("PassEvent handler failed: %s", exc)
        return {}


def _extract_shot_stats(events: List[F24EventAdapter], player_id: int, team_id: int) -> Dict[str, Any]:
    """Run ShotandGoalEvents handler."""
    try:
        from shared.events.ShotandGoalEvents import ShotandGoalEvents
        handler = ShotandGoalEvents()
        handler.callEventHandler({
            "teamID": [team_id],
            "playerID": [player_id],
            "events": events,
        }, print_results=False)
        return {
            "goals": handler.goals,
            "total_shots": handler.total_shots,
            "shots_on_target": getattr(handler, 'shots_on_target', 0),
            "shots_inside_box": handler.shots_inside_box,
            "shots_outside_box": handler.shots_outside_box,
            "goals_inside_the_box": handler.goals_inside_the_box,
            "goals_outside_the_box": handler.goals_outside_the_box,
            "headed_goals": handler.headed_goals,
            "goals_from_set_play": handler.goals_from_set_play,
            "goals_from_open_play": handler.goals_from_open_play,
            "goals_from_penalties": handler.goals_from_penalties,
            "blocked_shot": handler.blocked_shot,
            "non_penalty_goals": handler.non_penalty_goals,
        }
    except Exception as exc:
        logger.debug("ShotandGoalEvents handler failed: %s", exc)
        return {}


def _extract_touch_stats(events: List[F24EventAdapter], player_id: int, team_id: int) -> Dict[str, Any]:
    """Run TouchEvents handler."""
    try:
        from shared.events.TouchEvents import TouchEvents
        handler = TouchEvents()
        handler.callEventHandler({
            "teamID": [team_id],
            "playerID": [player_id],
            "events": events,
        }, print_results=False)
        return {
            "total_touches": handler.total_touches,
            "total_touches_in_attacking_third": handler.total_touches_in_attacking_third,
            "total_touches_in_middle_third": handler.total_touches_in_middle_third,
            "total_touches_in_defensive_third": handler.total_touches_in_defensive_third,
            "total_touches_in_box": handler.total_touches_in_box,
            "turnover": handler.turnover,
            "turnover_percentage": handler.turnover_percentage,
            "total_tackles": handler.total_tackles,
            "total_successful_tackles": handler.total_successful_tackles,
            "tackle_attempts": handler.tackle_attempts,
            "tackle_made_percentage": handler.tackle_made_percentage,
            "tackle_success_percentage": handler.tackle_success_percentage,
            "total_tackles_in_attacking_third": handler.total_tackles_in_attacking_third,
            "total_tackles_in_middle_third": handler.total_tackles_in_middle_third,
            "total_tackles_in_defensive_third": handler.total_tackles_in_defensive_third,
            "last_man_tackles": handler.last_man_tackles,
            "total_ball_recovery": handler.total_ball_recovery,
            "total_recoveries_in_defensive_third": handler.total_recoveries_in_defensive_third,
            "total_recoveries_in_middle_third": handler.total_recoveries_in_middle_third,
            "total_recoveries_in_attacking_third": handler.total_recoveries_in_attacking_third,
            "total_interceptions": handler.total_interceptions,
            "total_interceptions_in_defensive_third": handler.total_interceptions_in_defensive_third,
            "total_interceptions_in_middle_third": handler.total_interceptions_in_middle_third,
            "total_interceptions_in_attacking_third": handler.total_interceptions_in_attacking_third,
            "total_clearances": handler.total_clearances,
            "total_clearances_in_defensive_third": handler.total_clearances_in_defensive_third,
        }
    except Exception as exc:
        logger.debug("TouchEvents handler failed: %s", exc)
        return {}


def _extract_aerial_stats(events: List[F24EventAdapter], player_id: int, team_id: int) -> Dict[str, Any]:
    """Run AerialDuelEvents handler."""
    try:
        from shared.events.AerialDuelEvents import AerialDuelEvents
        handler = AerialDuelEvents()
        handler.callEventHandler({
            "teamID": [team_id],
            "playerID": [player_id],
            "events": events,
        }, print_results=False)
        return {
            "total_aerial_duels": handler.total_aerial_duels,
            "aerial_duels_won": handler.successful_aerial_duels,
            "aerial_duels_lost": handler.unsuccessful_aerial_duels,
            "aerial_duel_success_rate": handler.aerial_duel_success_rate,
            "aerial_duels_in_attacking_half": handler.aerial_duels_in_attacking_half,
            "aerial_duels_in_defending_half": handler.aerial_duels_in_defending_half,
            "aerial_duels_in_attacking_third": handler.aerial_duels_in_attacking_third,
            "aerial_duels_in_middle_third": handler.aerial_duels_in_middle_third,
            "aerial_duels_in_defending_third": handler.aerial_duels_in_defending_third,
        }
    except Exception as exc:
        logger.debug("AerialDuelEvents handler failed: %s", exc)
        return {}


def _extract_foul_stats(events: List[F24EventAdapter], player_id: int, team_id: int) -> Dict[str, Any]:
    """Run FoulEvents handler."""
    try:
        from shared.events.FoulEvents import FoulEvents
        handler = FoulEvents()
        handler.callEventHandler({
            "teamID": [team_id],
            "playerID": [player_id],
            "events": events,
        }, print_results=False)
        return {
            "fouls_committed": handler.fouls_conceded,
            "fouls_won": handler.fouls_won,
            "handball_conceded": handler.handball_conceded,
            "penalty_conceded": handler.penalty_conceded,
            "penalty_won": handler.penalty_won,
            "fouls_won_in_defending_third": handler.fouls_won_in_defending_third,
            "fouls_won_in_middle_third": handler.fouls_won_in_middle_third,
            "fouls_won_in_attacking_third": handler.fouls_won_in_attacking_third,
            "fouls_committed_in_defending_third": handler.fouls_committed_in_defending_third,
            "fouls_committed_in_middle_third": handler.fouls_committed_in_middle_third,
            "fouls_committed_in_attacking_third": handler.fouls_committed_in_attacking_third,
        }
    except Exception as exc:
        logger.debug("FoulEvents handler failed: %s", exc)
        return {}


def _extract_card_stats(events: List[F24EventAdapter], player_id: int, team_id: int) -> Dict[str, Any]:
    """Run CardEvents handler."""
    try:
        from shared.events.CardEvents import CardEvents
        handler = CardEvents()
        handler.callEventHandler({
            "teamID": [team_id],
            "playerID": [player_id],
            "events": events,
        }, print_results=False)
        return {
            "yellow_cards": handler.yellow_card,
            "second_yellow_cards": handler.second_yellow_card,
            "red_cards": handler.red_card,
            "card_rescinded": handler.card_rescinded,
            "total_cards": handler.total_cards,
        }
    except Exception as exc:
        logger.debug("CardEvents handler failed: %s", exc)
        return {}


def _extract_takeon_stats(events: List[F24EventAdapter], player_id: int, team_id: int) -> Dict[str, Any]:
    """Run TakeOnEvents handler."""
    try:
        from shared.events.TakeOnEvents import TakeOnEvents
        handler = TakeOnEvents()
        handler.callEventHandler({
            "teamID": [team_id],
            "playerID": [player_id],
            "events": events,
        }, print_results=False)
        return {
            "total_take_ons": handler.total_take_ons,
            "successful_take_ons": handler.take_ons_successful,
            "unsuccessful_take_ons": handler.take_ons_unsuccessful,
            "take_on_success_rate": handler.take_on_success_rate,
            "take_on_overrun": handler.take_on_overrun,
            "take_ons_in_attacking_third": handler.take_on_in_attacking_third,
            "take_ons_in_box": handler.take_ons_in_box,
            "successful_take_ons_in_box": handler.successful_take_ons_in_box,
            "times_tackled": handler.tackled,
        }
    except Exception as exc:
        logger.debug("TakeOnEvents handler failed: %s", exc)
        return {}


def _extract_duel_stats(events: List[F24EventAdapter], player_id: int, team_id: int) -> Dict[str, Any]:
    """Run DuelEvents handler (ground duels by thirds)."""
    try:
        from shared.events.DuelEvents import DuelEvents
        handler = DuelEvents()
        handler.callEventHandler({
            "teamID": [team_id],
            "playerID": [player_id],
            "events": events,
        }, print_results=False)
        return {
            "total_duels": handler.total_duels,
            "successful_duels": handler.successful_duels,
            "unsuccessful_duels": handler.unsuccessful_duels,
            "defensive_duels": handler.defensive_duels,
            "offensive_duels": handler.offensive_duels,
            "total_ground_duels": handler.total_ground_duels,
            "successful_ground_duels": handler.successful_ground_duels,
            "unsuccessful_ground_duels": handler.unsuccessful_ground_duels,
            "duel_success_rate": handler.duel_success_rate,
            "duels_in_attacking_third": handler.duels_in_attacking_third,
            "duels_in_middle_third": handler.duels_in_middle_third,
            "duels_in_defending_third": handler.duels_in_defending_third,
        }
    except Exception as exc:
        logger.debug("DuelEvents handler failed: %s", exc)
        return {}


def _extract_ball_control_stats(events: List[F24EventAdapter], player_id: int, team_id: int) -> Dict[str, Any]:
    """Run BallControlEvents handler (dispossessed, errors, offsides, ball touches)."""
    try:
        from shared.events.BallControlEvents import BallControlEvents
        handler = BallControlEvents()
        handler.callEventHandler({
            "teamID": [team_id],
            "playerID": [player_id],
            "events": events,
        }, print_results=False)
        return {
            "total_dispossessed": handler.total_dispossessed,
            "total_errors": handler.errors,
            "errors_led_to_goal": handler.error_led_to_goal,
            "errors_led_to_shot": handler.error_led_to_shot,
            "caught_offside": handler.caught_offside,
            "ball_touches": handler.ball_touch,
        }
    except Exception as exc:
        logger.debug("BallControlEvents handler failed: %s", exc)
        return {}


def _extract_assist_stats(events: List[F24EventAdapter], player_id: int, team_id: int,
                          total_minutes: int = 0) -> Dict[str, Any]:
    """Run AssistEvents handler (assists, key passes, chances created).
    Requires total_minutes for minutes_per_chance calculation.
    """
    try:
        from shared.events.AssistEvents import AssistEvents
        handler = AssistEvents()
        handler.callEventHandler({
            "teamID": [team_id],
            "playerID": [player_id],
            "events": events,
            "total_minutes": total_minutes,
        }, print_results=False)
        return {
            "total_assists": handler.total_assists,
            "intentional_assists": handler.intentional_assists,
            "assists_from_open_play": handler.assists_from_open_play,
            "assists_from_set_play": handler.assists_from_set_play,
            "assists_from_free_kick": handler.assists_from_free_kick,
            "assists_from_corners": handler.assists_from_corners,
            "assists_from_throw_in": handler.assists_from_throw_in,
            "assists_from_goal_kick": handler.assists_from_goal_kick,
            "key_passes": handler.key_passes,
            "key_passes_after_dribble": handler.key_passes_after_dribble,
            "key_pass_corner": handler.key_pass_corner,
            "key_pass_free_kick": handler.key_pass_free_kick,
            "assist_and_key_passes": handler.assist_and_key_passes,
            "chances_created_from_open_play": handler.chances_created_from_open_play,
            "chances_created_from_set_play": handler.chances_created_from_set_play,
            "minutes_per_chance": handler.minutes_per_chance,
            "open_play_assist_rate": handler.open_play_assist_rate,
        }
    except Exception as exc:
        logger.debug("AssistEvents handler failed: %s", exc)
        return {}


def _extract_goalkeeper_stats(events: List[F24EventAdapter], player_id: int, team_id: int) -> Dict[str, Any]:
    """Run GoalkeeperEvents handler (saves, crosses, penalties faced, GK distributions)."""
    try:
        from shared.events.GoalkeeperEvents import GoalkeeperEvents
        handler = GoalkeeperEvents()
        handler.callEventHandler({
            "teamID": [team_id],
            "playerID": [player_id],
            "events": events,
        }, print_results=False)
        return {
            "saves": handler.saves,
            "save_percentage": handler.save_percentage,
            "save_1on1": handler.save_1on1,
            "goals_against": handler.goals_against,
            "clean_sheet": handler.clean_sheet,
            "gk_sweeper": handler.gk_sweeper,
            "accurate_keeper_sweeper": handler.accurate_keeper_sweeper,
            "crosses_faced": handler.crosses_faced,
            "crosses_claimed": handler.crosses_claimed,
            "crosses_punched": handler.crosses_punched,
            "crosses_not_claimed": handler.crosses_not_claimed,
            "gk_pick_ups": handler.gk_pick_ups,
            "goal_kicks": handler.goal_kicks,
            "successful_goal_kicks": handler.successful_goal_kicks,
            "gk_throws": handler.gk_throws,
            "successful_gk_throws": handler.successful_gk_throws,
            "gk_smother": handler.gk_smother,
            "penalty_faced": handler.penalty_faced,
            "penalties_saved": handler.penalties_saved,
            "penalties_scored": handler.penalties_scored,
            "penalties_missed": handler.penalties_missed,
            "shots_against": handler.shots_against,
            "shots_on_target_against": handler.shots_on_target_against,
            "team_own_goals": handler.team_own_goals,
            "saves_from_own_player": handler.saves_from_own_player,
            # Save types
            "save_body": handler.save_body,
            "save_caught": handler.save_caught,
            "save_diving": handler.save_diving,
            "save_feet": handler.save_feet,
            "save_hands": handler.save_hands,
            "save_penalty": handler.save_penalty,
            "save_inside_box": handler.save_inside_box,
            "save_outside_box": handler.save_outside_box,
        }
    except Exception as exc:
        logger.debug("GoalkeeperEvents handler failed: %s", exc)
        return {}


def _extract_games_minutes(events: List[F24EventAdapter], player_id: int, team_id: int) -> Dict[str, Any]:
    """Run GamesandMinutesEvents handler.
    Note: saveResults() only stores substitute_on/substitute_off in event_results,
    so we read the handler attributes directly.
    """
    try:
        from shared.events.GamesandMinutesEvents import GamesandMinutesEvents
        handler = GamesandMinutesEvents()
        handler.callEventHandler({
            "teamID": team_id,
            "playerID": player_id,
            "events": events,
        }, print_results=False)
        return {
            "minutes_played": handler.actual_minutes_on_field or handler.total_minutes,
            "games_played": handler.games_played,
            "games_started": handler.games_started,
            "substitute_on": handler.substitute_on,
            "substitute_off": handler.substitute_off,
            "minutes_per_game": handler.minutes_per_game,
        }
    except Exception as exc:
        logger.debug("GamesandMinutesEvents handler failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# Main pipeline class
# ---------------------------------------------------------------------------

class EventStatsPipeline:
    """Uses shared event classes to compute rich statistics from match_events.

    Stores results in ``player_statistics`` and ``team_statistics`` keyed by
    both Opta player_id AND scoutpro_player_id (as string) so both front-end
    ID schemes work.
    """

    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        db_name: str = "scoutpro",
    ) -> None:
        uri = mongo_uri or os.getenv(
            "MONGODB_URL",
            "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin",
        )
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]

    def close(self) -> None:
        self.client.close()

    # ------------------------------------------------------------------
    # ID resolution helpers (sync, pymongo)
    # ------------------------------------------------------------------

    def _resolve_scoutpro_player_id(self, opta_player_id: str) -> Optional[str]:
        """Look up ScoutPro canonical ID for a given Opta player ID."""
        try:
            doc = self.db.players.find_one(
                {"$or": [
                    {"provider_ids.opta": {"$in": [opta_player_id, f"p{opta_player_id}"]}},
                    {"uID": {"$in": [opta_player_id, f"p{opta_player_id}"]}},
                ]},
                {"scoutpro_id": 1, "id": 1}
            )
            if doc:
                sp_id = doc.get("scoutpro_id") or doc.get("id")
                if sp_id is not None:
                    return str(sp_id)
        except Exception as exc:
            logger.debug("_resolve_scoutpro_player_id(%s) failed: %s", opta_player_id, exc)
        return None

    def _resolve_scoutpro_team_id(self, opta_team_id: str) -> Optional[str]:
        """Look up ScoutPro canonical ID for a given Opta team ID."""
        try:
            doc = self.db.teams.find_one(
                {"$or": [
                    {"provider_ids.opta": {"$in": [opta_team_id, f"t{opta_team_id}"]}},
                    {"uID": {"$in": [opta_team_id, f"t{opta_team_id}"]}},
                ]},
                {"scoutpro_id": 1, "id": 1, "name": 1}
            )
            if doc:
                sp_id = doc.get("scoutpro_id") or doc.get("id")
                if sp_id is not None:
                    return str(sp_id)
        except Exception as exc:
            logger.debug("_resolve_scoutpro_team_id(%s) failed: %s", opta_team_id, exc)
        return None

    # ------------------------------------------------------------------
    # Per-player computation using shared event classes
    # ------------------------------------------------------------------

    def _compute_player_stats(
        self,
        events: List[F24EventAdapter],
        player_id: int,
        team_id: int,
    ) -> Dict[str, Any]:
        """Call all shared event handlers for one player-match.

        Execution order matters: GamesandMinutes first so total_minutes is
        available for AssistEvents (minutes_per_chance calculation).
        """
        stats: Dict[str, Any] = {"total_events": len(events)}

        # 1. Playing time (needed for AssistEvents minutes_per_chance)
        games_stats = _extract_games_minutes(events, player_id, team_id)
        stats.update(games_stats)
        total_minutes = games_stats.get("minutes_played", 0) or 0

        # 2. Attacking
        stats.update(_extract_shot_stats(events, player_id, team_id))
        stats.update(_extract_assist_stats(events, player_id, team_id, total_minutes))

        # 3. Passing
        stats.update(_extract_pass_stats(events, player_id, team_id))

        # 4. Defensive / physical
        stats.update(_extract_touch_stats(events, player_id, team_id))
        stats.update(_extract_aerial_stats(events, player_id, team_id))
        stats.update(_extract_duel_stats(events, player_id, team_id))
        stats.update(_extract_takeon_stats(events, player_id, team_id))

        # 5. Discipline
        stats.update(_extract_foul_stats(events, player_id, team_id))
        stats.update(_extract_card_stats(events, player_id, team_id))

        # 6. Ball control / errors
        stats.update(_extract_ball_control_stats(events, player_id, team_id))

        # 7. Goalkeeper (only contributes when the player has GK events)
        stats.update(_extract_goalkeeper_stats(events, player_id, team_id))

        return stats

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def run(
        self,
        match_id: Optional[str] = None,
        competition_id: Optional[str] = None,
        season_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """Process match events → compute stats → upsert into statistics collections.

        Args:
            match_id:       Limit to a single match (optional).
            competition_id: Limit to a competition (optional).
            season_id:      Limit to a season (optional).
        Returns:
            Counts of player/team docs written.
        """
        base_query: Dict[str, Any] = {}
        if competition_id:
            base_query["competition_id"] = competition_id
        if season_id:
            base_query["season_id"] = season_id

        if match_id:
            match_ids = [match_id]
        else:
            match_ids = self.db.match_events.distinct("matchID", base_query)

        if not match_ids:
            logger.warning("EventStatsPipeline: no match IDs found for %s", base_query)
            return {"player_docs": 0, "team_docs": 0}

        total_player = 0
        total_team = 0

        # Cache ScoutPro ID lookups within a run to reduce DB round-trips
        player_sp_cache: Dict[str, Optional[str]] = {}
        team_sp_cache: Dict[str, Optional[str]] = {}

        for mid in match_ids:
            query = dict(base_query)
            query["matchID"] = mid
            raw_events = list(self.db.match_events.find(query))
            if not raw_events:
                continue

            # Convert all docs to F24EventAdapter
            adapted = [F24EventAdapter(ev) for ev in raw_events]

            # Group by (player_id, team_id)
            player_buckets: Dict[Tuple[int, int], List[F24EventAdapter]] = defaultdict(list)
            team_buckets: Dict[int, List[F24EventAdapter]] = defaultdict(list)

            meta: Dict[int, Dict[str, Any]] = {}  # player_id → meta fields

            for ev_obj, ev_raw in zip(adapted, raw_events):
                if ev_obj.playerID:
                    player_buckets[(ev_obj.playerID, ev_obj.teamID)].append(ev_obj)
                    if ev_obj.playerID not in meta:
                        meta[ev_obj.playerID] = {
                            "competition_id": ev_raw.get("competition_id"),
                            "season_id": ev_raw.get("season_id"),
                            "match_id": str(mid),
                        }
                if ev_obj.teamID:
                    team_buckets[ev_obj.teamID].append(ev_obj)

            # ── Player statistics ──────────────────────────────────────────
            player_ops = []
            now = datetime.now(timezone.utc).isoformat()

            for (pid, tid), ev_list in player_buckets.items():
                stats = self._compute_player_stats(ev_list, pid, tid)
                opta_pid = str(pid)
                opta_tid = str(tid)

                if opta_pid not in player_sp_cache:
                    player_sp_cache[opta_pid] = self._resolve_scoutpro_player_id(opta_pid)
                if opta_tid not in team_sp_cache:
                    team_sp_cache[opta_tid] = self._resolve_scoutpro_team_id(opta_tid)

                sp_player_id = player_sp_cache[opta_pid]
                sp_team_id = team_sp_cache[opta_tid]

                doc = {
                    "player_id": opta_pid,
                    "team_id": opta_tid,
                    "match_id": str(mid),
                    "scoutpro_player_id": sp_player_id,
                    "scoutpro_team_id": sp_team_id,
                    "updated_at": now,
                    **meta.get(pid, {}),
                    **stats,
                }

                # Upsert: key on (player_id, match_id) — same as BatchAggregator
                filter_q = {"player_id": opta_pid, "match_id": str(mid)}
                # Also index by scoutpro_player_id for direct lookup
                if sp_player_id:
                    filter_q = {
                        "$or": [
                            {"player_id": opta_pid, "match_id": str(mid)},
                            {"scoutpro_player_id": sp_player_id, "match_id": str(mid)},
                        ]
                    }

                player_ops.append(UpdateOne(
                    {"player_id": opta_pid, "match_id": str(mid)},
                    {"$set": doc},
                    upsert=True,
                ))

            if player_ops:
                result = self.db.player_statistics.bulk_write(player_ops, ordered=False)
                total_player += (result.upserted_count or 0) + (result.modified_count or 0)

            # ── Team statistics ────────────────────────────────────────────
            team_ops = []
            for tid, ev_list in team_buckets.items():
                opta_tid = str(tid)
                if opta_tid not in team_sp_cache:
                    team_sp_cache[opta_tid] = self._resolve_scoutpro_team_id(opta_tid)
                sp_team_id = team_sp_cache[opta_tid]

                # Aggregate basic team counters from the adapted events
                t_stats = self._aggregate_team_counters(ev_list)
                raw_sample = next(
                    (e for e in raw_events if str(e.get("team_id") or "") == opta_tid), {}
                )
                doc = {
                    "team_id": opta_tid,
                    "match_id": str(mid),
                    "scoutpro_team_id": sp_team_id,
                    "competition_id": raw_sample.get("competition_id"),
                    "season_id": raw_sample.get("season_id"),
                    "updated_at": now,
                    **t_stats,
                }
                team_ops.append(UpdateOne(
                    {"team_id": opta_tid, "match_id": str(mid)},
                    {"$set": doc},
                    upsert=True,
                ))

            if team_ops:
                result = self.db.team_statistics.bulk_write(team_ops, ordered=False)
                total_team += (result.upserted_count or 0) + (result.modified_count or 0)

            # ── Match statistics ───────────────────────────────────────
            match_stats_doc = self._aggregate_match_stats(adapted, raw_events, str(mid), now)
            if match_stats_doc:
                scoutpro_match_id = next(
                    (event.get("scoutpro_match_id") for event in raw_events if event.get("scoutpro_match_id") not in (None, "")),
                    None,
                )
                if scoutpro_match_id is not None:
                    match_stats_doc["scoutpro_match_id"] = scoutpro_match_id

                # Resolve ScoutPro IDs for home/away team
                for side in ("home_team_id", "away_team_id"):
                    opta_tid = match_stats_doc.get(side)
                    if opta_tid and opta_tid not in team_sp_cache:
                        team_sp_cache[opta_tid] = self._resolve_scoutpro_team_id(opta_tid)
                    if opta_tid:
                        match_stats_doc[f"scoutpro_{side}"] = team_sp_cache.get(opta_tid)
                self.db.match_statistics.update_one(
                    {"match_id": str(mid)},
                    {"$set": match_stats_doc},
                    upsert=True,
                )

        logger.info(
            "EventStatsPipeline: wrote %d player docs, %d team docs across %d matches",
            total_player, total_team, len(match_ids),
        )
        return {"player_docs": total_player, "team_docs": total_team}

    # ------------------------------------------------------------------
    # Match-level aggregation (EventMinutes + per-team counters)
    # ------------------------------------------------------------------

    def _aggregate_match_stats(
        self,
        adapted: List[F24EventAdapter],
        raw_events: List[Dict[str, Any]],
        match_id: str,
        now: str,
    ) -> Optional[Dict[str, Any]]:
        """Produce a single match-level statistics document.

        Uses `EventMinutes` (shared) for the goal/card/substitution timeline
        and per-team counters for the headline box-score numbers.
        """
        try:
            import json as _json
            from shared.events.EventMinutes import EventMinutes

            # ── EventMinutes timeline ─────────────────────────────────────
            handler = EventMinutes()
            handler.callEventHandler({"events": adapted})
            # EventMinutes stores team/player IDs as integer dict keys which
            # MongoDB rejects.  Round-trip through JSON to coerce all keys to strings.
            try:
                timeline = _json.loads(_json.dumps(handler.results, default=str))
            except Exception:
                timeline = {}

            # ── Determine home / away team IDs ────────────────────────────
            team_ids: List[str] = []
            for ev in raw_events:
                tid = str(ev.get("team_id") or ev.get("teamID") or "")
                if tid and tid not in team_ids:
                    team_ids.append(tid)

            home_team_id = team_ids[0] if len(team_ids) > 0 else None
            away_team_id = team_ids[1] if len(team_ids) > 1 else None

            # ── Build per-team adapted event buckets ──────────────────────
            per_team: Dict[str, List[F24EventAdapter]] = defaultdict(list)
            for ev_obj in adapted:
                if ev_obj.teamID:
                    per_team[str(ev_obj.teamID)].append(ev_obj)

            def _team_counters(ev_list: List[F24EventAdapter]) -> Dict[str, int]:
                c: Dict[str, int] = {
                    "goals": 0, "shots": 0, "passes": 0, "passes_successful": 0,
                    "tackles": 0, "interceptions": 0, "clearances": 0,
                    "fouls": 0, "yellow_cards": 0, "red_cards": 0, "corners": 0,
                }
                for ev in ev_list:
                    tname = str(ev._raw.get("type_name") or "").lower().strip()
                    is_ok = ev.outcome == 1
                    if tname in self._PASS_TYPES:
                        c["passes"] += 1
                        if is_ok:
                            c["passes_successful"] += 1
                    if tname in self._CORNER_TYPES:
                        c["corners"] += 1
                    if tname in self._SHOT_TYPES:
                        c["shots"] += 1
                        if tname == "goal" or ev._raw.get("is_goal"):
                            c["goals"] += 1
                    if tname in self._TACKLE_TYPES:
                        c["tackles"] += 1
                    if tname in self._INTERCEPTION_TYPES:
                        c["interceptions"] += 1
                    if tname in self._CLEARANCE_TYPES:
                        c["clearances"] += 1
                    if tname in self._FOUL_TYPES:
                        c["fouls"] += 1
                    if tname in self._CARD_TYPES:
                        card_raw = str(ev._raw.get("card_type") or "").lower()
                        if not card_raw:
                            for q in ev.qEvents:
                                if q.qualifierID in (32, 33):
                                    card_raw = str(q.value).lower()
                                    break
                        if "yellow" in card_raw or "second" in card_raw:
                            c["yellow_cards"] += 1
                        elif "red" in card_raw:
                            c["red_cards"] += 1
                return c

            home_c = _team_counters(per_team.get(home_team_id, []) if home_team_id else [])
            away_c = _team_counters(per_team.get(away_team_id, []) if away_team_id else [])

            # ── Compute pass accuracy ─────────────────────────────────────
            def _pass_acc(c: Dict[str, int]) -> float:
                total = c.get("passes", 0)
                succ = c.get("passes_successful", 0)
                return round(succ / total * 100, 2) if total else 0.0

            # ── Meta from any event ───────────────────────────────────────
            meta_ev = raw_events[0] if raw_events else {}
            competition_id = meta_ev.get("competition_id")
            season_id = meta_ev.get("season_id")

            doc: Dict[str, Any] = {
                "match_id": match_id,
                "competition_id": competition_id,
                "season_id": season_id,
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                # Headline scoreline
                "home_goals": home_c["goals"],
                "away_goals": away_c["goals"],
                # Shots
                "home_shots": home_c["shots"],
                "away_shots": away_c["shots"],
                # Passing
                "home_passes": home_c["passes"],
                "away_passes": away_c["passes"],
                "home_passes_successful": home_c["passes_successful"],
                "away_passes_successful": away_c["passes_successful"],
                "home_pass_accuracy": _pass_acc(home_c),
                "away_pass_accuracy": _pass_acc(away_c),
                # Corners
                "home_corners": home_c["corners"],
                "away_corners": away_c["corners"],
                # Defence
                "home_tackles": home_c["tackles"],
                "away_tackles": away_c["tackles"],
                "home_interceptions": home_c["interceptions"],
                "away_interceptions": away_c["interceptions"],
                "home_clearances": home_c["clearances"],
                "away_clearances": away_c["clearances"],
                # Discipline
                "home_fouls": home_c["fouls"],
                "away_fouls": away_c["fouls"],
                "home_yellow_cards": home_c["yellow_cards"],
                "away_yellow_cards": away_c["yellow_cards"],
                "home_red_cards": home_c["red_cards"],
                "away_red_cards": away_c["red_cards"],
                # Match-minute timeline from EventMinutes
                "goal_events": timeline.get("Goals", []),
                "yellow_card_events": timeline.get("Yellow Cards", []),
                "red_card_events": timeline.get("Red Cards", []),
                "substitution_on_events": timeline.get("Player On", []),
                "substitution_off_events": timeline.get("Player Off", []),
                "first_half_end": timeline.get("First Half End", []),
                "match_end": timeline.get("End of the Game", []),
                # Totals
                "total_events": len(raw_events),
                "updated_at": now,
            }
            return doc
        except Exception as exc:
            logger.warning("_aggregate_match_stats(%s) failed: %s", match_id, exc)
            return None

    # ------------------------------------------------------------------
    # Team aggregation (counters only — no per-player breakdowns needed)
    # ------------------------------------------------------------------

    _PASS_TYPES = {"pass", "cross", "offside_pass", "offside pass", "corner_taken", "corner"}
    _CORNER_TYPES = {"corner", "corner awarded", "corner_awarded", "corner_taken"}
    _SHOT_TYPES = {"shot", "miss", "post", "attempt_saved", "attempt saved", "goal",
                   "blocked_shot", "chance_missed", "chance missed"}
    _TACKLE_TYPES = {"tackle"}
    _INTERCEPTION_TYPES = {"interception"}
    _CLEARANCE_TYPES = {"clearance"}
    _FOUL_TYPES = {"foul"}
    _CARD_TYPES = {"card"}

    def _aggregate_team_counters(self, events: List[F24EventAdapter]) -> Dict[str, Any]:
        counters: Dict[str, Any] = {
            "passes": 0, "passes_successful": 0, "shots": 0, "goals": 0,
            "tackles": 0, "interceptions": 0, "clearances": 0,
            "fouls": 0, "yellow_cards": 0, "red_cards": 0,
            "total_events": len(events),
        }
        for ev in events:
            tname = str(ev._raw.get("type_name") or "").lower().strip()
            is_ok = ev.outcome == 1
            if tname in self._PASS_TYPES:
                counters["passes"] += 1
                if is_ok:
                    counters["passes_successful"] += 1
            elif tname in self._SHOT_TYPES:
                counters["shots"] += 1
                if tname == "goal" or ev._raw.get("is_goal"):
                    counters["goals"] += 1
            elif tname in self._TACKLE_TYPES:
                counters["tackles"] += 1
            elif tname in self._INTERCEPTION_TYPES:
                counters["interceptions"] += 1
            elif tname in self._CLEARANCE_TYPES:
                counters["clearances"] += 1
            elif tname in self._FOUL_TYPES:
                counters["fouls"] += 1
            elif tname in self._CARD_TYPES:
                card_val = ""
                for q in ev.qEvents:
                    if q.qualifierID in (32, 33):  # Opta card type qualifiers
                        card_val = str(q.value).lower()
                        break
                card_raw = str(ev._raw.get("card_type") or card_val).lower()
                if "yellow" in card_raw or "second" in card_raw:
                    counters["yellow_cards"] += 1
                elif "red" in card_raw:
                    counters["red_cards"] += 1
        return counters
