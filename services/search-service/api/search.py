"""
Search API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional, Dict, Any, List
import sys
sys.path.append('/app')
from shared.models.base import APIResponse
from config.settings import get_settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/search", tags=["search"])

settings = get_settings()


@router.get("/players", response_model=APIResponse)
async def search_players(
    request: Request,
    q: str = Query(..., min_length=2),
    position: Optional[str] = Query(None),
    club: Optional[str] = Query(None),
    size: int = Query(20, le=100)
):
    """Search for players"""
    search_client = request.app.state.search_client
    results = await search_client.search_players(q, position=position, club=club, limit=size)

    return APIResponse(
        success=True,
        data=results,
        message=f"Found {len(results)} players"
    )


@router.get("/teams", response_model=APIResponse)
async def search_teams(
    request: Request,
    q: str = Query(..., min_length=2),
    size: int = Query(20, le=100)
):
    """Search for teams"""
    search_client = request.app.state.search_client
    results = await search_client.search_teams(q, limit=size)

    return APIResponse(
        success=True,
        data=results,
        message=f"Found {len(results)} teams"
    )


@router.get("/all", response_model=APIResponse)
async def search_all(
    request: Request,
    q: str = Query(..., min_length=2),
    size: int = Query(10, le=50)
):
    """Search across all entities"""
    search_client = request.app.state.search_client
    results = await search_client.search_all(q, size)

    total = sum(len(v) for v in results.values())

    return APIResponse(
        success=True,
        data=results,
        message=f"Found {total} total results"
    )


@router.post("/index/player/{player_id}", response_model=APIResponse)
async def index_player(request: Request, player_id: str, player_data: Dict[str, Any]):
    """Index a player for search"""
    try:
        search_client = request.app.state.search_client
        await search_client.index_player(player_id, player_data)

        return APIResponse(
            success=True,
            message=f"Player {player_id} indexed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/team/{team_id}", response_model=APIResponse)
async def index_team(request: Request, team_id: str, team_data: Dict[str, Any]):
    """Index a team for search"""
    try:
        search_client = request.app.state.search_client
        await search_client.index_team(team_id, team_data)

        return APIResponse(
            success=True,
            message=f"Team {team_id} indexed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backend")
async def get_backend(request: Request):
    """Return which search backend is active."""
    client = request.app.state.search_client
    return {"backend": client.backend, "es_available": client._es_available}


@router.get("/events", response_model=APIResponse)
async def search_events(
    request: Request,
    player_id: Optional[str] = Query(None, description="Filter by player ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type (pass, shot, tackle, etc.)"),
    match_id: Optional[str] = Query(None, description="Filter by match ID"),
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    size: int = Query(50, ge=1, le=500)
):
    """
    Search for match events with filtering.
    
    Query parameters:
    - player_id: Get events for a specific player
    - event_type: Filter by shot, pass, tackle, corner, etc.
    - match_id: Get events from a specific match
    - team_id: Get events from a team (across all their matches)
    """
    try:
        search_client = request.app.state.search_client
        
        # Build MongoDB query
        query: Dict[str, Any] = {}
        
        if player_id:
            pid_variants: List[Any] = [player_id]
            if player_id.isdigit():
                pid_variants.append(int(player_id))
            elif player_id.lower().startswith('p') and player_id[1:].isdigit():
                pid_variants.append(player_id[1:])
                pid_variants.append(int(player_id[1:]))
            query['$or'] = [
                {'player_id': {'$in': pid_variants}},
                {'playerID': {'$in': pid_variants}},
            ]
        
        if event_type:
            query['type_name'] = event_type
        
        if match_id:
            # Handle both string and numeric match IDs
            try:
                query['matchID'] = {'$in': [match_id, int(match_id)]}
            except (ValueError, TypeError):
                query['matchID'] = match_id
        
        # If team_id provided, find their matches first
        if team_id:
            try:
                db = search_client._get_db()
                matches_collection = db['matches']
                matches = await matches_collection.find({
                    '$or': [
                        {'homeTeamID': team_id},
                        {'awayTeamID': team_id},
                        {'home_team_id': team_id},
                        {'away_team_id': team_id},
                    ]
                }, {'matchID': 1, 'uID': 1}).to_list(None)

                match_ids = [m.get('matchID') or m.get('uID') for m in matches if m.get('matchID') or m.get('uID')]
                if match_ids:
                    query['matchID'] = {'$in': match_ids}
                else:
                    return APIResponse(
                        success=True,
                        data=[],
                        message=f"No matches found for team {team_id}"
                    )
            except Exception as e:
                logger.warning(f"Team filtering failed, skipping: {e}")

        # Query events directly from MongoDB
        try:
            db = search_client._get_db()
            events_collection = db['match_events']
            
            events = await events_collection.find(query).sort('timestamp', -1).to_list(size)
            
            # Remove MongoDB internal IDs
            for event in events:
                event.pop('_id', None)
            
            return APIResponse(
                success=True,
                data=events,
                message=f"Found {len(events)} events"
            )
        except Exception as e:
            logger.error(f"MongoDB event search failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to search events")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Event search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
