"""Anthropic Claude provider wrapper."""
from __future__ import annotations

from typing import AsyncIterator


async def chat_stream(prompt: str, model: str = "claude-sonnet-4-6") -> AsyncIterator[str]:
    """Stream tokens from Anthropic Messages API."""
    # TODO: use anthropic AsyncAnthropic client with streaming
    yield ""
