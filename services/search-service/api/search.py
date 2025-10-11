"""
Search API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import sys
sys.path.append('/app')
from shared.models.base import APIResponse
from search.elasticsearch_client import SearchClient
from config.settings import get_settings

router = APIRouter(prefix="/api/v2/search", tags=["search"])

# Initialize search client
settings = get_settings()
search_client = SearchClient(settings.elasticsearch_url)


@router.get("/players", response_model=APIResponse)
async def search_players(
    q: str = Query(..., min_length=2),
    position: Optional[str] = Query(None),
    club: Optional[str] = Query(None),
    size: int = Query(20, le=100)
):
    """Search for players"""
    filters = {}
    if position:
        filters['position'] = position
    if club:
        filters['club'] = club

    results = await search_client.search_players(q, filters, size)

    return APIResponse(
        success=True,
        data=results,
        message=f"Found {len(results)} players"
    )


@router.get("/teams", response_model=APIResponse)
async def search_teams(
    q: str = Query(..., min_length=2),
    size: int = Query(20, le=100)
):
    """Search for teams"""
    results = await search_client.search_teams(q, size=size)

    return APIResponse(
        success=True,
        data=results,
        message=f"Found {len(results)} teams"
    )


@router.get("/all", response_model=APIResponse)
async def search_all(
    q: str = Query(..., min_length=2),
    size: int = Query(10, le=50)
):
    """Search across all entities"""
    results = await search_client.search_all(q, size)

    total = sum(len(v) for v in results.values())

    return APIResponse(
        success=True,
        data=results,
        message=f"Found {total} total results"
    )


@router.post("/index/player/{player_id}", response_model=APIResponse)
async def index_player(player_id: str, player_data: Dict[str, Any]):
    """Index a player for search"""
    try:
        await search_client.index_player(player_id, player_data)

        return APIResponse(
            success=True,
            message=f"Player {player_id} indexed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/team/{team_id}", response_model=APIResponse)
async def index_team(team_id: str, team_data: Dict[str, Any]):
    """Index a team for search"""
    try:
        await search_client.index_team(team_id, team_data)

        return APIResponse(
            success=True,
            message=f"Team {team_id} indexed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
