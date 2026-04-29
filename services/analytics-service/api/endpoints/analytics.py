"""Analytics Service API Endpoints"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
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
    """Get league-wide trends - passing through to Analytics Handler"""
    # Requires matching API in statistics-service, here returning empty structure pending completion
    return {
        "competition": competition,
        "metric": metric,
        "period": period,
        "data": {"labels": [], "values": []},
        "info": "Real fetching logic requires statistics-service /trends endpoint."
    }


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
    competition: str = Query(...),
    metric: str = Query("points", description="Ranking metric"),
    limit: int = Query(20, ge=1, le=50),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    """Get team rankings by metric passed to statistics service"""
    try:
        response = await handler.get_team_rankings(competition, metric, limit)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/team/{team_id}", summary="Get team insights")
async def get_team_insights(team_id: str, handler: AnalyticsHandler = Depends(get_analytics_handler)):
    """Placeholder for ML insights that will be fetched from ML service"""
    return {"team_id": team_id, "insights": [], "info": "Connects to ML service."}

@router.get("/insights/player/{player_id}", summary="Get player insights")
async def get_player_insights(player_id: str, handler: AnalyticsHandler = Depends(get_analytics_handler)):
    """Placeholder for ML insights that will be fetched from ML service"""
    return {"player_id": player_id, "insights": [], "info": "Connects to ML service."}

@router.get("/comparison/players", summary="Compare multiple players")
async def compare_players(
    player_ids: List[str] = Query(..., description="Player IDs to compare"),
    metrics: Optional[List[str]] = Query(None),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    return {"player_ids": player_ids, "comparison": {}}

@router.get("/comparison/teams", summary="Compare multiple teams")
async def compare_teams(
    team_ids: List[str] = Query(..., description="Team IDs to compare"),
    metrics: Optional[List[str]] = Query(None),
    handler: AnalyticsHandler = Depends(get_analytics_handler)
):
    return {"team_ids": team_ids, "comparison": {}}
