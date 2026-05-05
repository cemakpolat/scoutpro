"""
Team API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
import sys
sys.path.append('/app')
from shared.models.base import Team, APIResponse
from services.team_service import TeamService
from dependencies import get_team_service, get_mongo_db
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/teams", tags=["teams"])


def _collect_identifier_variants(value: Any, prefix: str = 't') -> tuple[list[str], list[int]]:
    string_values: list[str] = []
    numeric_values: list[int] = []

    if value in (None, ''):
        return string_values, numeric_values

    raw_value = str(value).strip()
    if not raw_value:
        return string_values, numeric_values

    def add_string(candidate: str) -> None:
        if candidate and candidate not in string_values:
            string_values.append(candidate)

    def add_number(candidate: int) -> None:
        if candidate not in numeric_values:
            numeric_values.append(candidate)

    add_string(raw_value)

    stripped_value = raw_value
    if prefix and raw_value.lower().startswith(prefix.lower()):
        stripped_value = raw_value[1:]
        add_string(stripped_value)

    if stripped_value.isdigit():
        add_number(int(stripped_value))
        if prefix:
            add_string(f'{prefix}{stripped_value}')

    return string_values, numeric_values


def _build_lookup_clauses(
    string_values: List[str],
    numeric_values: List[int],
    fields: List[str],
) -> List[Dict[str, Any]]:
    clauses: List[Dict[str, Any]] = []
    for field in fields:
        if string_values:
            clauses.append({field: {'$in': string_values}})
        if numeric_values:
            clauses.append({field: {'$in': numeric_values}})
    return clauses


@router.get("", response_model=APIResponse)
async def list_teams(
    country: Optional[str] = Query(None),
    league: Optional[str] = Query(None),
    competition_id: Optional[int] = Query(None),
    limit: int = Query(100, le=500),
    service: TeamService = Depends(get_team_service)
):
    """List teams with filters"""
    filters = {}

    if country:
        filters['country'] = country
    if league:
        filters['league'] = league
    if competition_id:
        filters['competition_id'] = competition_id

    teams = await service.list_teams(filters, limit)

    return APIResponse(
        success=True,
        data=[t.dict() for t in teams],
        message=f"Retrieved {len(teams)} teams"
    )


@router.get("/search", response_model=APIResponse)
async def search_teams(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
    service: TeamService = Depends(get_team_service)
):
    """Search teams by name"""
    teams = await service.search_teams(q, limit)

    return APIResponse(
        success=True,
        data=[t.dict() for t in teams],
        message=f"Found {len(teams)} teams matching '{q}'"
    )


@router.get("/{team_id}", response_model=APIResponse)
async def get_team(
    team_id: str,
    service: TeamService = Depends(get_team_service)
):
    """Get team by ID"""
    team = await service.get_team(team_id)

    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

    return APIResponse(
        success=True,
        data=team.dict(),
        message="Team retrieved successfully"
    )


@router.get("/{team_id}/squad", response_model=APIResponse)
async def get_squad(
    team_id: str,
    service: TeamService = Depends(get_team_service)
):
    """Get team squad"""
    squad = await service.get_squad(team_id)

    return APIResponse(
        success=True,
        data=squad,
        message=f"Retrieved squad for team {team_id}"
    )


@router.get("/{team_id}/events", response_model=APIResponse)
async def get_team_events(
    team_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type (pass, shot, tackle, etc.)"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """
    Get all events for a team across all their matches.
    
    Returns events where the team was involved (all events in team's home/away matches).
    Optionally filter by event type.
    """
    try:
        events_collection = db['match_events']
        matches_collection = db['matches']
        teams_collection = db['teams']

        team_string_values, team_numeric_values = _collect_identifier_variants(team_id)

        team_lookup = _build_lookup_clauses(
            team_string_values,
            team_numeric_values,
            ['uID', 'provider_ids.opta', 'id', 'scoutpro_id'],
        )
        team_doc = await teams_collection.find_one(
            {'$or': team_lookup} if team_lookup else {'uID': team_id},
            {'_id': 0, 'uID': 1, 'id': 1, 'scoutpro_id': 1, 'provider_ids': 1},
        )

        if team_doc:
            for candidate in (
                team_doc.get('uID'),
                team_doc.get('id'),
                team_doc.get('scoutpro_id'),
                (team_doc.get('provider_ids') or {}).get('opta'),
            ):
                strings, numbers = _collect_identifier_variants(candidate)
                for value in strings:
                    if value not in team_string_values:
                        team_string_values.append(value)
                for value in numbers:
                    if value not in team_numeric_values:
                        team_numeric_values.append(value)
        
        # First, find all match IDs where this team played
        match_lookup = _build_lookup_clauses(
            team_string_values,
            team_numeric_values,
            [
                'homeTeamID',
                'awayTeamID',
                'home_team_id',
                'away_team_id',
                'home_team_ref',
                'away_team_ref',
                'home_opta_team_id',
                'away_opta_team_id',
            ],
        )

        cursor = matches_collection.find(
            {'$or': match_lookup} if match_lookup else {'homeTeamID': team_id}
        ).project({
            'matchID': 1,
            'match_id': 1,
            'uID': 1,
            'id': 1,
            'scoutpro_id': 1,
            'provider_ids': 1,
        })
        matches = await cursor.to_list(length=None)

        match_string_values: List[str] = []
        match_numeric_values: List[int] = []
        for match in matches:
            for candidate in (
                match.get('matchID'),
                match.get('match_id'),
                match.get('uID'),
                match.get('id'),
                match.get('scoutpro_id'),
                (match.get('provider_ids') or {}).get('opta'),
            ):
                strings, numbers = _collect_identifier_variants(candidate, prefix='g')
                for value in strings:
                    if value not in match_string_values:
                        match_string_values.append(value)
                for value in numbers:
                    if value not in match_numeric_values:
                        match_numeric_values.append(value)
        
        if not match_string_values and not match_numeric_values:
            return APIResponse(
                success=True,
                data=[],
                message=f"No matches found for team {team_id}"
            )
        
        # Now get all events from those matches
        event_clauses = _build_lookup_clauses(
            match_string_values,
            match_numeric_values,
            ['matchID', 'match_id', 'scoutpro_match_id'],
        )
        event_query: Dict[str, Any] = {
            '$or': event_clauses
        }
        
        if event_type:
            event_query['type_name'] = event_type
        
        cursor = events_collection.find(event_query).sort('timestamp', 1).limit(limit)
        events = await cursor.to_list(length=limit)
        
        # Clean response
        for event in events:
            event.pop('_id', None)
        
        return APIResponse(
            success=True,
            data=events,
            message=f"Retrieved {len(events)} events for team {team_id}"
        )
    except Exception as e:
        logger.error(f"Error getting team events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=APIResponse, status_code=201)
async def create_team(
    team: Team,
    service: TeamService = Depends(get_team_service)
):
    """Create new team"""
    try:
        team_id = await service.create_team(team)

        return APIResponse(
            success=True,
            data={"team_id": team_id},
            message="Team created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{team_id}", response_model=APIResponse)
async def update_team(
    team_id: str,
    team: Team,
    service: TeamService = Depends(get_team_service)
):
    """Update team"""
    try:
        success = await service.update_team(team_id, team)

        if not success:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

        return APIResponse(
            success=True,
            message="Team updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
