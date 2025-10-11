"""
Shared domain models for ScoutPro services
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PositionEnum(str, Enum):
    GOALKEEPER = "Goalkeeper"
    DEFENDER = "Defender"
    MIDFIELDER = "Midfielder"
    FORWARD = "Forward"


class Player(BaseModel):
    id: str = Field(alias="uID")
    name: str
    first_name: Optional[str] = Field(None, alias="first")
    last_name: Optional[str] = Field(None, alias="last")
    position: str
    age: Optional[int] = None
    nationality: Optional[str] = None
    club: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    shirt_number: Optional[int] = Field(None, alias="shirtNumber")

    class Config:
        populate_by_name = True
        from_attributes = True


class Team(BaseModel):
    id: str = Field(alias="uID")
    name: str
    short_name: Optional[str] = Field(None, alias="shortName")
    country: Optional[str] = None
    founded: Optional[int] = None
    stadium: Optional[str] = None
    capacity: Optional[int] = None
    manager: Optional[str] = None

    class Config:
        populate_by_name = True
        from_attributes = True


class Match(BaseModel):
    id: str = Field(alias="uID")
    home_team_id: str = Field(alias="homeTeamID")
    away_team_id: str = Field(alias="awayTeamID")
    home_score: int = Field(0, alias="homeScore")
    away_score: int = Field(0, alias="awayScore")
    date: str
    status: str = "scheduled"  # scheduled, live, finished
    competition_id: Optional[int] = Field(None, alias="competitionID")
    season_id: Optional[int] = Field(None, alias="seasonID")
    venue: Optional[str] = None

    class Config:
        populate_by_name = True
        from_attributes = True


class PlayerStatistics(BaseModel):
    player_id: str
    player_name: Optional[str] = None
    competition_id: Optional[int] = None
    season_id: Optional[int] = None
    stats: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class APIError(BaseModel):
    success: bool = False
    error: Dict[str, Any]
