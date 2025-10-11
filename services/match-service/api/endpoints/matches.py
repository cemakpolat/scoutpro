"""
Match Service API Endpoints
Implements all endpoints defined in MatchServiceClient
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from datetime import datetime
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

sys.path.append('/app')

from feedapi.game_api import GameAPI
from feedapi.event_api import EventAPI
from shared.messaging import get_kafka_producer, EventType, create_event
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/matches", tags=["matches"])

# Thread pool for running sync code
executor = ThreadPoolExecutor(max_workers=10)

# Default competition/season
DEFAULT_COMPETITION_ID = 8
DEFAULT_SEASON_ID = 2023


def get_game_api():
    """Get GameAPI instance"""
    return GameAPI(DEFAULT_COMPETITION_ID, DEFAULT_SEASON_ID)


def get_event_api():
    """Get EventAPI instance"""
    return EventAPI(DEFAULT_COMPETITION_ID, DEFAULT_SEASON_ID)


async def publish_match_event(event_type: EventType, data: dict):
    """
    Publish match event to Kafka

    Args:
        event_type: Type of event
        data: Event payload data
    """
    try:
        producer = await get_kafka_producer()
        event = create_event(
            event_type=event_type,
            data=data,
            source_service="match-service"
        )
        await producer.send_event(
            topic="match.events",
            event=event.dict(),
            key=data.get("match_id")
        )
        logger.debug(f"Published {event_type.value} event for match {data.get('match_id')}")
    except Exception as e:
        logger.error(f"Failed to publish match event: {e}")
        # Don't fail the request if event publishing fails


# ============ Match Data Endpoints ============

@router.get("/{match_id}", summary="Get match by ID")
async def get_match_by_id(
    match_id: str = Path(..., description="Match ID")
):
    """
    Get match details by ID

    Uses legacy GameAPI.getGameDataById() method
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_match():
            game_api = get_game_api()
            return game_api.getGameDataById(match_id)

        result = await loop.run_in_executor(executor, fetch_match)

        if not result:
            raise HTTPException(status_code=404, detail="Match not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching match {match_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", summary="Get all matches")
async def get_all_matches(
    competition_id: Optional[int] = Query(None, description="Competition ID filter"),
    season_id: Optional[int] = Query(None, description="Season ID filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """
    Get all matches with optional filters

    Uses legacy GameAPI.getAllMatches() method
    """
    try:
        loop = asyncio.get_event_loop()

        comp_id = competition_id or DEFAULT_COMPETITION_ID
        seas_id = season_id or DEFAULT_SEASON_ID

        def fetch_matches():
            game_api = GameAPI(comp_id, seas_id)
            return game_api.getAllMatches()

        matches = await loop.run_in_executor(executor, fetch_matches)

        return {
            "competition_id": comp_id,
            "season_id": seas_id,
            "matches": matches[:limit] if matches else [],
            "total": len(matches) if matches else 0
        }

    except Exception as e:
        logger.error(f"Error fetching matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", summary="Search matches")
async def search_matches(
    team_id: Optional[str] = Query(None, description="Team ID filter"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    status: Optional[str] = Query(None, description="Match status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """Search for matches with filters"""
    try:
        loop = asyncio.get_event_loop()

        def search():
            game_api = get_game_api()
            # TODO: Implement search with filters
            # For now, return all matches
            return game_api.getAllMatches() or []

        matches = await loop.run_in_executor(executor, search)

        # Apply filters (simplified)
        filtered = matches[:limit]

        return {
            "filters": {
                "team_id": team_id,
                "start_date": start_date,
                "end_date": end_date,
                "status": status
            },
            "matches": filtered,
            "total": len(filtered)
        }

    except Exception as e:
        logger.error(f"Error searching matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Match Statistics Endpoints ============

@router.get("/{match_id}/stats", summary="Get match statistics")
async def get_match_stats(
    match_id: str = Path(..., description="Match ID")
):
    """Get comprehensive match statistics"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_stats():
            game_api = get_game_api()
            # TODO: Implement get match stats
            return {
                "match_id": match_id,
                "stats": {}
            }

        result = await loop.run_in_executor(executor, fetch_stats)
        return result

    except Exception as e:
        logger.error(f"Error fetching stats for match {match_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{match_id}/summary", summary="Get match summary")
async def get_match_summary(
    match_id: str = Path(..., description="Match ID")
):
    """Get match summary"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_summary():
            game_api = get_game_api()
            return game_api.getGameDataById(match_id)

        result = await loop.run_in_executor(executor, fetch_summary)
        return result

    except Exception as e:
        logger.error(f"Error fetching summary for match {match_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Live Match Endpoints ============

@router.get("/live", summary="Get live matches")
async def get_live_matches():
    """Get currently live matches"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_live():
            game_api = get_game_api()
            # TODO: Implement get live matches
            return []

        matches = await loop.run_in_executor(executor, fetch_live)

        return {
            "matches": matches,
            "total": len(matches)
        }

    except Exception as e:
        logger.error(f"Error fetching live matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{match_id}/live", summary="Get live match data")
async def get_match_live_data(
    match_id: str = Path(..., description="Match ID")
):
    """Get live data for a specific match"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_live_data():
            game_api = get_game_api()
            # TODO: Implement live data
            return {
                "match_id": match_id,
                "live": False,
                "minute": 0,
                "score": {"home": 0, "away": 0}
            }

        result = await loop.run_in_executor(executor, fetch_live_data)
        return result

    except Exception as e:
        logger.error(f"Error fetching live data for match {match_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Match Events Endpoints ============

@router.get("/{match_id}/events", summary="Get match events")
async def get_match_events(
    match_id: str = Path(..., description="Match ID"),
    event_type: Optional[str] = Query(None, description="Event type filter")
):
    """
    Get all events for a match

    Uses legacy EventAPI methods
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_events():
            event_api = get_event_api()
            # TODO: Implement getMatchEvents
            return []

        events = await loop.run_in_executor(executor, fetch_events)

        # Filter by type if specified
        if event_type and events:
            events = [e for e in events if e.get('type') == event_type]

        return {
            "match_id": match_id,
            "event_type": event_type,
            "events": events,
            "total": len(events)
        }

    except Exception as e:
        logger.error(f"Error fetching events for match {match_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}", summary="Get event by ID")
async def get_event_by_id(
    event_id: str = Path(..., description="Event ID")
):
    """
    Get specific event by ID

    Uses legacy EventAPI.getEventById() method
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_event():
            event_api = get_event_api()
            return event_api.getEventById(event_id)

        result = await loop.run_in_executor(executor, fetch_event)

        if not result:
            raise HTTPException(status_code=404, detail="Event not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching event {event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{match_id}/events/filter", summary="Get filtered match events")
async def get_filtered_events(
    match_id: str = Path(..., description="Match ID"),
    event_type: Optional[str] = Query(None, description="Event type"),
    team_id: Optional[str] = Query(None, description="Team ID"),
    player_id: Optional[str] = Query(None, description="Player ID"),
    period: Optional[int] = Query(None, ge=1, le=2, description="Period (1 or 2)")
):
    """Get filtered match events with multiple criteria"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_filtered():
            event_api = get_event_api()
            # TODO: Implement filtered events
            return []

        events = await loop.run_in_executor(executor, fetch_filtered)

        return {
            "match_id": match_id,
            "filters": {
                "event_type": event_type,
                "team_id": team_id,
                "player_id": player_id,
                "period": period
            },
            "events": events,
            "total": len(events)
        }

    except Exception as e:
        logger.error(f"Error fetching filtered events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Team-specific Match Data ============

@router.get("/by-team", summary="Get matches by team")
async def get_team_matches(
    team_id: str = Query(..., description="Team ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """Get all matches for a specific team"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_team_matches():
            game_api = get_game_api()
            all_matches = game_api.getAllMatches() or []
            # TODO: Filter by team_id
            return all_matches[:limit]

        matches = await loop.run_in_executor(executor, fetch_team_matches)

        return {
            "team_id": team_id,
            "matches": matches,
            "total": len(matches)
        }

    except Exception as e:
        logger.error(f"Error fetching matches for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Player-specific Match Data ============

@router.get("/{match_id}/players/{player_id}/stats", summary="Get player match stats")
async def get_player_match_stats(
    match_id: str = Path(..., description="Match ID"),
    player_id: str = Path(..., description="Player ID")
):
    """Get player statistics for a specific match"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_player_stats():
            # TODO: Implement player match stats
            return {
                "match_id": match_id,
                "player_id": player_id,
                "stats": {}
            }

        result = await loop.run_in_executor(executor, fetch_player_stats)
        return result

    except Exception as e:
        logger.error(f"Error fetching player stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Date Range Queries ============

@router.get("/date-range", summary="Get matches by date range")
async def get_matches_by_date_range(
    start_date: str = Query(..., description="Start date (ISO format)"),
    end_date: str = Query(..., description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """Get matches within a date range"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_by_date():
            game_api = get_game_api()
            # TODO: Implement date filtering
            return game_api.getAllMatches() or []

        matches = await loop.run_in_executor(executor, fetch_by_date)

        return {
            "start_date": start_date,
            "end_date": end_date,
            "matches": matches[:limit],
            "total": len(matches)
        }

    except Exception as e:
        logger.error(f"Error fetching matches by date range: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Season Data ============

@router.get("/season", summary="Get season matches")
async def get_season_matches(
    competition_id: int = Query(..., description="Competition ID"),
    season_id: int = Query(..., description="Season ID")
):
    """Get all matches for a season"""
    try:
        loop = asyncio.get_event_loop()

        def fetch_season_matches():
            game_api = GameAPI(competition_id, season_id)
            return game_api.getAllMatches() or []

        matches = await loop.run_in_executor(executor, fetch_season_matches)

        return {
            "competition_id": competition_id,
            "season_id": season_id,
            "matches": matches,
            "total": len(matches)
        }

    except Exception as e:
        logger.error(f"Error fetching season matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/season/events", summary="Get all season game events")
async def get_all_season_game_events(
    team_id: str = Query(..., description="Team ID"),
    player_id: Optional[str] = Query(None, description="Player ID filter")
):
    """
    Get all game events for a season

    Uses legacy GameAPI.getAllSeasonGameEvents() method
    """
    try:
        loop = asyncio.get_event_loop()

        def fetch_season_events():
            game_api = get_game_api()
            return game_api.getAllSeasonGameEvents(team_id, player_id) if hasattr(game_api, 'getAllSeasonGameEvents') else []

        events = await loop.run_in_executor(executor, fetch_season_events)

        return {
            "team_id": team_id,
            "player_id": player_id,
            "events": events or [],
            "total": len(events) if events else 0
        }

    except Exception as e:
        logger.error(f"Error fetching season events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
