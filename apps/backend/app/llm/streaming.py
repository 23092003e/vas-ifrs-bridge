"""SSE streaming helpers for LLM token events."""
from __future__ import annotations

from typing import AsyncIterator


async def stream_tokens(provider_stream: AsyncIterator[str]) -> AsyncIterator[str]:
    """Convert raw provider token chunks to SSE-formatted strings."""
    async for token in provider_stream:
        yield f"data: {token}\n\n"
