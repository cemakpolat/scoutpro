"""
StatsBomb file loader for the provider server mock.
"""

from __future__ import annotations

import csv
import io
from functools import lru_cache
from pathlib import Path
from typing import Optional

from config import STATSBOMB_ROOT


class StatsBombFileNotFoundError(FileNotFoundError):
    pass


def _find_match_file(match_id: str) -> Optional[Path]:
    for path in STATSBOMB_ROOT.glob("*.csv"):
        if match_id in path.stem:
            return path
    return None


@lru_cache(maxsize=128)
def load_events_raw(match_id: str) -> bytes:
    path = _find_match_file(match_id)
    if not path:
        raise StatsBombFileNotFoundError(
            f"No StatsBomb CSV found for match_id={match_id} in {STATSBOMB_ROOT}"
        )
    return path.read_bytes()


def load_events_json(match_id: str) -> list[dict]:
    raw = load_events_raw(match_id)
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    return [row for row in reader]


def list_matches() -> list[dict]:
    matches = []
    for path in sorted(STATSBOMB_ROOT.glob("*.csv")):
        parts = path.stem.rsplit("_", 1)
        match_id = parts[-1] if len(parts) == 2 else path.stem
        name_part = parts[0] if len(parts) == 2 else ""
        teams = name_part.split("_") if name_part else []

        matches.append(
            {
                "match_id": match_id,
                "file": path.name,
                "home_team": teams[0] if len(teams) >= 1 else None,
                "away_team": teams[1] if len(teams) >= 2 else None,
            }
        )
    return matches
