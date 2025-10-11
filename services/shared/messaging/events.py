"""
Event Schemas for Kafka Event Streaming
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, Literal
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Event type enumeration"""
    # Player events
    PLAYER_CREATED = "player.created"
    PLAYER_UPDATED = "player.updated"
    PLAYER_STATS_UPDATED = "player.stats.updated"
    PLAYER_TRANSFERRED = "player.transferred"

    # Team events
    TEAM_CREATED = "team.created"
    TEAM_UPDATED = "team.updated"
    TEAM_STATS_UPDATED = "team.stats.updated"
    TEAM_SQUAD_UPDATED = "team.squad.updated"
    TEAM_STANDINGS_UPDATED = "team.standings.updated"

    # Match events
    MATCH_CREATED = "match.created"
    MATCH_STARTED = "match.started"
    MATCH_UPDATED = "match.updated"
    MATCH_ENDED = "match.ended"
    MATCH_EVENT_CREATED = "match.event.created"

    # Match event types (live)
    GOAL_SCORED = "match.goal"
    ASSIST_MADE = "match.assist"
    CARD_ISSUED = "match.card"
    SUBSTITUTION_MADE = "match.substitution"
    SHOT_TAKEN = "match.shot"
    PASS_COMPLETED = "match.pass"

    # Statistics events
    STATS_AGGREGATED = "stats.aggregated"
    STATS_CALCULATED = "stats.calculated"

    # ML events
    ML_PREDICTION_REQUESTED = "ml.prediction.requested"
    ML_PREDICTION_COMPLETED = "ml.prediction.completed"
    ML_MODEL_TRAINED = "ml.model.trained"
    ML_MODEL_DEPLOYED = "ml.model.deployed"

    # Search events
    SEARCH_INDEX_UPDATED = "search.index.updated"
    SEARCH_REINDEX_REQUESTED = "search.reindex.requested"


class Event(BaseModel):
    """Base event schema"""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Event type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    version: str = Field(default="1.0", description="Event schema version")
    source_service: str = Field(..., description="Service that generated the event")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")
    data: Dict[str, Any] = Field(..., description="Event payload data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PlayerEvent(Event):
    """Player-specific event"""
    source_service: Literal["player-service"] = "player-service"

    @property
    def player_id(self) -> Optional[str]:
        """Extract player ID from data"""
        return self.data.get("player_id")

    @property
    def team_id(self) -> Optional[str]:
        """Extract team ID from data"""
        return self.data.get("team_id")


class TeamEvent(Event):
    """Team-specific event"""
    source_service: Literal["team-service"] = "team-service"

    @property
    def team_id(self) -> Optional[str]:
        """Extract team ID from data"""
        return self.data.get("team_id")

    @property
    def competition_id(self) -> Optional[str]:
        """Extract competition ID from data"""
        return self.data.get("competition_id")


class MatchEvent(Event):
    """Match-specific event"""
    source_service: Literal["match-service"] = "match-service"

    @property
    def match_id(self) -> Optional[str]:
        """Extract match ID from data"""
        return self.data.get("match_id")

    @property
    def home_team_id(self) -> Optional[str]:
        """Extract home team ID from data"""
        return self.data.get("home_team_id")

    @property
    def away_team_id(self) -> Optional[str]:
        """Extract away team ID from data"""
        return self.data.get("away_team_id")

    @property
    def minute(self) -> Optional[int]:
        """Extract match minute from data (for live events)"""
        return self.data.get("minute")


class StatisticsEvent(Event):
    """Statistics-specific event"""
    source_service: Literal["statistics-service"] = "statistics-service"

    @property
    def entity_type(self) -> Optional[str]:
        """Extract entity type (player/team/match) from data"""
        return self.data.get("entity_type")

    @property
    def entity_id(self) -> Optional[str]:
        """Extract entity ID from data"""
        return self.data.get("entity_id")


class MLEvent(Event):
    """ML-specific event"""
    source_service: Literal["ml-service"] = "ml-service"

    @property
    def model_id(self) -> Optional[str]:
        """Extract model ID from data"""
        return self.data.get("model_id")

    @property
    def prediction_id(self) -> Optional[str]:
        """Extract prediction ID from data"""
        return self.data.get("prediction_id")


class SearchEvent(Event):
    """Search-specific event"""
    source_service: Literal["search-service"] = "search-service"

    @property
    def index_name(self) -> Optional[str]:
        """Extract index name from data"""
        return self.data.get("index_name")

    @property
    def document_id(self) -> Optional[str]:
        """Extract document ID from data"""
        return self.data.get("document_id")


# Event factory for creating typed events
def create_event(
    event_type: EventType,
    data: Dict[str, Any],
    source_service: str,
    event_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Event:
    """
    Factory function to create appropriate event type

    Args:
        event_type: Type of event
        data: Event payload
        source_service: Service generating the event
        event_id: Optional event ID (auto-generated if not provided)
        correlation_id: Optional correlation ID for tracing
        metadata: Optional metadata

    Returns:
        Appropriate Event subclass instance
    """
    import uuid

    event_id = event_id or str(uuid.uuid4())

    event_data = {
        "event_id": event_id,
        "event_type": event_type,
        "source_service": source_service,
        "data": data,
        "correlation_id": correlation_id,
        "metadata": metadata or {}
    }

    # Determine event class based on source service
    if source_service == "player-service":
        return PlayerEvent(**event_data)
    elif source_service == "team-service":
        return TeamEvent(**event_data)
    elif source_service == "match-service":
        return MatchEvent(**event_data)
    elif source_service == "statistics-service":
        return StatisticsEvent(**event_data)
    elif source_service == "ml-service":
        return MLEvent(**event_data)
    elif source_service == "search-service":
        return SearchEvent(**event_data)
    else:
        return Event(**event_data)
