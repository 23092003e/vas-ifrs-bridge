"""Account mapping rule schemas."""

from __future__ import annotations

from pydantic import UUID4, BaseModel


class MappingRule(BaseModel):
    id: UUID4
    vas_code: str
    ifrs_code: str
    confidence: float = 1.0
    source: str = "manual"
