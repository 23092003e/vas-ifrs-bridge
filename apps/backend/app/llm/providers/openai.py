"""OpenAI provider — GPT-4.5 for IFRS reasoning and mapping."""
from __future__ import annotations

import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4.5-preview"
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
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> AsyncIterator[str]:
    """Stream tokens from OpenAI Chat Completions API."""
    client = _get_client()
    stream = await client.chat.completions.create(
        model=model,
        stream=True,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta
