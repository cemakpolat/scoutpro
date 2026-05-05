"""
Shared domain models for ScoutPro services
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PositionEnum(str, Enum):
    GOALKEEPER = "Goalkeeper"
    DEFENDER = "Defender"
    MIDFIELDER = "Midfielder"
    FORWARD = "Forward"


class Player(BaseModel):
    # ─── Canonical golden-record ID ──────────────────────────────────────────
    # Stable, provider-agnostic UUID-5 generated from "opta:<numeric_uid>".
    # This is the primary key used everywhere inside ScoutPro.
    id: str = Field(alias="scoutpro_id")

    # ─── Provider references ──────────────────────────────────────────────────
    # Cross-provider ID map:  {"opta": "p184522", "statsbomb": "12345"}
    # Used to join F1/F9/F24/F40 by opta ID, StatsBomb CSV by sb ID.
    provider_ids: Dict[str, str] = Field(default_factory=dict)

    # ─── Legacy Opta uID — kept for internal joins / backward compat ──────────
    opta_uid: Optional[str] = Field(None, alias="uID")

    name: str
    first_name: Optional[str] = Field(None, alias="first")
    last_name: Optional[str] = Field(None, alias="last")
    position: Optional[str] = None
    age: Optional[int] = None
    nationality: Optional[str] = None
    club: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    shirt_number: Optional[int] = Field(None, alias="shirtNumber")
    preferred_foot: Optional[str] = Field(None, alias="preferredFoot")
    birth_date: Optional[str] = Field(None, alias="birthDate")
    team_name: Optional[str] = Field(None, alias="teamName")
    team_id: Optional[str] = Field(None, alias="teamID")
    position: Optional[str] = None
    detailed_position: Optional[str] = Field(None, alias="detailedPosition")
    raw_position: Optional[str] = Field(None, alias="rawPosition")

    # StatsBomb enrichment — populated by the StatsBomb enrichment pipeline
    # Contains: total_xg, total_obv, passes, shots, goals, avg_pass_success_prob, match_id
    statsbomb_enrichment: Optional[Dict[str, Any]] = Field(None, alias="statsbombEnrichment")

    # Coerce numeric height/weight to str (MongoDB may store them as int)
    @field_validator('height', 'weight', mode='before')
    @classmethod
    def coerce_numeric_to_str(cls, v):
        if v is not None and not isinstance(v, str):
            return str(v)
        return v

    # Coerce numeric opta_uid / team_id to str
    @field_validator('opta_uid', 'team_id', mode='before')
    @classmethod
    def coerce_id_to_str(cls, v):
        if v is not None and not isinstance(v, str):
            return str(v)
        return v

    # Coerce string shirt_number to int
    @field_validator('shirt_number', mode='before')
    @classmethod
    def coerce_shirt_number(cls, v):
        if v is not None and isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        return v

    # Coerce datetime birth_date to ISO format string
    @field_validator('birth_date', mode='before')
    @classmethod
    def coerce_birth_date(cls, v):
        if v is not None:
            if isinstance(v, str):
                return v
            # Handle datetime objects
            if hasattr(v, 'isoformat'):
                return v.isoformat()
            return str(v)
        return v

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
    home_team_name: Optional[str] = Field(None, alias="homeTeamName")
    away_team_name: Optional[str] = Field(None, alias="awayTeamName")
    home_score: int = Field(0, alias="homeScore")
    away_score: int = Field(0, alias="awayScore")
    date: Optional[str] = None
    status: str = "scheduled"  # scheduled, live, finished
    match_day: Optional[int] = Field(None, alias="matchDay")
    competition_id: Optional[str] = Field(None, alias="competitionID")
    season_id: Optional[str] = Field(None, alias="seasonID")
    venue: Optional[str] = None
    competition: Optional[str] = None

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
