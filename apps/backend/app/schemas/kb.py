"""Knowledge base document and chunk schemas."""

from __future__ import annotations

from pydantic import UUID4, BaseModel, Field


class KBDocument(BaseModel):
    id: UUID4
    tenant_id: str
    filename: str
    collection: str
    chunk_count: int = 0


class KBChunk(BaseModel):
    id: UUID4
    document_id: UUID4
    content: str
    embedding: list[float] | None = None
    metadata: dict = Field(default_factory=dict)
