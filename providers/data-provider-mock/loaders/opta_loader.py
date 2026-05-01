"""
Opta file loader for the provider server mock.

Resolves feed files from data/opta/ using Opta's standard naming convention.
"""

from __future__ import annotations

import re
from pathlib import Path
from functools import lru_cache
from typing import Optional

from config import OPTA_ROOT


class OptaFileNotFoundError(FileNotFoundError):
    pass


def _season_dirs(competition_id: str, season_id: str) -> list[Path]:
    return [
        OPTA_ROOT / season_id,
        OPTA_ROOT,
    ]


def _build_filename(
    feed: int,
    competition_id: str,
    season_id: str,
    match_id: Optional[str] = None,
) -> str:
    base = f"f{feed}_{competition_id}_{season_id}"
    if match_id:
        base = f"{base}_{match_id}"
    return base


@lru_cache(maxsize=512)
def load_feed(
    feed: int,
    competition_id: str,
    season_id: str,
    match_id: Optional[str] = None,
) -> bytes:
    filename = _build_filename(feed, competition_id, season_id, match_id)

    for directory in _season_dirs(competition_id, season_id):
        candidate = directory / filename
        if candidate.is_file():
            return candidate.read_bytes()

    raise OptaFileNotFoundError(
        f"No file found for feed=F{feed} competition={competition_id} "
        f"season={season_id} match={match_id}. "
        f"Searched: {[str(d / filename) for d in _season_dirs(competition_id, season_id)]}"
    )


def list_match_ids(competition_id: str, season_id: str) -> list[str]:
    pattern = re.compile(
        rf"^f24_{re.escape(competition_id)}_{re.escape(season_id)}_(\d+)$"
    )
    match_ids: list[str] = []
    for directory in _season_dirs(competition_id, season_id):
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            match = pattern.match(path.name)
            if match:
                match_ids.append(match.group(1))
    return sorted(set(match_ids))


def list_competitions() -> list[dict]:
    results: dict[tuple, dict] = {}
    feed_pattern = re.compile(r"^f(\d+)_(\d+)_(\d+)(?:_(\d+))?$")

    for path in OPTA_ROOT.rglob("f*"):
        if not path.is_file():
            continue
        match = feed_pattern.match(path.name)
        if not match:
            continue
        feed_num, comp_id, seas_id, match_id = match.groups()
        key = (comp_id, seas_id)
        if key not in results:
            results[key] = {
                "competition_id": comp_id,
                "season_id": seas_id,
                "feed_types": set(),
                "match_count": 0,
            }
        results[key]["feed_types"].add(int(feed_num))
        if match_id:
            results[key]["match_count"] += 1

    return [
        {**value, "feed_types": sorted(value["feed_types"])}
        for value in results.values()
    ]
