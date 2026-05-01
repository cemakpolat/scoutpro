"""
Event Statistics API Endpoints
Exposes event-type-specific aggregations following legacy architecture pattern
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import sys
sys.path.append('/app')
from shared.models.base import APIResponse
from services.event_aggregator import EventAggregator
from dependencies import get_db_client, get_redis_client

router = APIRouter(prefix="/api/v2/events", tags=["events"])


def get_event_aggregator(
    db_client = Depends(get_db_client),
    redis_client = Depends(get_redis_client)
) -> EventAggregator:
    """Dependency injection for EventAggregator"""
    return EventAggregator(db_client, redis_client)


# ==================== PASS EVENTS ====================

@router.get("/passes/player/{player_id}", response_model=APIResponse)
async def get_player_pass_stats(
    player_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get pass statistics for a player"""
    stats = await aggregator.get_pass_statistics(
        player_id=player_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Pass statistics not found for player {player_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Player pass statistics retrieved successfully"
    )


@router.get("/passes/team/{team_id}", response_model=APIResponse)
async def get_team_pass_stats(
    team_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get pass statistics for a team"""
    stats = await aggregator.get_pass_statistics(
        team_id=team_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Pass statistics not found for team {team_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Team pass statistics retrieved successfully"
    )


# ==================== AERIAL DUEL EVENTS ====================

@router.get("/aerials/player/{player_id}", response_model=APIResponse)
async def get_player_aerial_stats(
    player_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get aerial duel statistics for a player"""
    stats = await aggregator.get_aerial_statistics(
        player_id=player_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Aerial statistics not found for player {player_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Player aerial statistics retrieved successfully"
    )


@router.get("/aerials/team/{team_id}", response_model=APIResponse)
async def get_team_aerial_stats(
    team_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get aerial duel statistics for a team"""
    stats = await aggregator.get_aerial_statistics(
        team_id=team_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Aerial statistics not found for team {team_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Team aerial statistics retrieved successfully"
    )


# ==================== SHOT/GOAL EVENTS ====================

@router.get("/shots/player/{player_id}", response_model=APIResponse)
async def get_player_shot_stats(
    player_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get shot and goal statistics for a player"""
    stats = await aggregator.get_shot_statistics(
        player_id=player_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Shot statistics not found for player {player_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Player shot statistics retrieved successfully"
    )


@router.get("/shots/team/{team_id}", response_model=APIResponse)
async def get_team_shot_stats(
    team_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get shot and goal statistics for a team"""
    stats = await aggregator.get_shot_statistics(
        team_id=team_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Shot statistics not found for team {team_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Team shot statistics retrieved successfully"
    )


# ==================== TACKLE/DUEL EVENTS ====================

@router.get("/tackles/player/{player_id}", response_model=APIResponse)
async def get_player_tackle_stats(
    player_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get tackle and duel statistics for a player"""
    stats = await aggregator.get_tackle_statistics(
        player_id=player_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Tackle statistics not found for player {player_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Player tackle statistics retrieved successfully"
    )


@router.get("/tackles/team/{team_id}", response_model=APIResponse)
async def get_team_tackle_stats(
    team_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get tackle and duel statistics for a team"""
    stats = await aggregator.get_tackle_statistics(
        team_id=team_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Tackle statistics not found for team {team_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Team tackle statistics retrieved successfully"
    )


# ==================== DRIBBLE/TAKE-ON EVENTS ====================

@router.get("/takeons/player/{player_id}", response_model=APIResponse)
async def get_player_takeon_stats(
    player_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get dribble/take-on statistics for a player"""
    stats = await aggregator.get_takeon_statistics(
        player_id=player_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Take-on statistics not found for player {player_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Player take-on statistics retrieved successfully"
    )


@router.get("/takeons/team/{team_id}", response_model=APIResponse)
async def get_team_takeon_stats(
    team_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get dribble/take-on statistics for a team"""
    stats = await aggregator.get_takeon_statistics(
        team_id=team_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Take-on statistics not found for team {team_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Team take-on statistics retrieved successfully"
    )


# ==================== GOALKEEPER EVENTS ====================

@router.get("/goalkeeper/player/{player_id}", response_model=APIResponse)
async def get_goalkeeper_stats(
    player_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get goalkeeper-specific statistics for a player"""
    stats = await aggregator.get_goalkeeper_statistics(
        player_id=player_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Goalkeeper statistics not found for player {player_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Goalkeeper statistics retrieved successfully"
    )


@router.get("/goalkeeper/team/{team_id}", response_model=APIResponse)
async def get_team_goalkeeper_stats(
    team_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get team goalkeeper statistics"""
    stats = await aggregator.get_goalkeeper_statistics(
        team_id=team_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Team goalkeeper statistics not found"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Team goalkeeper statistics retrieved successfully"
    )


# ==================== CARD EVENTS ====================

@router.get("/cards/player/{player_id}", response_model=APIResponse)
async def get_card_stats(
    player_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get card (yellow/red) statistics for a player"""
    stats = await aggregator.get_card_statistics(
        player_id=player_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Card statistics not found for player {player_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Player card statistics retrieved successfully"
    )


@router.get("/cards/team/{team_id}", response_model=APIResponse)
async def get_team_card_stats(
    team_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get card statistics for a team"""
    stats = await aggregator.get_card_statistics(
        team_id=team_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Card statistics not found for team {team_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Team card statistics retrieved successfully"
    )


# ==================== FOUL EVENTS ====================

@router.get("/fouls/player/{player_id}", response_model=APIResponse)
async def get_foul_stats(
    player_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get foul statistics for a player"""
    stats = await aggregator.get_foul_statistics(
        player_id=player_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Foul statistics not found for player {player_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Player foul statistics retrieved successfully"
    )


@router.get("/fouls/team/{team_id}", response_model=APIResponse)
async def get_team_foul_stats(
    team_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get foul statistics for a team"""
    stats = await aggregator.get_foul_statistics(
        team_id=team_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Foul statistics not found for team {team_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Team foul statistics retrieved successfully"
    )


# ==================== ASSIST/KEY PASS EVENTS ====================

@router.get("/assists/player/{player_id}", response_model=APIResponse)
async def get_assist_stats(
    player_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get assist and key pass statistics for a player"""
    stats = await aggregator.get_assist_statistics(
        player_id=player_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Assist statistics not found for player {player_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Player assist statistics retrieved successfully"
    )


@router.get("/assists/team/{team_id}", response_model=APIResponse)
async def get_team_assist_stats(
    team_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get assist statistics for a team"""
    stats = await aggregator.get_assist_statistics(
        team_id=team_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Assist statistics not found for team {team_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Team assist statistics retrieved successfully"
    )


# ==================== BALL CONTROL EVENTS ====================

@router.get("/ball_control/player/{player_id}", response_model=APIResponse)
async def get_ball_control_stats(
    player_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get ball control (touches, receptions) statistics for a player"""
    stats = await aggregator.get_ball_control_statistics(
        player_id=player_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Ball control statistics not found for player {player_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Player ball control statistics retrieved successfully"
    )


@router.get("/ball_control/team/{team_id}", response_model=APIResponse)
async def get_team_ball_control_stats(
    team_id: str,
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get ball control statistics for a team"""
    stats = await aggregator.get_ball_control_statistics(
        team_id=team_id,
        competition_id=competition_id,
        season_id=season_id
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Ball control statistics not found for team {team_id}"
        )
    
    return APIResponse(
        success=True,
        data=stats,
        message="Team ball control statistics retrieved successfully"
    )


# ==================== META ENDPOINTS ====================

@router.get("/types", response_model=APIResponse)
async def get_event_types(
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Get list of all available event types"""
    types = await aggregator.get_all_event_types()
    
    return APIResponse(
        success=True,
        data={"event_types": types, "count": len(types)},
        message=f"Retrieved {len(types)} event types"
    )


@router.post("/cache/clear", response_model=APIResponse)
async def clear_event_cache(
    pattern: str = Query("event:*"),
    aggregator: EventAggregator = Depends(get_event_aggregator)
):
    """Clear event aggregation cache"""
    await aggregator.clear_cache(pattern)
    
    return APIResponse(
        success=True,
        data={"pattern": pattern},
        message="Event cache cleared successfully"
    )
