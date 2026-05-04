"""
StatsBomb Connector

Reads StatsBomb data from either the local filesystem or an external provider
server that exposes the ScoutPro StatsBomb contract.

File naming convention used by the local data layer:
    {HomeTeam}_{AwayTeam}_{match_id}.csv
"""
from __future__ import annotations

import csv
import io
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from shared.adapters.base import BaseConnector

logger = logging.getLogger(__name__)

_DEFAULT_ROOT = Path(os.environ.get("DATA_ROOT", "/app/data")) / "statsbomb"


class StatsBombConnector(BaseConnector):
    """
    File-system connector for StatsBomb CSV event data.

    Usage:
        connector = StatsBombConnector({"data_root": "/app/data"})
        rows = await connector.fetch_match_events("3946949")
        players = await connector.fetch_players(match_id="3946949")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        data_root = self.config.get("data_root") or os.environ.get("DATA_ROOT", "/app/data")
        self.root: Path = Path(data_root) / "statsbomb"
        self.online = bool(self.config.get("online", False))
        self.base_url = (self.config.get("base_url") or os.environ.get("STATSBOMB_BASE_URL", "http://data-provider:7000")).rstrip("/")
        self.api_key = self.config.get("api_key") or os.environ.get("STATSBOMB_API_KEY")

    # ------------------------------------------------------------------
    # BaseConnector interface
    # ------------------------------------------------------------------

    def get_provider_name(self) -> str:
        return "statsbomb"

    async def fetch_match_events(self, match_id: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Return all raw CSV rows for the given match_id as a list of dicts.
        Each dict key corresponds to a CSV column header.
        """
        if self.online:
            return await self._fetch_match_events_online(match_id)

        path = self._find_file(match_id)
        if not path:
            logger.warning("StatsBomb CSV not found for match_id=%s in %s", match_id, self.root)
            return []

        raw_bytes = path.read_bytes()
        reader = csv.DictReader(io.StringIO(raw_bytes.decode("utf-8")))
        rows = [dict(row) for row in reader]
        logger.info("Loaded %d StatsBomb event rows for match %s", len(rows), match_id)
        return rows

    async def fetch_players(self, match_id: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract unique players from the StatsBomb event stream.

        For each unique (player_id, player_name) pair found in the CSV,
        aggregates per-player statistics:
          - total_xg   : sum of statsbomb_xg across all events
          - total_obv  : sum of obv_total_net across all events
          - passes     : count of pass events
          - shots      : count of shot events
          - goals      : count of shot events where outcome_name == 'Goal'
          - avg_pass_success_prob : mean pass_success_probability (where non-empty)

        Returns a list of player dicts compatible with the StatsBomb player schema.
        """
        if not match_id:
            # Aggregate across all available matches
            results: Dict[str, Dict[str, Any]] = {}
            for path in sorted(self.root.glob("*.csv")):
                parts = path.stem.rsplit("_", 1)
                mid = parts[-1] if len(parts) == 2 else path.stem
                for player in await self.fetch_players(match_id=mid):
                    pid = player["player_id"]
                    if pid not in results:
                        results[pid] = player
                    else:
                        self._merge_player_stats(results[pid], player)
            return list(results.values())

        rows = await self.fetch_match_events(match_id)
        return self._extract_players_from_rows(rows, match_id)

    async def fetch_teams(self, match_id: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Extract unique teams from StatsBomb event stream."""
        if not match_id:
            return []
        rows = await self.fetch_match_events(match_id)
        teams: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            team_id = self._clean(row.get("team_id") or row.get("possession_team_id"))
            team_name = self._clean(row.get("team_name") or row.get("possession_team_name"))
            if team_id and team_name and team_id not in teams:
                teams[team_id] = {"team_id": team_id, "team_name": team_name, "match_id": match_id}
        return list(teams.values())

    def list_matches(self) -> List[Dict[str, Any]]:
        """List all available StatsBomb matches from file discovery."""
        matches = []
        for path in sorted(self.root.glob("*.csv")):
            parts = path.stem.rsplit("_", 1)
            match_id = parts[-1] if len(parts) == 2 else path.stem
            name_part = parts[0] if len(parts) == 2 else ""
            teams = name_part.split("_") if name_part else []
            matches.append({
                "match_id": match_id,
                "file": path.name,
                "home_team": teams[0] if len(teams) >= 1 else None,
                "away_team": teams[1] if len(teams) >= 2 else None,
            })
        return matches

    # ------------------------------------------------------------------
    # BaseConnector required abstract methods
    # (StatsBomb CSV files don't provide these natively; return empty stubs)
    # ------------------------------------------------------------------

    async def fetch_match(self, match_id: str, **kwargs) -> Dict[str, Any]:
        """Return basic match metadata derived from the CSV file name."""
        path = self._find_file(match_id)
        if not path:
            return {}
        parts = path.stem.rsplit("_", 1)
        name_part = parts[0] if len(parts) == 2 else ""
        teams = name_part.split("_") if name_part else []
        return {
            "match_id": match_id,
            "home_team": teams[0] if len(teams) >= 1 else None,
            "away_team": teams[1] if len(teams) >= 2 else None,
            "provider": "statsbomb",
        }

    async def fetch_matches(
        self,
        competition_id: Optional[str] = None,
        season_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return all available StatsBomb matches from CSV discovery."""
        if self.online:
            return await self._fetch_matches_online()

        return self.list_matches()

    async def fetch_player(self, player_id: str, **kwargs) -> Dict[str, Any]:
        """
        Look up a player across all available StatsBomb match CSVs.
        Returns the first matching player row aggregated across matches.
        """
        for m in self.list_matches():
            players = await self.fetch_players(match_id=m["match_id"])
            for p in players:
                if p.get("player_id") == player_id:
                    return p
        return {}

    async def fetch_team(self, team_id: str, **kwargs) -> Dict[str, Any]:
        """Look up a team across all available StatsBomb match CSVs."""
        for m in self.list_matches():
            teams = await self.fetch_teams(match_id=m["match_id"])
            for t in teams:
                if t.get("team_id") == team_id:
                    return t
        return {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_file(self, match_id: str) -> Optional[Path]:
        for path in self.root.glob("*.csv"):
            if match_id in path.stem:
                return path
        return None

    async def _fetch_matches_online(self) -> List[Dict[str, Any]]:
        payload = await self._request_json(f"{self.base_url}/api/statsbomb/matches")
        if not payload:
            return []
        return payload.get("matches", [])

    async def _fetch_match_events_online(self, match_id: str) -> List[Dict[str, Any]]:
        payload = await self._request_json(f"{self.base_url}/api/statsbomb/events/{match_id}")
        if not payload:
            return []
        return payload.get("events", [])

    async def _request_json(self, url: str) -> Dict[str, Any]:
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.error("StatsBomb provider request failed [%s]: %s", url, exc)
            return {}

    def _extract_players_from_rows(self, rows: List[Dict[str, Any]], match_id: str) -> List[Dict[str, Any]]:
        players: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            # Prefer explicit player fields; fall back to formation/substitution fields
            player_id = self._clean(
                row.get("player_id")
                or row.get("formation_player_id")
                or row.get("substituted_player_id")
            )
            player_name = self._clean(
                row.get("player_name")
                or row.get("formation_player_name")
                or row.get("substituted_player_name")
            )

            if not player_id or not player_name:
                continue

            team_id = self._clean(row.get("team_id") or row.get("possession_team_id"))
            team_name = self._clean(row.get("team_name") or row.get("possession_team_name"))
            position_name = self._clean(
                row.get("player_position_name")
                or row.get("position_name")
                or row.get("formation_position_name")
            )

            if player_id not in players:
                players[player_id] = {
                    "player_id": player_id,
                    "player_name": player_name,
                    "team_id": team_id,
                    "team_name": team_name,
                    "position_name": position_name,
                    "match_id": match_id,
                    # Aggregated stats
                    "total_xg": 0.0,
                    "total_obv": 0.0,
                    "passes": 0,
                    "shots": 0,
                    "goals": 0,
                    "pass_success_probs": [],
                }

            p = players[player_id]
            event_type = self._clean(row.get("event_type_name", "")).lower()

            # xG (only on shot events)
            xg = self._safe_float(row.get("statsbomb_xg"))
            if xg is not None:
                p["total_xg"] += xg

            # On-Ball Value
            obv = self._safe_float(row.get("obv_total_net"))
            if obv is not None:
                p["total_obv"] += obv

            # Pass metrics
            if event_type == "pass":
                p["passes"] += 1
                psp = self._safe_float(row.get("pass_success_probability"))
                if psp is not None:
                    p["pass_success_probs"].append(psp)

            # Shot / goal metrics
            if event_type == "shot":
                p["shots"] += 1
                if self._clean(row.get("outcome_name", "")).lower() == "goal":
                    p["goals"] += 1

            # Fill position if we find a more specific one
            if not p["position_name"] and position_name:
                p["position_name"] = position_name

        # Compute average pass success probability
        for p in players.values():
            probs = p.pop("pass_success_probs", [])
            p["avg_pass_success_prob"] = round(sum(probs) / len(probs), 4) if probs else None
            p["total_xg"] = round(p["total_xg"], 4)
            p["total_obv"] = round(p["total_obv"], 4)

        return list(players.values())

    @staticmethod
    def _merge_player_stats(base: Dict[str, Any], extra: Dict[str, Any]) -> None:
        base["total_xg"] = round(base.get("total_xg", 0.0) + extra.get("total_xg", 0.0), 4)
        base["total_obv"] = round(base.get("total_obv", 0.0) + extra.get("total_obv", 0.0), 4)
        base["passes"] = base.get("passes", 0) + extra.get("passes", 0)
        base["shots"] = base.get("shots", 0) + extra.get("shots", 0)
        base["goals"] = base.get("goals", 0) + extra.get("goals", 0)

    @staticmethod
    def _clean(value: Any) -> Optional[str]:
        if value in (None, "", "None"):
            return None
        return str(value).strip() or None

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
