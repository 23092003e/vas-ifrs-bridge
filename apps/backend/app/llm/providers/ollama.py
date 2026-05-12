"""Ollama local LLM provider wrapper."""
from __future__ import annotations

from typing import AsyncIterator


async def chat_stream(prompt: str, model: str = "qwen2.5:14b") -> AsyncIterator[str]:
    """Stream tokens from a local Ollama model."""
    # TODO: call Ollama REST API via httpx
    yield ""
