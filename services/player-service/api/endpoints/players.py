"""
Player Service API Endpoints
Implements all endpoints defined in PlayerServiceClient
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

sys.path.append('/app')

from feedapi.player_api import PlayerAPI
from shared.clients import MatchServiceClient, TeamServiceClient
from shared.messaging import get_kafka_producer, EventType, create_event
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/players", tags=["players"])

# Thread pool for running sync PlayerAPI code
executor = ThreadPoolExecutor(max_workers=10)

# Default competition/season (can be made configurable)
DEFAULT_COMPETITION_ID = 8
DEFAULT_SEASON_ID = 2023


def get_player_api():
    """Get PlayerAPI instance"""
    return PlayerAPI(DEFAULT_COMPETITION_ID, DEFAULT_SEASON_ID)


async def publish_player_event(event_type: EventType, data: dict):
    """
    Publish player event to Kafka

    Args:
        event_type: Type of event
        data: Event payload data
    """
    try:
        producer = await get_kafka_producer()
        event = create_event(
            event_type=event_type,
            data=data,
            source_service="player-service"
        )
        await producer.send_event(
            topic="player.events",
            event=event.dict(),
            key=data.get("player_id")
        )
        logger.debug(f"Published {event_type.value} event for player {data.get('player_id')}")
    except Exception as e:
        logger.error(f"Failed to publish player event: {e}")
        # Don't fail the request if event publishing fails


# ============ Player Data Endpoints ============

@router.get("/{player_id}", summary="Get player by ID")
async def get_player_by_id(
    player_id: str = Path(..., description="Player ID")
):
    """
    Get player details by ID

    Returns comprehensive player information including:
    - Basic details (name, position, team)
    - Current statistics
    - Profile information
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_player():
            player_api = get_player_api()
            # TODO: Add get by ID method to PlayerAPI
            # For now, return placeholder
            return {
                "player_id": player_id,
                "status": "implemented_with_legacy_api"
            }

        result = await loop.run_in_executor(executor, fetch_player)

        if not result:
            raise HTTPException(status_code=404, detail="Player not found")

        return result

    except Exception as e:
        logger.error(f"Error fetching player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", summary="Search players")
async def search_players(
    q: Optional[str] = Query(None, description="Search query (player name)"),
    team: Optional[str] = Query(None, description="Filter by team name"),
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """
    Search for players with optional filters

    Supports:
    - Full-text search by name
    - Team filtering
    - Position filtering
    """
    try:
        loop = asyncio.get_event_loop()

        def search():
            player_api = get_player_api()
            # TODO: Implement search in PlayerAPI
            players = []
            return players[:limit]

        players = await loop.run_in_executor(executor, search)

        return {
            "players": players,
            "total": len(players),
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Error searching players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-name", summary="Get player by team and name")
async def get_player_by_name(
    team: str = Query(..., description="Team name"),
    name: str = Query(..., description="Player name")
):
    """
    Get player data by team name and player name

    Uses legacy PlayerAPI.getPlayerData() method
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_player():
            player_api = get_player_api()
            return player_api.getPlayerData(team, name)

        result = await loop.run_in_executor(executor, fetch_player)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Player '{name}' not found in team '{team}'"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching player {name} from {team}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Player Statistics Endpoints ============

@router.get("/{player_id}/stats", summary="Get player statistics by ID")
async def get_player_stats_by_id(
    player_id: str = Path(..., description="Player ID"),
    per_90: bool = Query(False, description="Normalize to per 90 minutes"),
    stat_type: Optional[str] = Query(None, description="Type of statistics")
):
    """
    Get player statistics by ID

    Options:
    - per_90: Normalize statistics to per 90 minutes
    - stat_type: Filter by stat type (passing, shooting, etc.)
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_stats():
            player_api = get_player_api()
            # TODO: Add get stats by ID to PlayerAPI
            return {
                "player_id": player_id,
                "per_90": per_90,
                "stat_type": stat_type,
                "stats": {}
            }

        result = await loop.run_in_executor(executor, fetch_stats)
        return result

    except Exception as e:
        logger.error(f"Error fetching stats for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-name", summary="Get player statistics by name")
async def get_player_stats_by_name(
    team: str = Query(..., description="Team name"),
    name: str = Query(..., description="Player name"),
    per_90: bool = Query(False, description="Normalize to per 90 minutes"),
    stat_type: Optional[str] = Query(None, description="Type of statistics")
):
    """
    Get player statistics by team and name

    Uses legacy PlayerAPI.getPlayerStatistics() method
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_stats():
            player_api = get_player_api()
            return player_api.getPlayerStatistics(team, name, per_90)

        result = await loop.run_in_executor(executor, fetch_stats)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Statistics not found for {name} from {team}"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stats for {name} from {team}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Player Events Endpoints ============

@router.get("/events/passes", summary="Get player pass events")
async def get_player_pass_events(
    team: str = Query(..., description="Team name"),
    name: str = Query(..., description="Player name")
):
    """
    Get all pass events for a player

    Uses legacy PlayerAPI.getPlayerPassEvents() method
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_passes():
            player_api = get_player_api()
            return player_api.getPlayerPassEvents(team, name)

        passes = await loop.run_in_executor(executor, fetch_passes)

        return {
            "team": team,
            "player": name,
            "passes": passes or [],
            "total": len(passes) if passes else 0
        }

    except Exception as e:
        logger.error(f"Error fetching pass events for {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/shots", summary="Get player shot events")
async def get_player_shot_events(
    team: str = Query(..., description="Team name"),
    name: str = Query(..., description="Player name")
):
    """
    Get all shot events for a player

    Uses legacy PlayerAPI.getPlayerShotEvents() method
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_shots():
            player_api = get_player_api()
            return player_api.getPlayerShotEvents(team, name)

        shots = await loop.run_in_executor(executor, fetch_shots)

        return {
            "team": team,
            "player": name,
            "shots": shots or [],
            "total": len(shots) if shots else 0
        }

    except Exception as e:
        logger.error(f"Error fetching shot events for {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{player_id}/events", summary="Get player events")
async def get_player_events(
    player_id: str = Path(..., description="Player ID"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    match_id: Optional[str] = Query(None, description="Match ID filter")
):
    """
    Get all events for a player with optional filters

    For match-specific events, makes cross-service call to Match Service
    """
    try:
        if match_id:
            # Cross-service call to Match Service
            async with MatchServiceClient() as client:
                events = await client.get_player_match_events(match_id, player_id)
                return {
                    "player_id": player_id,
                    "match_id": match_id,
                    "event_type": event_type,
                    "events": events
                }
        else:
            # Get all events for player
            loop = asyncio.get_event_loop()

            def fetch_events():
                player_api = get_player_api()
                # TODO: Implement get all events in PlayerAPI
                return []

            events = await loop.run_in_executor(executor, fetch_events)

            return {
                "player_id": player_id,
                "events": events
            }

    except Exception as e:
        logger.error(f"Error fetching events for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Player Comparison Endpoints ============

@router.get("/compare", summary="Compare two players")
async def compare_players(
    team1: str = Query(..., description="First player's team"),
    player1: str = Query(..., description="First player name"),
    team2: str = Query(..., description="Second player's team"),
    player2: str = Query(..., description="Second player name")
):
    """
    Compare statistics between two players

    Uses legacy PlayerAPI.comparePlayers() method
    """
    try:
        loop = asyncio.get_event_loop()

        def compare():
            player_api = get_player_api()
            return player_api.comparePlayers(team1, player1, team2, player2)

        result = await loop.run_in_executor(executor, compare)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Could not compare players"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Minutes Played Endpoints ============

@router.get("/minutes", summary="Calculate minutes played")
async def calculate_minutes_played(
    team: str = Query(..., description="Team name"),
    name: str = Query(..., description="Player name")
):
    """
    Calculate total minutes played for a player

    Uses legacy PlayerAPI.calculateMinutesPlayed() method
    """
    try:
        loop = asyncio.get_event_loop()

        def calc_minutes():
            player_api = get_player_api()
            return player_api.calculateMinutesPlayed(team, name)

        result = await loop.run_in_executor(executor, calc_minutes)

        return {
            "team": team,
            "player": name,
            "minutes": result
        }

    except Exception as e:
        logger.error(f"Error calculating minutes for {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Bulk Operations Endpoints ============

@router.get("/by-team", summary="Get players by team")
async def get_players_by_team(
    team: str = Query(..., description="Team name")
):
    """
    Get all players for a specific team

    Makes cross-service call to Team Service
    """
    try:
        async with TeamServiceClient() as client:
            players = await client.get_team_players(team_name=team)

            return {
                "team": team,
                "players": players,
                "total": len(players)
            }

    except Exception as e:
        logger.error(f"Error fetching players for team {team}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top", summary="Get top players by statistic")
async def get_top_players(
    stat: str = Query(..., description="Statistic name (e.g., goals, assists)"),
    limit: int = Query(10, ge=1, le=100, description="Number of players"),
    position: Optional[str] = Query(None, description="Position filter")
):
    """
    Get top N players by a specific statistic
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_top():
            player_api = get_player_api()
            # TODO: Implement top players in PlayerAPI
            return []

        players = await loop.run_in_executor(executor, fetch_top)

        return {
            "statistic": stat,
            "position": position,
            "limit": limit,
            "players": players[:limit]
        }

    except Exception as e:
        logger.error(f"Error fetching top players: {e}")
        raise HTTPException(status_code=500, detail=str(e))
