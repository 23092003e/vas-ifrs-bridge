"""Anthropic Claude provider — Sonnet/Opus for long-context synthesis."""
from __future__ import annotations

import logging
from typing import AsyncIterator

import anthropic

from app.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-6"
DEEP_MODEL = "claude-opus-4-7"
_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def stream_chat(
    *,
    system: str,
    user: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    max_tokens: int = 8192,
    extended_thinking: bool = False,
    thinking_budget: int = 8000,
) -> AsyncIterator[str]:
    """Stream tokens from Anthropic Messages API."""
    client = _get_client()

    kwargs: dict = dict(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature if not extended_thinking else 1,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    if extended_thinking:
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
        kwargs.pop("temperature", None)

    async with client.messages.stream(**kwargs) as stream:
        async for text in stream.text_stream:
            yield text
