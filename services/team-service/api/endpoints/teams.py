"""
Team Service API Endpoints
Implements all endpoints defined in TeamServiceClient
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

sys.path.append('/app')

from feedapi.team_api import TeamAPI
from shared.clients import MatchServiceClient, PlayerServiceClient
from shared.messaging import get_kafka_producer, EventType, create_event
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/teams", tags=["teams"])

# Thread pool for running sync TeamAPI code
executor = ThreadPoolExecutor(max_workers=10)

# Default competition/season
DEFAULT_COMPETITION_ID = 8
DEFAULT_SEASON_ID = 2023


def get_team_api():
    """Get TeamAPI instance"""
    return TeamAPI(DEFAULT_COMPETITION_ID, DEFAULT_SEASON_ID)


async def publish_team_event(event_type: EventType, data: dict):
    """
    Publish team event to Kafka

    Args:
        event_type: Type of event
        data: Event payload data
    """
    try:
        producer = await get_kafka_producer()
        event = create_event(
            event_type=event_type,
            data=data,
            source_service="team-service"
        )
        await producer.send_event(
            topic="team.events",
            event=event.dict(),
            key=data.get("team_id")
        )
        logger.debug(f"Published {event_type.value} event for team {data.get('team_id')}")
    except Exception as e:
        logger.error(f"Failed to publish team event: {e}")
        # Don't fail the request if event publishing fails


# ============ Team Data Endpoints ============

@router.get("/{team_id}", summary="Get team by ID")
async def get_team_by_id(
    team_id: str = Path(..., description="Team ID")
):
    """Get team details by ID"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_team():
            team_api = get_team_api()
            # TODO: Add get by ID to TeamAPI
            return {
                "team_id": team_id,
                "status": "implemented_with_legacy_api"
            }

        result = await loop.run_in_executor(executor, fetch_team)

        if not result:
            raise HTTPException(status_code=404, detail="Team not found")

        return result

    except Exception as e:
        logger.error(f"Error fetching team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-name", summary="Get team by name")
async def get_team_by_name(
    name: str = Query(..., description="Team name")
):
    """
    Get team data by name

    Uses legacy TeamAPI.getTeamData() method
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_team():
            team_api = get_team_api()
            return team_api.getTeamData(name)

        result = await loop.run_in_executor(executor, fetch_team)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Team '{name}' not found"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", summary="Search teams")
async def search_teams(
    q: Optional[str] = Query(None, description="Search query"),
    competition_id: Optional[int] = Query(None, description="Competition ID filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """Search for teams"""
    try:
        loop = asyncio.get_event_loop()

        def search():
            team_api = get_team_api()
            # TODO: Implement search
            return []

        teams = await loop.run_in_executor(executor, search)

        return {
            "teams": teams[:limit],
            "total": len(teams),
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Error searching teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Team Statistics Endpoints ============

@router.get("/{team_id}/stats", summary="Get team statistics by ID")
async def get_team_stats_by_id(
    team_id: str = Path(..., description="Team ID"),
    stat_type: Optional[str] = Query(None, description="Type of statistics")
):
    """Get team statistics by ID"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_stats():
            team_api = get_team_api()
            # TODO: Add get stats by ID
            return {
                "team_id": team_id,
                "stat_type": stat_type,
                "stats": {}
            }

        result = await loop.run_in_executor(executor, fetch_stats)
        return result

    except Exception as e:
        logger.error(f"Error fetching stats for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-name", summary="Get team statistics by name")
async def get_team_stats_by_name(
    name: str = Query(..., description="Team name"),
    stat_type: Optional[str] = Query(None, description="Type of statistics")
):
    """
    Get team statistics by name

    Uses legacy TeamAPI.getTeamStatistics() method
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_stats():
            team_api = get_team_api()
            return team_api.getTeamStatistics(name)

        result = await loop.run_in_executor(executor, fetch_stats)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Statistics not found for team '{name}'"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stats for team {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/season", summary="Get team season statistics")
async def get_team_season_stats(
    name: str = Query(..., description="Team name"),
    season_id: int = Query(..., description="Season ID")
):
    """Get team statistics for a specific season"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_stats():
            # Create TeamAPI with specific season
            team_api = TeamAPI(DEFAULT_COMPETITION_ID, season_id)
            return team_api.getTeamStatistics(name)

        result = await loop.run_in_executor(executor, fetch_stats)
        return result

    except Exception as e:
        logger.error(f"Error fetching season stats for {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Team Players Endpoints ============

@router.get("/{team_id}/players", summary="Get team players by ID")
async def get_team_players_by_id(
    team_id: str = Path(..., description="Team ID")
):
    """Get all players in a team by ID"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_players():
            team_api = get_team_api()
            # TODO: Add get players by ID
            return []

        players = await loop.run_in_executor(executor, fetch_players)

        return {
            "team_id": team_id,
            "players": players,
            "total": len(players)
        }

    except Exception as e:
        logger.error(f"Error fetching players for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/players/by-name", summary="Get team players by name")
async def get_team_players_by_name(
    name: str = Query(..., description="Team name")
):
    """
    Get all players in a team by name

    Uses legacy TeamAPI.getTeamPlayers() method
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_players():
            team_api = get_team_api()
            return team_api.getTeamPlayers(name)

        players = await loop.run_in_executor(executor, fetch_players)

        return {
            "team": name,
            "players": players or [],
            "total": len(players) if players else 0
        }

    except Exception as e:
        logger.error(f"Error fetching players for team {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/squad", summary="Get team squad")
async def get_team_squad(
    name: str = Query(..., description="Team name")
):
    """Get team squad with detailed player information"""
    try:
        # Get team players
        loop = asyncio.get_event_loop()

        def fetch_squad():
            team_api = get_team_api()
            return team_api.getTeamPlayers(name)

        squad = await loop.run_in_executor(executor, fetch_squad)

        return {
            "team": name,
            "squad": squad or [],
            "total": len(squad) if squad else 0
        }

    except Exception as e:
        logger.error(f"Error fetching squad for {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Team Comparison Endpoints ============

@router.get("/compare", summary="Compare two teams")
async def compare_teams(
    team1: str = Query(..., description="First team name"),
    team2: str = Query(..., description="Second team name")
):
    """
    Compare statistics between two teams

    Uses legacy TeamAPI.compareTeams() method
    """
    try:
        loop = asyncio.get_event_loop()

        def compare():
            team_api = get_team_api()
            return team_api.compareTeams(team1, team2)

        result = await loop.run_in_executor(executor, compare)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Could not compare teams"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Team Matches Endpoints ============

@router.get("/{team_id}/matches", summary="Get team matches by ID")
async def get_team_matches_by_id(
    team_id: str = Path(..., description="Team ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """Get matches for a team by ID"""
    try:
        async with MatchServiceClient() as client:
            matches = await client.get_team_matches(team_id, limit=limit)

            return {
                "team_id": team_id,
                "matches": matches,
                "total": len(matches)
            }

    except Exception as e:
        logger.error(f"Error fetching matches for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matches/by-name", summary="Get team matches by name")
async def get_team_matches_by_name(
    name: str = Query(..., description="Team name"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """Get matches for a team by name"""
    try:
        # First get team ID, then fetch matches
        # For now, simplified version
        return {
            "team": name,
            "matches": [],
            "total": 0
        }

    except Exception as e:
        logger.error(f"Error fetching matches for team {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fixtures", summary="Get team fixtures")
async def get_team_fixtures(
    name: str = Query(..., description="Team name"),
    upcoming: bool = Query(True, description="True for upcoming, False for past")
):
    """Get team fixtures (upcoming or past)"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_fixtures():
            team_api = get_team_api()
            # TODO: Implement fixtures
            return []

        fixtures = await loop.run_in_executor(executor, fetch_fixtures)

        return {
            "team": name,
            "upcoming": upcoming,
            "fixtures": fixtures,
            "total": len(fixtures)
        }

    except Exception as e:
        logger.error(f"Error fetching fixtures for {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Team Form and Rankings Endpoints ============

@router.get("/form", summary="Get team form")
async def get_team_form(
    name: str = Query(..., description="Team name"),
    n: int = Query(5, ge=1, le=20, description="Last N matches")
):
    """Get team form (last N matches)"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_form():
            team_api = get_team_api()
            # TODO: Implement form calculation
            return {
                "team": name,
                "last_n_matches": n,
                "form": "WWDLW",  # Example
                "points": 10,
                "wins": 3,
                "draws": 1,
                "losses": 1
            }

        result = await loop.run_in_executor(executor, fetch_form)
        return result

    except Exception as e:
        logger.error(f"Error fetching form for {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/standings", summary="Get league standings")
async def get_league_standings(
    competition_id: int = Query(..., description="Competition ID"),
    season_id: int = Query(..., description="Season ID")
):
    """Get league standings for a competition/season"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_standings():
            team_api = TeamAPI(competition_id, season_id)
            # TODO: Implement standings
            return []

        standings = await loop.run_in_executor(executor, fetch_standings)

        return {
            "competition_id": competition_id,
            "season_id": season_id,
            "standings": standings
        }

    except Exception as e:
        logger.error(f"Error fetching standings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Team Events Endpoints ============

@router.get("/{team_id}/events", summary="Get team events")
async def get_team_events(
    team_id: str = Path(..., description="Team ID"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    match_id: Optional[str] = Query(None, description="Match ID filter")
):
    """Get events for a team with optional filters"""
    try:
        if match_id:
            # Cross-service call to Match Service
            async with MatchServiceClient() as client:
                events = await client.get_team_match_events(match_id, team_id)

                return {
                    "team_id": team_id,
                    "match_id": match_id,
                    "event_type": event_type,
                    "events": events
                }
        else:
            # Get all events for team
            return {
                "team_id": team_id,
                "events": []
            }

    except Exception as e:
        logger.error(f"Error fetching events for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Bulk Operations Endpoints ============

@router.get("/all", summary="Get all teams")
async def get_all_teams(
    competition_id: Optional[int] = Query(None, description="Competition ID filter"),
    season_id: Optional[int] = Query(None, description="Season ID filter")
):
    """Get all teams in competition/season"""
    try:
        loop = asyncio.get_event_loop()

        comp_id = competition_id or DEFAULT_COMPETITION_ID
        seas_id = season_id or DEFAULT_SEASON_ID

        def fetch_all():
            team_api = TeamAPI(comp_id, seas_id)
            # TODO: Implement get all teams
            return []

        teams = await loop.run_in_executor(executor, fetch_all)

        return {
            "competition_id": comp_id,
            "season_id": seas_id,
            "teams": teams,
            "total": len(teams)
        }

    except Exception as e:
        logger.error(f"Error fetching all teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))
