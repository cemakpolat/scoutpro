"""
Match API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
sys.path.append('/app')
from shared.models.base import Match, APIResponse
from services.match_service import MatchService
from dependencies import get_match_service

router = APIRouter(prefix="/api/v2/matches", tags=["matches"])


@router.get("/{match_id}", response_model=APIResponse)
async def get_match(
    match_id: str,
    service: MatchService = Depends(get_match_service)
):
    """Get match by ID"""
    match = await service.get_match(match_id)

    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

    return APIResponse(
        success=True,
        data=match.dict(),
        message="Match retrieved successfully"
    )


@router.get("", response_model=APIResponse)
async def list_matches(
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    team_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    service: MatchService = Depends(get_match_service)
):
    """List matches with filters"""
    filters = {}

    if competition_id:
        filters['competition_id'] = competition_id
    if season_id:
        filters['season_id'] = season_id
    if team_id:
        filters['team_id'] = team_id
    if status:
        filters['status'] = status

    matches = await service.list_matches(filters, limit)

    return APIResponse(
        success=True,
        data=[m.dict() for m in matches],
        message=f"Retrieved {len(matches)} matches"
    )


@router.get("/team/{team_id}", response_model=APIResponse)
async def get_team_matches(
    team_id: str,
    limit: int = Query(20, le=100),
    service: MatchService = Depends(get_match_service)
):
    """Get matches for a specific team"""
    matches = await service.get_team_matches(team_id, limit)

    return APIResponse(
        success=True,
        data=[m.dict() for m in matches],
        message=f"Retrieved {len(matches)} matches for team {team_id}"
    )


@router.get("/live", response_model=APIResponse)
async def get_live_matches(
    service: MatchService = Depends(get_match_service)
):
    """Get currently live matches"""
    matches = await service.get_live_matches()

    return APIResponse(
        success=True,
        data=[m.dict() for m in matches],
        message=f"Retrieved {len(matches)} live matches"
    )


@router.get("/date-range", response_model=APIResponse)
async def get_matches_by_date_range(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    limit: int = Query(100, le=500),
    service: MatchService = Depends(get_match_service)
):
    """Get matches within a date range"""
    matches = await service.get_matches_by_date_range(start_date, end_date, limit)

    return APIResponse(
        success=True,
        data=[m.dict() for m in matches],
        message=f"Retrieved {len(matches)} matches"
    )


@router.get("/{match_id}/events", response_model=APIResponse)
async def get_match_events(
    match_id: str,
    service: MatchService = Depends(get_match_service)
):
    """Get all events for a match"""
    events = await service.get_match_events(match_id)

    return APIResponse(
        success=True,
        data=events,
        message=f"Retrieved {len(events)} events for match {match_id}"
    )


@router.post("", response_model=APIResponse, status_code=201)
async def create_match(
    match: Match,
    service: MatchService = Depends(get_match_service)
):
    """Create new match"""
    try:
        match_id = await service.create_match(match)

        return APIResponse(
            success=True,
            data={"match_id": match_id},
            message="Match created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{match_id}", response_model=APIResponse)
async def update_match(
    match_id: str,
    match: Match,
    service: MatchService = Depends(get_match_service)
):
    """Update match"""
    try:
        success = await service.update_match(match_id, match)

        if not success:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

        return APIResponse(
            success=True,
            message="Match updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{match_id}/live", response_model=APIResponse)
async def update_live_data(
    match_id: str,
    live_data: Dict[str, Any],
    service: MatchService = Depends(get_match_service)
):
    """Update live match data"""
    try:
        success = await service.update_live_data(match_id, live_data)

        if not success:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

        return APIResponse(
            success=True,
            message="Live data updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
