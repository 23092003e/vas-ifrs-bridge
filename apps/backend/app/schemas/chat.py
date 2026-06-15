"""Chat request and streaming event schemas."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: UUID | None = None
    content: str
    lang: Literal["vi", "en", "auto"] = "auto"
    intent_hint: Literal["qa", "compare", "mapping", "report", "adjustment"] | None = None
    reasoning: Literal["fast", "balanced", "deep"] = "balanced"
    scope: Literal["shared", "tenant", "both"] = "both"


class ChatTokenEvent(BaseModel):
    type: Literal["token"]
    delta: str


class ChatCitationEvent(BaseModel):
    type: Literal["citation"]
    key: str
    doc_id: UUID
    chunk_id: UUID
    snippet: str
    standard_code: str | None = None
