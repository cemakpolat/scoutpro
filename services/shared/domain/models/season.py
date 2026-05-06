"""Canonical season model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ScoutProSeason:
    """Provider-agnostic competition season model."""

    id: int
    external_id: str
    provider: str
    name: str
    competition_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    year: Optional[int] = None
    provider_ids: Dict[str, str] = field(default_factory=dict)
    provider_data: Dict[str, Any] = field(default_factory=dict)
    data_quality: Dict[str, Any] = field(default_factory=dict)
    scoutpro_metadata: Dict[str, Any] = field(default_factory=dict)
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
            "competition_id": self.competition_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "year": self.year,
            "provider_ids": self.provider_ids,
            "provider_data": self.provider_data,
            "data_quality": self.data_quality,
            "scoutpro_metadata": self.scoutpro_metadata,
            "conflicts": self.conflicts,
            "merge_info": self.merge_info,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoutProSeason":
        if "scoutpro_id" in data:
            data["id"] = data.pop("scoutpro_id")
        return cls(**data)