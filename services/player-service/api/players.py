"""
Player API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
import sys
sys.path.append('/app')
from shared.models.base import Player, PlayerStatistics, APIResponse
from services.player_service import PlayerService
from services.statsbomb_enrichment import StatsBombEnrichmentService
from dependencies import get_player_service, get_mongo_db
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/players", tags=["players"])


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
    q: Optional[str] = Query(None, description="Search query"),
    position: Optional[List[str]] = Query(None),
    club: Optional[List[str]] = Query(None),
    nationality: Optional[str] = Query(None),
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
    if nationality:
        filters['nationality'] = nationality
    if age_min:
        filters['age_min'] = age_min
    if age_max:
        filters['age_max'] = age_max
    if q:
        filters['search'] = q

    players = await service.list_players(filters, limit)

    return APIResponse(
        success=True,
        data=[p.dict() for p in players],
        message=f"Retrieved {len(players)} players"
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


@router.get("/{player_id}/events", response_model=APIResponse)
async def get_player_events(
    player_id: str,
    match_id: Optional[str] = Query(None, description="Filter by match ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type (pass, shot, tackle, etc.)"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """
    Get all events for a player.
    
    Optionally filter by match ID or event type.
    Returns events where the player was involved (as passer, receiver, tackler, etc).
    """
    try:
        events_collection = db['match_events']
        
        # Build query for player events
        query: Dict[str, Any] = {
            'player_id': player_id
        }
        
        if match_id:
            # Handle both numeric and string match IDs
            try:
                query['matchID'] = {'$in': [match_id, int(match_id)]}
            except (ValueError, TypeError):
                query['matchID'] = match_id
        
        if event_type:
            query['type_name'] = event_type
        
        # Fetch events sorted by timestamp
        cursor = events_collection.find(query).sort('timestamp', 1).limit(limit)
        events = await cursor.to_list(length=limit)
        
        # Remove MongoDB internal ID for cleaner response
        for event in events:
            event.pop('_id', None)
        
        return APIResponse(
            success=True,
            data=events,
            message=f"Retrieved {len(events)} events for player {player_id}"
        )
    except Exception as e:
        logger.error(f"Error getting player events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{player_id}/matches", response_model=APIResponse)
async def get_player_matches(
    player_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """
    Get all matches where this player was involved (appeared in events).
    
    Returns distinct match data for matches containing this player's events.
    """
    try:
        events_collection = db['match_events']
        matches_collection = db['matches']
        
        # Find all unique matches containing this player's events
        pipeline = [
            {'$match': {'player_id': player_id}},
            {'$group': {'_id': '$matchID'}},
            {'$limit': limit}
        ]
        
        cursor = events_collection.aggregate(pipeline)
        match_ids = await cursor.to_list(length=limit)
        match_ids = [m['_id'] for m in match_ids]
        
        if not match_ids:
            return APIResponse(
                success=True,
                data=[],
                message=f"No matches found for player {player_id}"
            )
        
        # Fetch match documents
        query = {'$or': [
            {'matchID': {'$in': match_ids}},
            {'uID': {'$in': match_ids}}
        ]}
        
        cursor = matches_collection.find(query).sort('date', -1)
        matches = await cursor.to_list(length=limit)
        
        # Clean up response
        for match in matches:
            match.pop('_id', None)
        
        return APIResponse(
            success=True,
            data=matches,
            message=f"Retrieved {len(matches)} matches for player {player_id}"
        )
    except Exception as e:
        logger.error(f"Error getting player matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@router.post("/enrich/statsbomb", response_model=APIResponse)
async def enrich_statsbomb(
    match_id: Optional[str] = Query(None, description="StatsBomb match_id to enrich; omit for all"),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Trigger the StatsBomb enrichment pipeline.

    Reads StatsBomb CSV event files, aggregates per-player advanced metrics
    (xG, OBV, pass success probability), and writes them onto matched player
    documents in MongoDB as statsbombEnrichment.
    """
    try:
        svc = StatsBombEnrichmentService(db)
        summary = await svc.enrich(match_id=match_id)
        return APIResponse(
            success=True,
            data=summary,
            message=(
                f"StatsBomb enrichment complete: "
                f"{summary['updated']} players updated, "
                f"{summary['unmatched']} unmatched"
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
