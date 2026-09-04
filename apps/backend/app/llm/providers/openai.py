"""OpenAI provider — GPT-4.5 for IFRS reasoning and mapping."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o"
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def stream_chat(
    *,
    system: str,
    user: str,
    messages: list[dict[str, str]] | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> AsyncIterator[str]:
    """Stream tokens from OpenAI Chat Completions API."""
    client = _get_client()
    
    api_messages = [{"role": "system", "content": system}]
    if messages:
        api_messages.extend(messages)
    api_messages.append({"role": "user", "content": user})
    
    stream = await client.chat.completions.create(
        model=model,
        stream=True,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=api_messages,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta
