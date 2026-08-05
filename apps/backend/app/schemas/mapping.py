"""Account mapping rule schemas."""

from __future__ import annotations

from pydantic import UUID4, BaseModel, Field


class MappingRule(BaseModel):
    id: UUID4
    vas_code: str
    ifrs_code: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = "manual"
