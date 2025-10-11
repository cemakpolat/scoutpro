"""
Player API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import sys
sys.path.append('/app')
from shared.models.base import Player, PlayerStatistics, APIResponse
from services.player_service import PlayerService
from dependencies import get_player_service

router = APIRouter(prefix="/api/v2/players", tags=["players"])


@router.get("/{player_id}", response_model=APIResponse)
async def get_player(
    player_id: str,
    service: PlayerService = Depends(get_player_service)
):
    """Get player by ID"""
    player = await service.get_player(player_id)

    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")

    return APIResponse(
        success=True,
        data=player.dict(),
        message="Player retrieved successfully"
    )


@router.get("", response_model=APIResponse)
async def list_players(
    position: Optional[List[str]] = Query(None),
    club: Optional[List[str]] = Query(None),
    age_min: Optional[int] = Query(None),
    age_max: Optional[int] = Query(None),
    limit: int = Query(100, le=500),
    service: PlayerService = Depends(get_player_service)
):
    """List players with filters"""
    filters = {}

    if position:
        filters['position'] = position
    if club:
        filters['club'] = club
    if age_min:
        filters['age_min'] = age_min
    if age_max:
        filters['age_max'] = age_max

    players = await service.list_players(filters, limit)

    return APIResponse(
        success=True,
        data=[p.dict() for p in players],
        message=f"Retrieved {len(players)} players"
    )


@router.get("/search", response_model=APIResponse)
async def search_players(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
    service: PlayerService = Depends(get_player_service)
):
    """Search players by name"""
    players = await service.search_players(q, limit)

    return APIResponse(
        success=True,
        data=[p.dict() for p in players],
        message=f"Found {len(players)} players matching '{q}'"
    )


@router.get("/{player_id}/statistics", response_model=APIResponse)
async def get_player_statistics(
    player_id: str,
    stat_type: Optional[str] = Query(None),
    per_90: bool = Query(False),
    service: PlayerService = Depends(get_player_service)
):
    """Get player statistics"""
    stats = await service.get_player_statistics(player_id, stat_type, per_90)

    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Statistics not found for player {player_id}"
        )

    return APIResponse(
        success=True,
        data=stats.dict(),
        message="Statistics retrieved successfully"
    )


@router.post("", response_model=APIResponse, status_code=201)
async def create_player(
    player: Player,
    service: PlayerService = Depends(get_player_service)
):
    """Create new player"""
    try:
        player_id = await service.create_player(player)

        return APIResponse(
            success=True,
            data={"player_id": player_id},
            message="Player created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{player_id}", response_model=APIResponse)
async def update_player(
    player_id: str,
    player: Player,
    service: PlayerService = Depends(get_player_service)
):
    """Update player"""
    try:
        success = await service.update_player(player_id, player)

        if not success:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")

        return APIResponse(
            success=True,
            message="Player updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
