from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.agents.orchestrator import _select_model
from app.llm import router


@pytest.mark.parametrize(
    ("intent", "reasoning", "expected_provider"),
    [
        ("compare", "fast", "ollama"),
        ("mapping", "balanced", "openai"),
        ("qa", "deep", "anthropic"),
    ],
)
def test_reasoning_tier_selects_provider_independently_of_intent(
    intent: str,
    reasoning: str,
    expected_provider: str,
) -> None:
    assert _select_model(intent, reasoning) == expected_provider


@pytest.mark.asyncio
async def test_router_streams_from_selected_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    assert hasattr(router, "stream_chat"), "LLM router must expose the shared streaming gateway"

    called: list[str] = []

    async def fake_openai(*_: Any, **__: Any) -> AsyncIterator[str]:
        called.append("openai")
        yield "token"

    monkeypatch.setattr("app.llm.providers.openai.stream_chat", fake_openai)

    tokens = [
        token
        async for token in router.stream_chat(
            system="system",
            user="user",
            model_hint="openai",
        )
    ]

    assert called == ["openai"]
    assert tokens == ["token"]
