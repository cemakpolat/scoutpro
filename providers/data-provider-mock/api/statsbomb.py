"""
StatsBomb provider server router.

Exposes endpoints that mirror the StatsBomb server contract used by ScoutPro.

Endpoints
---------
    GET /api/statsbomb/matches               — list available matches
    GET /api/statsbomb/events/{match_id}     — event-level data as JSON
    GET /api/statsbomb/events/{match_id}/csv — event-level data as raw CSV
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from loaders.statsbomb_loader import (
    StatsBombFileNotFoundError,
    list_matches,
    load_events_json,
    load_events_raw,
)

router = APIRouter(tags=["StatsBomb Feeds"])


@router.get(
    "/matches",
    summary="List all available StatsBomb match files",
)
def get_matches():
    return {"matches": list_matches()}


@router.get(
    "/events/{match_id}",
    summary="Match events as JSON (StatsBomb format)",
)
def get_events_json(match_id: str):
    try:
        events = load_events_json(match_id)
    except StatsBombFileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"match_id": match_id, "event_count": len(events), "events": events}


@router.get(
    "/events/{match_id}/csv",
    summary="Match events as raw CSV",
)
def get_events_csv(match_id: str):
    try:
        data = load_events_raw(match_id)
    except StatsBombFileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{match_id}.csv"'},
    )
