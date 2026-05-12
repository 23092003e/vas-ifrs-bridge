"""Chat request and streaming event schemas."""
from __future__ import annotations

from pydantic import BaseModel, UUID4
from typing import Literal


class ChatRequest(BaseModel):
    conversation_id: UUID4 | None = None
    content: str
    lang: Literal["vi", "en", "auto"] = "auto"
    intent_hint: Literal["qa", "compare", "mapping", "report"] | None = None
    reasoning: Literal["fast", "balanced", "deep"] = "balanced"
    scope: Literal["shared", "tenant", "both"] = "both"


class ChatTokenEvent(BaseModel):
    type: Literal["token"]
    delta: str


class ChatCitationEvent(BaseModel):
    type: Literal["citation"]
    key: str
    doc_id: UUID4
    chunk_id: UUID4
    snippet: str
    standard_code: str | None = None
