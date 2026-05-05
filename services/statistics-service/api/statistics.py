"""
Statistics API Endpoints
"""
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Optional, List
import asyncio
import logging
import sys
sys.path.append('/app')
from shared.models.base import APIResponse
from services.statistics_service import StatisticsService
from dependencies import get_statistics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/statistics", tags=["statistics"])


class ProjectionRebuildRequest(BaseModel):
    match_id: Optional[str] = None
    competition_id: Optional[str] = None
    season_id: Optional[str] = None


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


@router.get("/match/{match_id}", response_model=APIResponse)
async def get_match_statistics(
    match_id: str,
    service: StatisticsService = Depends(get_statistics_service)
):
    """Get aggregated match statistics: box score, passing, discipline, and EventMinutes timeline."""
    stats = await service.get_match_statistics(match_id)
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Statistics not found for match {match_id}"
        )
    return APIResponse(
        success=True,
        data=stats,
        message="Match statistics retrieved successfully"
    )


@router.get("/match/{match_id}/advanced-metrics", response_model=APIResponse)
async def get_match_advanced_metrics(
    match_id: str,
    time_bucket: str = Query("5m"),
    service: StatisticsService = Depends(get_statistics_service)
):
    payload = await service.get_match_advanced_metrics(match_id, time_bucket)
    if not payload:
        raise HTTPException(status_code=404, detail=f"Advanced metrics not found for match {match_id}")

    return APIResponse(
        success=True,
        data=payload,
        message="Match advanced metrics retrieved successfully"
    )


@router.get("/match/{match_id}/tactical", response_model=APIResponse)
async def get_match_tactical_snapshot(
    match_id: str,
    service: StatisticsService = Depends(get_statistics_service)
):
    payload = await service.get_match_tactical_snapshot(match_id)
    if not payload:
        raise HTTPException(status_code=404, detail=f"Tactical snapshot not found for match {match_id}")

    return APIResponse(
        success=True,
        data=payload,
        message="Match tactical snapshot retrieved successfully"
    )


@router.get("/match/{match_id}/pass-network", response_model=APIResponse)
async def get_match_pass_network(
    match_id: str,
    service: StatisticsService = Depends(get_statistics_service)
):
    payload = await service.get_match_pass_network(match_id)
    if not payload:
        raise HTTPException(status_code=404, detail=f"Pass network not found for match {match_id}")

    return APIResponse(
        success=True,
        data=payload,
        message="Match pass network retrieved successfully"
    )


@router.get("/match/{match_id}/sequences", response_model=APIResponse)
async def get_match_sequence_summary(
    match_id: str,
    service: StatisticsService = Depends(get_statistics_service)
):
    payload = await service.get_match_sequence_summary(match_id)
    if not payload:
        raise HTTPException(status_code=404, detail=f"Sequence summary not found for match {match_id}")

    return APIResponse(
        success=True,
        data=payload,
        message="Match sequence summary retrieved successfully"
    )


@router.post("/projections/rebuild", response_model=APIResponse)
async def rebuild_match_projections(
    request: ProjectionRebuildRequest,
    service: StatisticsService = Depends(get_statistics_service)
):
    result = await service.rebuild_match_projections(
        match_id=request.match_id,
        competition_id=request.competition_id,
        season_id=request.season_id,
    )

    return APIResponse(
        success=True,
        data=result,
        message="Projection rebuild completed"
    )


class AggregateRunRequest(BaseModel):
    match_id: Optional[str] = None
    competition_id: Optional[str] = None
    season_id: Optional[str] = None
    background: bool = False  # if True, run asynchronously and return immediately


def _run_pipeline_sync(match_id, competition_id, season_id):
    """Run EventStatsPipeline in a thread (it uses sync pymongo)."""
    from services.event_stats_pipeline import EventStatsPipeline
    pipeline = EventStatsPipeline()
    try:
        return pipeline.run(
            match_id=match_id,
            competition_id=competition_id,
            season_id=season_id,
        )
    finally:
        pipeline.close()


async def _run_pipeline_background(match_id, competition_id, season_id):
    """Async wrapper that runs the sync pipeline in a thread pool."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_pipeline_sync, match_id, competition_id, season_id)
    logger.info("Background EventStatsPipeline finished: %s", result)


@router.post("/aggregate/run", response_model=APIResponse, tags=["statistics"])
async def run_aggregate_pipeline(
    request: AggregateRunRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger the event-statistics aggregation pipeline.

    Reads all ``match_events`` (optionally filtered by match/competition/season),
    applies the shared F24 event classes (PassEvent, ShotandGoalEvents, TouchEvents,
    AerialDuelEvents, FoulEvents, CardEvents, TakeOnEvents) to compute per-player
    and per-team statistics, and upserts them into ``player_statistics`` and
    ``team_statistics`` with ScoutPro IDs.

    Use ``background=true`` for large full-dataset runs (returns immediately).
    """
    if request.background:
        background_tasks.add_task(
            _run_pipeline_background,
            request.match_id,
            request.competition_id,
            request.season_id,
        )
        return APIResponse(
            success=True,
            data={"status": "started"},
            message="Aggregation pipeline started in background"
        )

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        _run_pipeline_sync,
        request.match_id,
        request.competition_id,
        request.season_id,
    )

    return APIResponse(
        success=True,
        data=result,
        message=f"Aggregation complete: {result.get('player_docs', 0)} player docs, "
                f"{result.get('team_docs', 0)} team docs written"
    )
