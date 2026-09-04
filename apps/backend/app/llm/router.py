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
        "gemini": "gemini",
    }
    hint = model_hint.lower()
    if hint in aliases:
        return aliases[hint]
    return hint


async def stream_chat(
    *,
    system: str,
    user: str,
    messages: list[dict[str, str]] | None = None,
    model_hint: str = "balanced",
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> AsyncIterator[str]:
    """Route one streaming request to the provider selected by the model hint."""
    provider = _resolve_provider(model_hint)

    from collections.abc import Callable

    provider_stream: Callable[..., AsyncIterator[str]]
    if provider == "ollama":
        from app.llm.providers.ollama import stream_chat as ollama_stream
        provider_stream = ollama_stream
    elif provider == "openai":
        from app.llm.providers.openai import stream_chat as openai_stream
        provider_stream = openai_stream
    elif provider == "anthropic":
        from app.llm.providers.anthropic import stream_chat as anthropic_stream
        provider_stream = anthropic_stream
    else:
        from app.llm.providers.gemini import stream_chat as gemini_stream
        provider_stream = gemini_stream

    async for token in provider_stream(
        system=system,
        user=user,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    ):
        yield token


async def complete_chat(
    *,
    system: str,
    user: str,
    messages: list[dict[str, str]] | None = None,
    model_hint: str = "fast",
    temperature: float = 0.1,
    max_tokens: int = 1024,
) -> str:
    """Accumulate stream_chat tokens and return complete string response."""
    tokens = []
    async for tok in stream_chat(
        system=system,
        user=user,
        messages=messages,
        model_hint=model_hint,
        temperature=temperature,
        max_tokens=max_tokens,
    ):
        tokens.append(tok)
    return "".join(tokens).strip()

