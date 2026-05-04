"""Analytics Service API Endpoints"""
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging
import sys
sys.path.append('/app')
from services.analytics_handler import AnalyticsHandler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/analytics", tags=["analytics"])

class DashboardData(BaseModel):
    title: str
    data: Dict[str, Any]
    last_updated: str


class ComparisonRequest(BaseModel):
    player_ids: List[str] = []
    team_ids: List[str] = []
    metrics: Optional[List[str]] = None


class PlayerSequenceCoverageRequest(BaseModel):
    player_ids: List[str] = []


async def get_analytics_handler():
    handler = AnalyticsHandler()
    try:
        yield handler
    finally:
        await handler.close()


@router.get("/dashboard/overview", summary="Get overview dashboard")
async def get_overview_dashboard(
    season: Optional[str] = Query(None, description="Filter by season"),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    """Get overview analytics dashboard based on real aggregated data"""
    try:
        return await handler.get_overview(season)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/team/{team_id}", summary="Get team analytics dashboard")
async def get_team_dashboard(
    team_id: str,
    season: Optional[str] = Query(None),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    """Get team-specific analytics dashboard from statistics service"""
    try:
        return await handler.get_team_dashboard(team_id, season)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/player/{player_id}", summary="Get player analytics dashboard")
async def get_player_dashboard(
    player_id: str,
    season: Optional[str] = Query(None),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    """Get player-specific analytics dashboard from statistics service"""
    try:
        return await handler.get_player_dashboard(player_id, season)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/league", summary="Get league trends")
async def get_league_trends(
    competition: str = Query(..., description="Competition name"),
    metric: str = Query("goals", description="Metric to analyze"),
    period: str = Query("season", description="Time period (season, month, week)"),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    """Get league-wide trends derived from live match data"""
    try:
        return await handler.get_league_trends(competition, metric, period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/players", summary="Get player rankings")
async def get_player_rankings(
    metric: str = Query("goals", description="Ranking metric"),
    position: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    """Get player rankings by metric passed to statistics service"""
    try:
        response = await handler.get_player_rankings(metric, position, limit)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/teams", summary="Get team rankings")
async def get_team_rankings(
    competition: Optional[str] = Query(None),
    metric: str = Query("points", description="Ranking metric"),
    limit: int = Query(20, ge=1, le=50),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    """Get team rankings by metric passed to statistics service"""
    try:
        response = await handler.get_team_rankings(competition or 'all', metric, limit)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced-metrics/{match_id}", summary="Get advanced match metrics")
async def get_advanced_metrics(
    match_id: str,
    time_bucket: str = Query("5m"),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    try:
        return await handler.get_advanced_metrics(match_id, time_bucket)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/team/{team_id}", summary="Get team insights")
async def get_team_insights(team_id: str, handler: AnalyticsHandler = Depends(get_analytics_handler)):
    try:
        return await handler.get_team_insights(team_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/player/{player_id}", summary="Get player insights")
async def get_player_insights(player_id: str, handler: AnalyticsHandler = Depends(get_analytics_handler)):
    try:
        return await handler.get_player_insights(player_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/player/{player_id}/sequences", summary="Get player sequence insights")
async def get_player_sequence_insights(player_id: str, handler: AnalyticsHandler = Depends(get_analytics_handler)):
    try:
        return await handler.get_player_sequence_insights(player_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights/players/sequences", summary="Get player sequence coverage for multiple players")
async def get_player_sequence_coverage(
    request: PlayerSequenceCoverageRequest = Body(...),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    try:
        return await handler.get_player_sequence_coverage(request.player_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparison/players", summary="Compare multiple players")
async def compare_players(
    player_ids: List[str] = Query(..., description="Player IDs to compare"),
    metrics: Optional[List[str]] = Query(None),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    try:
        return await handler.compare_players(player_ids, metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comparison/players", summary="Compare multiple players")
async def compare_players_post(
    request: ComparisonRequest = Body(...),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    try:
        return await handler.compare_players(request.player_ids, request.metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparison/teams", summary="Compare multiple teams")
async def compare_teams(
    team_ids: List[str] = Query(..., description="Team IDs to compare"),
    metrics: Optional[List[str]] = Query(None),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    try:
        return await handler.compare_teams(team_ids, metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comparison/teams", summary="Compare multiple teams")
async def compare_teams_post(
    request: ComparisonRequest = Body(...),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    try:
        return await handler.compare_teams(request.team_ids, request.metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pass-network/{match_id}", summary="Get directed pass network for a match")
async def get_pass_network(
    match_id: str,
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    """
    Build a directed pass-network graph from match events.
    Returns nodes (players + pass share), weighted edges (passer → receiver),
    and per-team possession percentage.
    """
    try:
        return await handler.get_pass_network(match_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tactical/{match_id}", summary="Get tactical metrics for a match")
async def get_tactical_metrics(
    match_id: str,
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    """
    Compute PPDA (Passes Per Defensive Action), possession-zone breakdown
    (defensive / middle / attacking third), and pressing intensity per team.
    """
    try:
        return await handler.get_tactical_metrics(match_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sequences/{match_id}", summary="Get possession-sequence summary for a match")
async def get_sequence_insights(
    match_id: str,
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    try:
        return await handler.get_sequence_insights(match_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MultiMatchRequest(BaseModel):
    match_ids: List[str]


@router.post("/multi-match", summary="Aggregate analytics across multiple matches")
async def get_multi_match_analytics(
    request: MultiMatchRequest = Body(...),
    handler: AnalyticsHandler = Depends(get_analytics_handler),
):
    """Server-side aggregation of events across multiple matches.
    Returns player leaderboard, match KPIs, patterns, and key insights."""
    try:
        return await handler.get_multi_match_analytics(request.match_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# Player spatial analysis (cross-match)
# ------------------------------------------------------------------

@router.get("/player/{player_id}/shots-map", summary="Shot map with xG for a player across recent matches")
async def get_player_shot_map(
    player_id: str,
    last_n: int = Query(10, ge=1, le=30, description="Number of recent matches to include"),
    handler: AnalyticsHandler = Depends(get_analytics_handler),
):
    try:
        return await handler.get_player_shot_map(player_id, last_n_matches=last_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/player/{player_id}/heat-map", summary="Heat map of player event locations across recent matches")
async def get_player_heat_map(
    player_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type (pass, shot, tackle …)"),
    last_n: int = Query(10, ge=1, le=30),
    handler: AnalyticsHandler = Depends(get_analytics_handler),
):
    try:
        return await handler.get_player_heat_map(player_id, event_type=event_type, last_n_matches=last_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/player/{player_id}/pass-map", summary="Pass map with progressive flag for a player across recent matches")
async def get_player_pass_map(
    player_id: str,
    last_n: int = Query(10, ge=1, le=30),
    handler: AnalyticsHandler = Depends(get_analytics_handler),
):
    try:
        return await handler.get_player_pass_map(player_id, last_n_matches=last_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/match/{match_id}/player/{player_id}/stats", summary="Per-player per-match aggregated stats from F24 events")
async def get_match_player_stats(
    match_id: str,
    player_id: str,
    handler: AnalyticsHandler = Depends(get_analytics_handler),
):
    try:
        return await handler.get_match_player_stats(match_id, player_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
