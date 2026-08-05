"""LLM router — selects provider and model based on reasoning tier."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Literal

ReasoningTier = Literal["fast", "balanced", "deep"]


def get_provider(tier: ReasoningTier) -> str:
    """Return the provider name for the given reasoning tier."""
    mapping: dict[ReasoningTier, str] = {
        "fast": "ollama",
        "balanced": "openai",
        "deep": "anthropic",
    }
    return mapping[tier]


def _resolve_provider(model_hint: str) -> str:
    aliases = {
        "fast": "ollama",
        "qwen": "ollama",
        "ollama": "ollama",
        "balanced": "openai",
        "openai": "openai",
        "deep": "anthropic",
        "claude": "anthropic",
        "anthropic": "anthropic",
    }
    try:
        return aliases[model_hint]
    except KeyError as exc:
        raise ValueError(f"Unsupported LLM model hint: {model_hint}") from exc


async def stream_chat(
    *,
    system: str,
    user: str,
    model_hint: str = "balanced",
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> AsyncIterator[str]:
    """Route one streaming request to the provider selected by the model hint."""
    provider = _resolve_provider(model_hint)

    if provider == "ollama":
        from app.llm.providers.ollama import stream_chat as provider_stream
    elif provider == "openai":
        from app.llm.providers.openai import stream_chat as provider_stream
    else:
        from app.llm.providers.anthropic import stream_chat as provider_stream

    async for token in provider_stream(
        system=system,
        user=user,
        temperature=temperature,
        max_tokens=max_tokens,
    ):
        yield token
