from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.agents import gl_mapping_agent, ifrs_compare_agent, retrieval_agent


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

    monkeypatch.setattr(module, "retrieve" if module is ifrs_compare_agent else "retrieve_multi", fake_multi)
    monkeypatch.setattr(module, "_call_llm", fake_llm)
    monkeypatch.setattr("app.rag.retriever.retrieve", fake_direct)

    events = [event async for event in agent_type().arun(query="VAS và IFRS")]

    assert events
    assert direct_calls == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(("module", "agent_type", "retrieve_name", "provider_name"), [
    (retrieval_agent, retrieval_agent.RetrievalAgent, "retrieve", "_stream_llm"),
    (ifrs_compare_agent, ifrs_compare_agent.IFRSCompareAgent, "retrieve", "_call_llm"),
])
async def test_no_sources_bypasses_model(
    module: Any, agent_type: Any, retrieve_name: str, provider_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def empty(*_: Any, **__: Any) -> list[Any]:
        return []

    async def provider(*_: Any) -> AsyncIterator[str]:
        pytest.fail("Model must not run without source evidence")
        yield ""

    monkeypatch.setattr(module, retrieve_name, empty)
    monkeypatch.setattr(module, provider_name, provider)
    events = [json.loads(e.removeprefix("data: ")) async for e in
              agent_type().arun(query="Fixture without evidence", scope="shared", lang="en")]

    assert len(events) == 1 and events[0]["type"] == "final"
    assert "source" in events[0]["content"]
