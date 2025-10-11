"""
Statistics API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import sys
sys.path.append('/app')
from shared.models.base import APIResponse
from services.statistics_service import StatisticsService
from dependencies import get_statistics_service

router = APIRouter(prefix="/api/v2/statistics", tags=["statistics"])


@router.get("/player/{player_id}", response_model=APIResponse)
async def get_player_statistics(
    player_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    per_90: bool = Query(False),
    service: StatisticsService = Depends(get_statistics_service)
):
    """Get player statistics"""
    stats = await service.get_player_statistics(
        player_id,
        competition_id,
        season_id,
        per_90
    )

    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Statistics not found for player {player_id}"
        )

    return APIResponse(
        success=True,
        data=stats.dict(),
        message="Player statistics retrieved successfully"
    )


@router.get("/team/{team_id}", response_model=APIResponse)
async def get_team_statistics(
    team_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    service: StatisticsService = Depends(get_statistics_service)
):
    """Get team statistics"""
    stats = await service.get_team_statistics(
        team_id,
        competition_id,
        season_id
    )

    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Statistics not found for team {team_id}"
        )

    return APIResponse(
        success=True,
        data=stats,
        message="Team statistics retrieved successfully"
    )


@router.get("/rankings/players", response_model=APIResponse)
async def get_player_rankings(
    stat_name: str = Query(...),
    position: Optional[str] = Query(None),
    competition_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    service: StatisticsService = Depends(get_statistics_service)
):
    """Get player rankings by statistic"""
    rankings = await service.get_player_rankings(
        stat_name,
        position,
        competition_id,
        limit
    )

    return APIResponse(
        success=True,
        data=rankings,
        message=f"Retrieved top {len(rankings)} players for {stat_name}"
    )


@router.get("/rankings/teams", response_model=APIResponse)
async def get_team_rankings(
    stat_name: str = Query(...),
    competition_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    service: StatisticsService = Depends(get_statistics_service)
):
    """Get team rankings by statistic"""
    rankings = await service.get_team_rankings(
        stat_name,
        competition_id,
        limit
    )

    return APIResponse(
        success=True,
        data=rankings,
        message=f"Retrieved top {len(rankings)} teams for {stat_name}"
    )


@router.post("/compare/players", response_model=APIResponse)
async def compare_players(
    player_ids: List[str],
    stat_categories: Optional[List[str]] = None,
    service: StatisticsService = Depends(get_statistics_service)
):
    """Compare multiple players"""
    if len(player_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 players required for comparison"
        )

    comparison = await service.compare_players(player_ids, stat_categories)

    return APIResponse(
        success=True,
        data=comparison,
        message=f"Compared {len(player_ids)} players"
    )


@router.get("/aggregate/player/{player_id}", response_model=APIResponse)
async def aggregate_player_stats(
    player_id: str,
    start_date: str = Query(...),
    end_date: str = Query(...),
    service: StatisticsService = Depends(get_statistics_service)
):
    """Aggregate player stats over time period"""
    aggregated = await service.aggregate_player_stats(
        player_id,
        start_date,
        end_date
    )

    return APIResponse(
        success=True,
        data=aggregated,
        message=f"Aggregated statistics for player {player_id}"
    )
