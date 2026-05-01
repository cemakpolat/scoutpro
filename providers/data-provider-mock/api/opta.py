"""
Opta provider server router.

Exposes feed endpoints that mirror the Opta Stats Perform HTTP API shape so
downstream services can point OPTA_BASE_URL at a provider server and work
without changing their ingestion logic.

Endpoint patterns
-----------------
Season-level feeds (F1, F9, F40):
    GET /api/football/f{feed}/{competition_id}/{season_id}

Match-level feed (F24):
    GET /api/football/f24/{competition_id}/{season_id}/{match_id}

Discovery:
    GET /api/football/matches/{competition_id}/{season_id}
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from loaders.opta_loader import (
    OptaFileNotFoundError,
    load_feed,
    list_match_ids,
)

router = APIRouter(tags=["Opta Feeds"])


def _smart_response(data: bytes) -> Response:
    """Return feed bytes with the correct content type."""
    stripped = data.lstrip()
    if stripped and stripped[0] in (ord('{'), ord('[')):
        return Response(content=data, media_type="application/json")
    if stripped and stripped[0] == ord('<'):
        return Response(content=data, media_type="application/xml")
    return Response(content=data, media_type="application/json")


def _feed_response(
    feed: int,
    competition_id: str,
    season_id: str,
    match_id: str | None = None,
) -> Response:
    try:
        data = load_feed(feed, competition_id, season_id, match_id)
    except OptaFileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _smart_response(data)


@router.get(
    "/f1/{competition_id}/{season_id}",
    summary="F1 — Season schedule (all fixtures and results)",
)
def get_f1(competition_id: str, season_id: str):
    return _feed_response(1, competition_id, season_id)


@router.get(
    "/f9/{competition_id}/{season_id}",
    summary="F9 — Single match summary (lineups, stats, bookings)",
)
def get_f9(competition_id: str, season_id: str):
    return _feed_response(9, competition_id, season_id)


@router.get(
    "/f40/{competition_id}/{season_id}",
    summary="F40 — Squad lists (full player profiles for all teams)",
)
def get_f40(competition_id: str, season_id: str):
    return _feed_response(40, competition_id, season_id)


@router.get(
    "/f24/{competition_id}/{season_id}/{match_id}",
    summary="F24 — In-match events (passes, shots, tackles…)",
)
def get_f24(competition_id: str, season_id: str, match_id: str):
    return _feed_response(24, competition_id, season_id, match_id)


@router.get(
    "/matches/{competition_id}/{season_id}",
    summary="List all available match IDs for this competition/season",
)
def list_matches(competition_id: str, season_id: str):
    match_ids = list_match_ids(competition_id, season_id)
    return {
        "competition_id": competition_id,
        "season_id": season_id,
        "match_count": len(match_ids),
        "match_ids": match_ids,
    }
