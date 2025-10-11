"""
Team API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import sys
sys.path.append('/app')
from shared.models.base import Team, APIResponse
from services.team_service import TeamService
from dependencies import get_team_service

router = APIRouter(prefix="/api/v2/teams", tags=["teams"])


@router.get("/{team_id}", response_model=APIResponse)
async def get_team(
    team_id: str,
    service: TeamService = Depends(get_team_service)
):
    """Get team by ID"""
    team = await service.get_team(team_id)

    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

    return APIResponse(
        success=True,
        data=team.dict(),
        message="Team retrieved successfully"
    )


@router.get("", response_model=APIResponse)
async def list_teams(
    country: Optional[str] = Query(None),
    league: Optional[str] = Query(None),
    competition_id: Optional[int] = Query(None),
    limit: int = Query(100, le=500),
    service: TeamService = Depends(get_team_service)
):
    """List teams with filters"""
    filters = {}

    if country:
        filters['country'] = country
    if league:
        filters['league'] = league
    if competition_id:
        filters['competition_id'] = competition_id

    teams = await service.list_teams(filters, limit)

    return APIResponse(
        success=True,
        data=[t.dict() for t in teams],
        message=f"Retrieved {len(teams)} teams"
    )


@router.get("/search", response_model=APIResponse)
async def search_teams(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
    service: TeamService = Depends(get_team_service)
):
    """Search teams by name"""
    teams = await service.search_teams(q, limit)

    return APIResponse(
        success=True,
        data=[t.dict() for t in teams],
        message=f"Found {len(teams)} teams matching '{q}'"
    )


@router.get("/{team_id}/squad", response_model=APIResponse)
async def get_squad(
    team_id: str,
    service: TeamService = Depends(get_team_service)
):
    """Get team squad"""
    squad = await service.get_squad(team_id)

    return APIResponse(
        success=True,
        data=squad,
        message=f"Retrieved squad for team {team_id}"
    )


@router.post("", response_model=APIResponse, status_code=201)
async def create_team(
    team: Team,
    service: TeamService = Depends(get_team_service)
):
    """Create new team"""
    try:
        team_id = await service.create_team(team)

        return APIResponse(
            success=True,
            data={"team_id": team_id},
            message="Team created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{team_id}", response_model=APIResponse)
async def update_team(
    team_id: str,
    team: Team,
    service: TeamService = Depends(get_team_service)
):
    """Update team"""
    try:
        success = await service.update_team(team_id, team)

        if not success:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

        return APIResponse(
            success=True,
            message="Team updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
