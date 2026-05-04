"""
Enhanced Events API - Phase 1 Enrichments
RESTful endpoints for advanced event statistics with regional analysis
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Any, List
import logging
import sys

sys.path.append('/app')

from services.event_aggregator_enhanced import EnhancedEventAggregator
from dependencies import get_event_aggregator_enhanced
from shared.models.base import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/events", tags=["events_enhanced"])


@router.get("/passes/enhanced/player/{player_id}")
async def get_player_pass_stats_enhanced(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced pass statistics for a player
    Includes regional breakdown, pass types, context analysis
    """
    try:
        stats = await aggregator.get_pass_statistics_enhanced(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Pass statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced player pass statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving player pass stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/passes/enhanced/team/{team_id}")
async def get_team_pass_stats_enhanced(
    team_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced pass statistics for a team
    """
    try:
        stats = await aggregator.get_pass_statistics_enhanced(
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Pass statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced team pass statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving team pass stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shots/enhanced/player/{player_id}")
async def get_player_shot_stats_enhanced(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced shot statistics for a player
    Includes location analysis, conversion rates, big chances
    """
    try:
        stats = await aggregator.get_shot_statistics_enhanced(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Shot statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced player shot statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving player shot stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shots/enhanced/team/{team_id}")
async def get_team_shot_stats_enhanced(
    team_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced shot statistics for a team
    """
    try:
        stats = await aggregator.get_shot_statistics_enhanced(
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Shot statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced team shot statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving team shot stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/duels/enhanced/player/{player_id}")
async def get_player_duel_stats_enhanced(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced duel statistics for a player
    Includes success rates, regional breakdown
    """
    try:
        stats = await aggregator.get_duel_statistics_enhanced(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Duel statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced player duel statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving player duel stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/duels/enhanced/team/{team_id}")
async def get_team_duel_stats_enhanced(
    team_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced duel statistics for a team
    """
    try:
        stats = await aggregator.get_duel_statistics_enhanced(
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Duel statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced team duel statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving team duel stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tackles/enhanced/player/{player_id}")
async def get_player_tackle_stats_enhanced(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced tackle statistics for a player
    Includes success rates, regional breakdown
    """
    try:
        stats = await aggregator.get_tackle_statistics_enhanced(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Tackle statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced player tackle statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving player tackle stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tackles/enhanced/team/{team_id}")
async def get_team_tackle_stats_enhanced(
    team_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced tackle statistics for a team
    """
    try:
        stats = await aggregator.get_tackle_statistics_enhanced(
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Tackle statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced team tackle statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving team tackle stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ball-control/enhanced/player/{player_id}")
async def get_player_ball_control_stats_enhanced(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced ball control statistics for a player
    Includes touch accuracy, regional analysis
    """
    try:
        stats = await aggregator.get_ball_control_statistics_enhanced(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Ball control statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced player ball control statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving player ball control stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ball-control/enhanced/team/{team_id}")
async def get_team_ball_control_stats_enhanced(
    team_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced ball control statistics for a team
    """
    try:
        stats = await aggregator.get_ball_control_statistics_enhanced(
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Ball control statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced team ball control statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving team ball control stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fouls/enhanced/player/{player_id}")
async def get_player_foul_stats_enhanced(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced foul statistics for a player
    Includes foul types, location analysis
    """
    try:
        stats = await aggregator.get_foul_statistics_enhanced(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Foul statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced player foul statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving player foul stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fouls/enhanced/team/{team_id}")
async def get_team_foul_stats_enhanced(
    team_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced foul statistics for a team
    """
    try:
        stats = await aggregator.get_foul_statistics_enhanced(
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Foul statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced team foul statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving team foul stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/take-ons/enhanced/player/{player_id}")
async def get_player_takeon_stats_enhanced(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced take-on/dribble statistics for a player
    Includes success rates, regional breakdown
    """
    try:
        stats = await aggregator.get_takeon_statistics_enhanced(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Take-on statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced player take-on statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving player take-on stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/take-ons/enhanced/team/{team_id}")
async def get_team_takeon_stats_enhanced(
    team_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced take-on statistics for a team
    """
    try:
        stats = await aggregator.get_takeon_statistics_enhanced(
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Take-on statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced team take-on statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving team take-on stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recoveries/enhanced/player/{player_id}")
async def get_player_recovery_stats_enhanced(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced ball recovery statistics for a player
    """
    try:
        stats = await aggregator.get_ball_recovery_statistics_enhanced(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Recovery statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced player recovery statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving player recovery stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recoveries/enhanced/team/{team_id}")
async def get_team_recovery_stats_enhanced(
    team_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced ball recovery statistics for a team
    """
    try:
        stats = await aggregator.get_ball_recovery_statistics_enhanced(
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Recovery statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced team recovery statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving team recovery stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interceptions/enhanced/player/{player_id}")
async def get_player_interception_stats_enhanced(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced interception statistics for a player
    """
    try:
        stats = await aggregator.get_interception_statistics_enhanced(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Interception statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced player interception statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving player interception stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interceptions/enhanced/team/{team_id}")
async def get_team_interception_stats_enhanced(
    team_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced interception statistics for a team
    """
    try:
        stats = await aggregator.get_interception_statistics_enhanced(
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Interception statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced team interception statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving team interception stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goalkeepers/enhanced/player/{player_id}")
async def get_player_goalkeeper_stats_enhanced(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced goalkeeper statistics for a player
    """
    try:
        stats = await aggregator.get_goalkeeper_statistics_enhanced(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Goalkeeper statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced player goalkeeper statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving player goalkeeper stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goalkeepers/enhanced/team/{team_id}")
async def get_team_goalkeeper_stats_enhanced(
    team_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced goalkeeper statistics for a team
    """
    try:
        stats = await aggregator.get_goalkeeper_statistics_enhanced(
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Goalkeeper statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced team goalkeeper statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving team goalkeeper stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/creative/enhanced/player/{player_id}")
async def get_player_creative_stats_enhanced(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced creative statistics for a player
    """
    try:
        stats = await aggregator.get_creative_statistics_enhanced(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Creative statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced player creative statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving player creative stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/creative/enhanced/team/{team_id}")
async def get_team_creative_stats_enhanced(
    team_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get enhanced creative statistics for a team
    """
    try:
        stats = await aggregator.get_creative_statistics_enhanced(
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id
        )
        
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Creative statistics not found")
        
        return APIResponse(
            success=True,
            data=stats,
            message="Enhanced team creative statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving team creative stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PHASE 3 ENRICHMENTS API ====================

from fastapi import Query

@router.get("/heatmap/player/{player_id}")
async def get_player_heatmap(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    event_type: Optional[str] = None,
    grid_cols: int = 10,
    grid_rows: int = 10,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get spatial density heatmap for a player's events.
    """
    try:
        stats = await aggregator.get_spatial_density_heatmap(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id,
            event_type=event_type,
            grid_cols=grid_cols,
            grid_rows=grid_rows
        )
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Heatmap data not found or error occurred")
            
        return APIResponse(success=True, data=stats, message="Spatial density heatmap retrieved successfully")
    except Exception as e:
        logger.error(f"Error retrieving heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/composite-index/player/{player_id}")
async def get_composite_index(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get composite performance index for a player.
    Combines passing, shooting, and duel metrics.
    """
    try:
        stats = await aggregator.get_player_composite_index(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Composite index could not be calculated")
            
        return APIResponse(success=True, data=stats, message="Composite index retrieved successfully")
    except Exception as e:
        logger.error(f"Error retrieving composite index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expected-metrics/player/{player_id}")
async def get_expected_metrics(
    player_id: str,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Get expected metrics (xG, xA) for a player extracted from enriched events.
    """
    try:
        stats = await aggregator.get_expected_metrics(
            player_id=player_id,
            competition_id=competition_id,
            season_id=season_id
        )
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Expected metrics not found")
            
        return APIResponse(success=True, data=stats, message="Expected metrics retrieved successfully")
    except Exception as e:
        logger.error(f"Error retrieving expected metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similarity/player/{player_id}")
async def get_player_similarity(
    player_id: str,
    targets: List[str] = Query(..., description="List of target player IDs to compare against"),
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Calculate similarity between a base player and target players based on a stat vector.
    """
    try:
        stats = await aggregator.get_player_similarity(
            player_id=player_id,
            target_player_ids=targets,
            competition_id=competition_id,
            season_id=season_id
        )
        if not stats or "error" in stats:
            raise HTTPException(status_code=404, detail="Could not calculate player similarity")
            
        return APIResponse(success=True, data=stats, message="Player similarity calculated successfully")
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/player/{player_id}/analytics-bundle")
async def get_player_analytics_bundle(
    player_id: str,
    team_id: Optional[str] = None,
    competition_id: Optional[int] = None,
    season_id: Optional[int] = None,
    aggregator: EnhancedEventAggregator = Depends(get_event_aggregator_enhanced)
) -> APIResponse:
    """
    Return all player analytics in a single pre-computed bundle.

    Includes: pass stats, shot stats, duel stats, tackle stats, ball control,
    spatial heatmap, composite index, expected metrics (xG/xA), match count.

    Results are persisted to MongoDB player_analytics so subsequent calls are
    instant regardless of Redis state.
    """
    try:
        bundle = await aggregator.get_analytics_bundle(
            player_id=player_id,
            team_id=team_id,
            competition_id=competition_id,
            season_id=season_id,
        )
        return APIResponse(success=True, data=bundle, message="Analytics bundle retrieved")
    except Exception as e:
        logger.error(f"Error retrieving analytics bundle for {player_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
