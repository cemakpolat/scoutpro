from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional


class MatchProjectionBuilder:
    """Build persistent match-level analytics projections from match_events."""

    DEFENSIVE_ACTIONS = {"tackle", "interception", "foul"}

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        if value in (None, "", "None"):
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        if value in (None, "", "None"):
            return default
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _optional_number(value: Any) -> Optional[float]:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _event_type(event: Dict[str, Any]) -> str:
        return str(event.get("type_name") or event.get("type") or "").strip().lower()

    @classmethod
    def _normalize_coordinate(cls, value: Any, axis: str) -> Optional[float]:
        numeric = cls._optional_number(value)
        if numeric is None:
            return None

        normalized = (numeric / 120.0) * 100.0 if axis == "x" and numeric > 100 else numeric
        if axis == "y" and numeric > 100:
            normalized = (numeric / 80.0) * 100.0

        return max(0.0, min(100.0, normalized))

    @classmethod
    def _to_location(cls, location: Any) -> Optional[Dict[str, float]]:
        if not location:
            return None

        if isinstance(location, list) and len(location) >= 2:
            x_value = cls._normalize_coordinate(location[0], "x")
            y_value = cls._normalize_coordinate(location[1], "y")
        elif isinstance(location, dict):
            x_value = cls._normalize_coordinate(location.get("x"), "x")
            y_value = cls._normalize_coordinate(location.get("y"), "y")
        else:
            return None

        if x_value is None or y_value is None:
            return None

        return {
            "x": round(x_value, 2),
            "y": round(y_value, 2),
        }

    @classmethod
    def _event_location(cls, event: Dict[str, Any]) -> Optional[Dict[str, float]]:
        if isinstance(event.get("location"), dict):
            return cls._to_location(event.get("location"))

        raw_event = event.get("raw_event") if isinstance(event.get("raw_event"), dict) else {}
        return (
            cls._to_location(event.get("location"))
            or cls._to_location(raw_event.get("location"))
            or cls._to_location({"x": event.get("x"), "y": event.get("y")})
        )

    @classmethod
    def _get_qualifier_end_location(cls, event: Dict[str, Any]) -> Optional[Dict[str, float]]:
        raw_event = event.get("raw_event") if isinstance(event.get("raw_event"), dict) else {}
        qualifiers = raw_event.get("qualifiers") or event.get("qualifiers") or {}
        if not isinstance(qualifiers, dict):
            return None

        x_value = qualifiers.get(140) if 140 in qualifiers else qualifiers.get("140")
        y_value = qualifiers.get(141) if 141 in qualifiers else qualifiers.get("141")
        if x_value is None or y_value is None:
            return None

        return cls._to_location({"x": x_value, "y": y_value})

    @classmethod
    def _sequence_start_location(cls, event: Dict[str, Any]) -> Optional[Dict[str, float]]:
        raw_event = event.get("raw_event") if isinstance(event.get("raw_event"), dict) else {}
        return cls._to_location(event.get("location") or raw_event.get("location")) or cls._event_location(event)

    @classmethod
    def _sequence_end_location(cls, event: Dict[str, Any]) -> Optional[Dict[str, float]]:
        raw_event = event.get("raw_event") if isinstance(event.get("raw_event"), dict) else {}
        return cls._to_location(
            event.get("end_location")
            or raw_event.get("end_location")
            or raw_event.get("pass_end_location")
            or raw_event.get("carry_end_location")
            or raw_event.get("shot_end_location")
        ) or cls._get_qualifier_end_location(event)

    @classmethod
    def _sequence_action_location(cls, event: Dict[str, Any]) -> Optional[Dict[str, float]]:
        return cls._sequence_end_location(event) or cls._sequence_start_location(event)

    @classmethod
    def _sequence_event_timestamp(cls, event: Dict[str, Any]) -> float:
        explicit = cls._optional_number(event.get("timestamp"))
        if explicit is not None:
            return explicit

        timestamp_seconds = cls._optional_number(event.get("timestamp_seconds"))
        if timestamp_seconds is not None:
            return timestamp_seconds

        minute = cls._to_int(event.get("minute"))
        second = cls._to_int(event.get("second"))
        return float(minute * 60 + second)

    @classmethod
    def _is_actionable_sequence_event(cls, event: Dict[str, Any]) -> bool:
        ignored_event_types = {
            "starting xi",
            "half start",
            "half end",
            "unknown",
            "lineup",
        }
        event_type = cls._event_type(event)
        if not event or event.get("team_id") in (None, "") or not event_type:
            return False

        if event_type in ignored_event_types:
            return False

        no_actor = event.get("player_id") in (None, "")
        if no_actor and not cls._sequence_start_location(event) and not cls._sequence_end_location(event):
            return False

        return True

    @staticmethod
    def _territory_lane(location: Optional[Dict[str, float]]) -> str:
        if not location or location.get("y") is None:
            return "Central Lane"
        if location["y"] < 33:
            return "Left Channel"
        if location["y"] > 66:
            return "Right Channel"
        return "Central Lane"

    @classmethod
    def _is_shot_like(cls, event: Dict[str, Any]) -> bool:
        event_type = cls._event_type(event)
        return bool(event.get("is_goal")) \
            or "shot" in event_type \
            or "goal" in event_type \
            or "attempt saved" in event_type \
            or "miss" in event_type \
            or "post" in event_type

    @classmethod
    def _is_direct_play_event(cls, event: Dict[str, Any]) -> bool:
        event_type = cls._event_type(event)
        raw_event = event.get("raw_event") if isinstance(event.get("raw_event"), dict) else {}
        qualifiers = raw_event.get("qualifiers") or event.get("qualifiers") or {}
        pass_type = str(raw_event.get("pass_type") or event.get("pass_type") or "").lower()

        return "clearance" in event_type \
            or "cross" in event_type \
            or "long" in pass_type \
            or "cross" in pass_type \
            or (isinstance(qualifiers, dict) and any(key in qualifiers for key in (1, "1", 2, "2")))

    @staticmethod
    def _match_team_context(match: Dict[str, Any]) -> Dict[str, str]:
        home_team = match.get("homeTeam") if isinstance(match.get("homeTeam"), dict) else {}
        away_team = match.get("awayTeam") if isinstance(match.get("awayTeam"), dict) else {}

        raw_home_id = (
            match.get("home_team_id")
            or match.get("homeTeamID")
            or match.get("homeTeamId")
            or home_team.get("id")
            or "home"
        )
        raw_away_id = (
            match.get("away_team_id")
            or match.get("awayTeamID")
            or match.get("awayTeamId")
            or away_team.get("id")
            or "away"
        )

        home_team_name = match.get("home_team_name") or match.get("home_team") or match.get("homeTeamName")
        if not home_team_name and isinstance(match.get("homeTeam"), str):
            home_team_name = match.get("homeTeam")
        if not home_team_name:
            home_team_name = home_team.get("name") or (f"Team {raw_home_id}" if raw_home_id != "home" else "Home")

        away_team_name = match.get("away_team_name") or match.get("away_team") or match.get("awayTeamName")
        if not away_team_name and isinstance(match.get("awayTeam"), str):
            away_team_name = match.get("awayTeam")
        if not away_team_name:
            away_team_name = away_team.get("name") or (f"Team {raw_away_id}" if raw_away_id != "away" else "Away")

        return {
            "home_team_id": str(raw_home_id),
            "away_team_id": str(raw_away_id),
            "home_team_name": str(home_team_name),
            "away_team_name": str(away_team_name),
        }

    @staticmethod
    def _round_average(total: float, count: int) -> float:
        if not count:
            return 0.0
        return round((total / count) * 10) / 10

    @staticmethod
    def _score_sequence(sequence: Dict[str, Any]) -> int:
        return sequence["territoryGain"] \
            + sequence["actions"] * 4 \
            + (12 if sequence["finalThirdEntry"] else 0) \
            + (16 if sequence["boxEntry"] else 0) \
            + (20 if sequence["endedWithShot"] else 0) \
            + (40 if sequence["endedWithGoal"] else 0)

    @classmethod
    def _create_sequence(cls, event: Dict[str, Any], match_context: Dict[str, Any]) -> Dict[str, Any]:
        start_location = cls._sequence_start_location(event) or cls._sequence_action_location(event)
        team_id = str(event.get("scoutpro_team_id") or event.get("team_id") or "")
        return {
            "teamId": team_id,
            "teamName": match_context["teamNames"].get(team_id, f"Team {team_id}"),
            "period": cls._to_int(event.get("period")),
            "startTimestamp": cls._sequence_event_timestamp(event),
            "endTimestamp": cls._sequence_event_timestamp(event),
            "startMinute": cls._to_int(event.get("minute")),
            "endMinute": cls._to_int(event.get("minute")),
            "startLocation": start_location,
            "endLocation": cls._sequence_action_location(event) or start_location,
            "directPlay": cls._is_direct_play_event(event),
            "events": [event],
        }

    @classmethod
    def _finalize_sequence(cls, sequence: Dict[str, Any]) -> Dict[str, Any]:
        start_location = sequence.get("startLocation") or sequence.get("endLocation") or {"x": 50, "y": 50}
        end_location = sequence.get("endLocation") or start_location
        duration_seconds = max(1, round(sequence["endTimestamp"] - sequence["startTimestamp"]))
        territory_gain = round((end_location.get("x") or 0) - (start_location.get("x") or 0))
        final_third_entry = (start_location.get("x") or 0) < 66 and (end_location.get("x") or 0) >= 66
        box_entry = (start_location.get("x") or 0) < 83 and (end_location.get("x") or 0) >= 83
        ended_with_shot = any(cls._is_shot_like(event) for event in sequence["events"])
        ended_with_goal = any(bool(event.get("is_goal")) for event in sequence["events"])

        return {
            "teamId": sequence["teamId"],
            "teamName": sequence["teamName"],
            "actions": len(sequence["events"]),
            "durationSeconds": duration_seconds,
            "startTimestamp": sequence["startTimestamp"],
            "endTimestamp": sequence["endTimestamp"],
            "startMinute": sequence["startMinute"],
            "endMinute": sequence["endMinute"],
            "territoryGain": territory_gain,
            "route": cls._territory_lane(end_location),
            "directPlay": sequence["directPlay"],
            "directAttack": duration_seconds <= 15 and territory_gain >= 15 and len(sequence["events"]) >= 3,
            "sustainedPressure": len(sequence["events"]) >= 5 and (end_location.get("x") or 0) >= 66,
            "finalThirdEntry": final_third_entry,
            "boxEntry": box_entry,
            "endedWithShot": ended_with_shot,
            "endedWithGoal": ended_with_goal,
        }

    @classmethod
    def _build_sequences(cls, events: List[Dict[str, Any]], match: Dict[str, Any]) -> List[Dict[str, Any]]:
        match_context_values = cls._match_team_context(match)
        match_context = {
            "teamNames": {
                match_context_values["home_team_id"]: match_context_values["home_team_name"],
                match_context_values["away_team_id"]: match_context_values["away_team_name"],
            }
        }

        actionable_events = sorted(
            [event for event in events if cls._is_actionable_sequence_event(event)],
            key=cls._sequence_event_timestamp,
        )

        sequences: List[Dict[str, Any]] = []
        current_sequence: Optional[Dict[str, Any]] = None

        for event in actionable_events:
            team_id = str(event.get("scoutpro_team_id") or event.get("team_id") or "")
            timestamp = cls._sequence_event_timestamp(event)
            event_period = cls._to_int(event.get("period"))
            action_location = cls._sequence_action_location(event) or cls._sequence_start_location(event)

            should_start_new_sequence = current_sequence is None \
                or current_sequence["teamId"] != team_id \
                or current_sequence["period"] != event_period \
                or timestamp - current_sequence["endTimestamp"] > 12

            if should_start_new_sequence:
                if current_sequence and current_sequence["events"]:
                    sequences.append(cls._finalize_sequence(current_sequence))
                current_sequence = cls._create_sequence(event, match_context)
                continue

            current_sequence["events"].append(event)
            current_sequence["endTimestamp"] = timestamp
            current_sequence["endMinute"] = cls._to_int(event.get("minute")) or current_sequence["endMinute"]
            current_sequence["endLocation"] = action_location or current_sequence["endLocation"]
            current_sequence["directPlay"] = current_sequence["directPlay"] or cls._is_direct_play_event(event)

        if current_sequence and current_sequence["events"]:
            sequences.append(cls._finalize_sequence(current_sequence))

        return sequences

    @staticmethod
    def _build_rapid_regain_index(sequences: List[Dict[str, Any]]) -> Dict[str, int]:
        rapid_regains: Dict[str, int] = {}

        for index in range(2, len(sequences)):
            previous_own_sequence = sequences[index - 2]
            opponent_sequence = sequences[index - 1]
            regained_sequence = sequences[index]

            if previous_own_sequence["teamId"] != regained_sequence["teamId"] or previous_own_sequence["teamId"] == opponent_sequence["teamId"]:
                continue

            regain_window = max(0, regained_sequence["startTimestamp"] - previous_own_sequence["endTimestamp"])
            regained_quickly = regained_sequence["durationSeconds"] <= 8 or opponent_sequence["durationSeconds"] <= 5
            if regain_window <= 8 and regained_quickly:
                rapid_regains[regained_sequence["teamId"]] = rapid_regains.get(regained_sequence["teamId"], 0) + 1

        return rapid_regains

    @staticmethod
    def rebucket_timeline(minute_timeline: List[Dict[str, Any]], bucket_minutes: int) -> List[Dict[str, Any]]:
        rolled: Dict[int, Dict[str, int]] = defaultdict(lambda: {
            "events": 0,
            "goals": 0,
            "shots": 0,
            "passes": 0,
            "cards": 0,
        })

        for row in minute_timeline:
            minute = MatchProjectionBuilder._to_int(row.get("minute"))
            bucket = (minute // bucket_minutes) * bucket_minutes
            rolled[bucket]["events"] += MatchProjectionBuilder._to_int(row.get("events"))
            rolled[bucket]["goals"] += MatchProjectionBuilder._to_int(row.get("goals"))
            rolled[bucket]["shots"] += MatchProjectionBuilder._to_int(row.get("shots"))
            rolled[bucket]["passes"] += MatchProjectionBuilder._to_int(row.get("passes"))
            rolled[bucket]["cards"] += MatchProjectionBuilder._to_int(row.get("cards"))

        return [
            {
                "bucketStartMinute": bucket,
                "bucketEndMinute": bucket + bucket_minutes,
                **values,
            }
            for bucket, values in sorted(rolled.items())
        ]

    @classmethod
    def build_advanced_metrics(
        cls,
        match_id: str,
        match: Dict[str, Any],
        events: List[Dict[str, Any]],
        time_bucket: str = "5m",
    ) -> Dict[str, Any]:
        bucket_digits = "".join(character for character in str(time_bucket) if character.isdigit())
        bucket_minutes = max(1, cls._to_int(bucket_digits, 5))
        event_types = Counter()
        team_counts = Counter()
        minute_timeline: Dict[int, Dict[str, int]] = defaultdict(lambda: {
            "events": 0,
            "goals": 0,
            "shots": 0,
            "passes": 0,
            "cards": 0,
        })

        goals = shots = passes = cards = fouls = substitutions = 0
        player_ids = set()
        team_ids = set()

        for event in events:
            event_type = cls._event_type(event)
            event_types[event_type] += 1
            if event.get("player_id") is not None:
                player_ids.add(str(event.get("player_id")))
            if event.get("team_id") is not None:
                team_id = str(event.get("team_id"))
                team_ids.add(team_id)
                team_counts[team_id] += 1

            minute = cls._to_int(event.get("minute"))
            timeline_bucket = minute_timeline[minute]
            timeline_bucket["events"] += 1

            if "goal" in event_type or bool(event.get("is_goal")):
                goals += 1
                timeline_bucket["goals"] += 1
            if "shot" in event_type:
                shots += 1
                timeline_bucket["shots"] += 1
            if "pass" in event_type:
                passes += 1
                timeline_bucket["passes"] += 1
            if "card" in event_type or event_type in {"yellow card", "red card"}:
                cards += 1
                timeline_bucket["cards"] += 1
            if "foul" in event_type:
                fouls += 1
            if "substitution" in event_type:
                substitutions += 1

        minute_rows = [
            {"minute": minute, **values}
            for minute, values in sorted(minute_timeline.items())
        ]

        return {
            "match_id": match_id,
            "match": match,
            "event_count": len(events),
            "events_available": bool(events),
            "metrics": {
                "goals": goals,
                "shots": shots,
                "passes": passes,
                "cards": cards,
                "fouls": fouls,
                "substitutions": substitutions,
                "uniquePlayers": len(player_ids),
                "uniqueTeams": len(team_ids),
                "eventsByType": dict(event_types.most_common(10)),
                "eventsByTeam": dict(team_counts),
            },
            "minuteTimeline": minute_rows,
            "timeline": cls.rebucket_timeline(minute_rows, bucket_minutes),
            "time_bucket": time_bucket,
            "last_updated": datetime.now().isoformat(),
        }

    @classmethod
    def build_pass_network(cls, match_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        timed_events = []
        for event in events:
            period = cls._to_int(event.get("period"), default=1)
            minute = cls._to_int(event.get("minute"), default=0)
            second = cls._to_int(event.get("second"), default=0)
            game_second = (period - 1) * 5400 + minute * 60 + second
            timed_events.append({
                "player_id": str(event.get("player_id") or ""),
                "team_id": str(event.get("team_id") or ""),
                "minute": minute,
                "game_second": game_second,
                "type_name": cls._event_type(event),
            })
        timed_events.sort(key=lambda event: event["game_second"])

        pass_events = [event for event in timed_events if event["type_name"] == "pass"]
        edges: Dict[tuple, int] = defaultdict(int)
        player_pass_count: Dict[str, int] = defaultdict(int)
        player_team: Dict[str, str] = {}

        for index, event in enumerate(timed_events):
            if event["type_name"] != "pass":
                continue
            player_id = event["player_id"]
            team_id = event["team_id"]
            if player_id:
                player_pass_count[player_id] += 1
                player_team[player_id] = team_id

            for next_index in range(index + 1, min(index + 8, len(timed_events))):
                next_event = timed_events[next_index]
                if next_event["team_id"] != team_id:
                    break
                if next_event["game_second"] - event["game_second"] > 15:
                    break
                receiver = next_event["player_id"]
                if receiver and receiver != player_id:
                    edges[(player_id, receiver, team_id)] += 1
                    break

        team_passes: Dict[str, int] = defaultdict(int)
        for event in pass_events:
            if event["team_id"]:
                team_passes[event["team_id"]] += 1

        total_passes = max(sum(team_passes.values()), 1)
        nodes = [
            {
                "player_id": player_id,
                "team_id": player_team.get(player_id, ""),
                "pass_count": count,
                "pass_share": round(count / total_passes, 3),
            }
            for player_id, count in sorted(player_pass_count.items(), key=lambda item: -item[1])[:30]
        ]
        edge_list = [
            {
                "from_player": passer,
                "to_player": receiver,
                "team_id": team_id,
                "weight": count,
            }
            for (passer, receiver, team_id), count in sorted(edges.items(), key=lambda item: -item[1])
            if count >= 2
        ]

        return {
            "match_id": match_id,
            "total_passes": len(pass_events),
            "nodes": nodes,
            "edges": edge_list,
            "possession_pct": {
                team_id: round(count / total_passes * 100, 1)
                for team_id, count in team_passes.items()
            },
            "top_passers": nodes[:5],
            "last_updated": datetime.now().isoformat(),
        }

    @classmethod
    def build_tactical_snapshot(cls, match_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        teams = sorted({str(event.get("team_id") or "") for event in events if event.get("team_id") not in (None, "")})
        team_stats: Dict[str, Dict[str, Any]] = {
            team_id: {
                "passes": 0,
                "passes_in_opp_half": 0,
                "def_actions": 0,
                "def_actions_in_opp_half": 0,
                "pressures": 0,
                "zones": {"defensive": 0, "middle": 0, "attacking": 0},
            }
            for team_id in teams
        }

        for event in events:
            team_id = str(event.get("team_id") or "")
            if team_id not in team_stats:
                continue
            location = cls._event_location(event) or {"x": 50.0, "y": 50.0}
            x_value = cls._to_float(location.get("x"), default=50.0)
            event_type = cls._event_type(event)

            if event_type == "pass":
                team_stats[team_id]["passes"] += 1
                if x_value > 50:
                    team_stats[team_id]["passes_in_opp_half"] += 1
                if x_value <= 33:
                    zone = "defensive"
                elif x_value <= 66:
                    zone = "middle"
                else:
                    zone = "attacking"
                team_stats[team_id]["zones"][zone] += 1
            elif event_type in cls.DEFENSIVE_ACTIONS:
                team_stats[team_id]["def_actions"] += 1
                if x_value > 50:
                    team_stats[team_id]["def_actions_in_opp_half"] += 1
            elif event_type == "pressure":
                team_stats[team_id]["pressures"] += 1

        tactical = {}
        for team_id in teams:
            opp_passes_in_own_half = sum(
                team_stats[other_team]["passes"] - team_stats[other_team]["passes_in_opp_half"]
                for other_team in teams if other_team != team_id
            )
            def_actions = max(team_stats[team_id]["def_actions_in_opp_half"], 1)
            ppda = round(opp_passes_in_own_half / def_actions, 2)

            total_passes = max(team_stats[team_id]["passes"], 1)
            zones_pct = {
                key: round(value / total_passes * 100, 1)
                for key, value in team_stats[team_id]["zones"].items()
            }

            if ppda < 10:
                press_label = "high press"
            elif ppda < 20:
                press_label = "medium press"
            else:
                press_label = "low press"

            tactical[team_id] = {
                "ppda": ppda,
                "press_style": press_label,
                "passes": team_stats[team_id]["passes"],
                "defensive_actions": team_stats[team_id]["def_actions"],
                "pressures": team_stats[team_id]["pressures"],
                "possession_zones_pct": zones_pct,
            }

        return {
            "match_id": match_id,
            "teams": teams,
            "tactical_metrics": tactical,
            "last_updated": datetime.now().isoformat(),
        }

    @classmethod
    def build_sequence_summary(cls, match_id: str, match: Dict[str, Any], events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not events:
            return None

        sequences = cls._build_sequences(events, match)
        if not sequences:
            return None

        match_context = cls._match_team_context(match)
        team_ids = list(dict.fromkeys(sequence["teamId"] for sequence in sequences if sequence.get("teamId")))
        home_team_id = match_context["home_team_id"] if match_context["home_team_id"] not in ("home", "") else (team_ids[0] if team_ids else "home")
        away_team_id = match_context["away_team_id"] if match_context["away_team_id"] not in ("away", "") else (team_ids[1] if len(team_ids) > 1 else "away")
        home_team_name = match_context["home_team_name"] if match_context["home_team_name"] not in ("Home", "") else (f"Team {home_team_id}" if home_team_id not in ("home", "") else "Home")
        away_team_name = match_context["away_team_name"] if match_context["away_team_name"] not in ("Away", "") else (f"Team {away_team_id}" if away_team_id not in ("away", "") else "Away")
        rapid_regains = cls._build_rapid_regain_index(sequences)

        def build_team_summary(team_id: str, team_name: str) -> Optional[Dict[str, Any]]:
            team_sequences = [sequence for sequence in sequences if sequence["teamId"] == team_id]
            total_sequences = len(team_sequences)
            if not total_sequences:
                return None
            return {
                "teamId": team_id,
                "teamName": team_name,
                "totalSequences": total_sequences,
                "directAttacks": len([sequence for sequence in team_sequences if sequence["directAttack"]]),
                "sustainedPressure": len([sequence for sequence in team_sequences if sequence["sustainedPressure"]]),
                "finalThirdEntries": len([sequence for sequence in team_sequences if sequence["finalThirdEntry"]]),
                "boxEntries": len([sequence for sequence in team_sequences if sequence["boxEntry"]]),
                "shotEndings": len([sequence for sequence in team_sequences if sequence["endedWithShot"]]),
                "goals": len([sequence for sequence in team_sequences if sequence["endedWithGoal"]]),
                "rapidRegains": rapid_regains.get(team_id, 0),
                "averageActions": cls._round_average(sum(sequence["actions"] for sequence in team_sequences), total_sequences),
                "averageDurationSeconds": cls._round_average(sum(sequence["durationSeconds"] for sequence in team_sequences), total_sequences),
            }

        return {
            "matchId": str(match.get("id") or match.get("uID") or match_id),
            "matchLabel": f"{home_team_name} vs {away_team_name}",
            "providers": sorted(set(str(event.get("provider")) for event in events if event.get("provider"))),
            "teamSummaries": [
                summary for summary in [
                    build_team_summary(home_team_id, home_team_name),
                    build_team_summary(away_team_id, away_team_name),
                ] if summary
            ],
            "topSequences": [
                sequence for sequence in sorted(
                    [sequence for sequence in sequences if sequence["actions"] >= 3 or sequence["endedWithShot"] or sequence["finalThirdEntry"]],
                    key=cls._score_sequence,
                    reverse=True,
                )[:4]
            ],
            "last_updated": datetime.now().isoformat(),
        }