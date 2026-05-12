"""OpenAI provider wrapper."""
from __future__ import annotations

from typing import AsyncIterator


async def chat_stream(prompt: str, model: str = "gpt-4o-mini") -> AsyncIterator[str]:
    """Stream tokens from OpenAI Chat Completions."""
    # TODO: use openai AsyncOpenAI client
    yield ""
