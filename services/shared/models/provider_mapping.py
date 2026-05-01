"""Canonical provider mapping models."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ProviderMapping(BaseModel):
    canonical_id: str
    entity_type: str
    provider: str
    provider_id: str
    display_name: Optional[str] = None
    source_match_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
