from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.agents import gl_mapping_agent, ifrs_compare_agent


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("module", "agent_type"),
    [
        (ifrs_compare_agent, ifrs_compare_agent.IFRSCompareAgent),
        (gl_mapping_agent, gl_mapping_agent.GLMappingAgent),
    ],
)
async def test_specialized_agent_does_not_query_ifrs_twice(
    module: Any,
    agent_type: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    direct_calls = 0

    async def fake_multi(*_: Any, **__: Any) -> list[Any]:
        return []

    async def fake_direct(*_: Any, **__: Any) -> list[Any]:
        nonlocal direct_calls
        direct_calls += 1
        return []

    async def fake_llm(*_: Any, **__: Any) -> AsyncIterator[str]:
        if False:
            yield ""

    monkeypatch.setattr(module, "retrieve_multi", fake_multi)
    monkeypatch.setattr(module, "_call_llm", fake_llm)
    monkeypatch.setattr("app.rag.retriever.retrieve", fake_direct)

    events = [event async for event in agent_type().arun(query="VAS và IFRS")]

    assert events
    assert direct_calls == 0
