"""LLM router — selects provider and model based on reasoning tier."""

from __future__ import annotations

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
