"""Canonical competition model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ScoutProCompetition:
    """Provider-agnostic competition model."""

    id: int
    external_id: str
    provider: str
    name: str
    country: Optional[str] = None
    gender: Optional[str] = None
    type: Optional[str] = None
    current_season_id: Optional[int] = None
    provider_ids: Dict[str, str] = field(default_factory=dict)
    provider_data: Dict[str, Any] = field(default_factory=dict)
    data_quality: Dict[str, Any] = field(default_factory=dict)
    scoutpro_metadata: Dict[str, Any] = field(default_factory=dict)
    season_ids: List[int] = field(default_factory=list)
    conflicts: Optional[list] = None
    merge_info: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scoutpro_id": self.id,
            "external_id": self.external_id,
            "provider": self.provider,
            "name": self.name,
            "country": self.country,
            "gender": self.gender,
            "type": self.type,
            "current_season_id": self.current_season_id,
            "provider_ids": self.provider_ids,
            "provider_data": self.provider_data,
            "data_quality": self.data_quality,
            "scoutpro_metadata": self.scoutpro_metadata,
            "season_ids": self.season_ids,
            "conflicts": self.conflicts,
            "merge_info": self.merge_info,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoutProCompetition":
        if "scoutpro_id" in data:
            data["id"] = data.pop("scoutpro_id")
        return cls(**data)