from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import networkx as nx
import pytest

from app.agents import retrieval_agent


async def _empty_llm(*_: Any, **__: Any) -> AsyncIterator[str]:
    if False:
        yield ""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scope", "expected_collections"),
    [
        (
            "shared",
            {
                "kb_shared_mapping",
                "kb_shared_vas",
                "kb_shared_ifrs",
                "kb_shared_guidance",
            },
        ),
        ("tenant", {"tenant_174c7f5b"}),
    ],
)
async def test_retrieval_scope_controls_queried_collections(
    scope: str,
    expected_collections: set[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queried: list[str] = []

    async def fake_retrieve(*_: Any, collection: str, **__: Any) -> list[Any]:
        queried.append(collection)
        return []

    async def fake_rerank(*_: Any, **__: Any) -> list[Any]:
        return []

    monkeypatch.setattr(retrieval_agent, "retrieve", fake_retrieve)
    monkeypatch.setattr(retrieval_agent, "_stream_llm", _empty_llm)
    monkeypatch.setattr("app.rag.reranker.rerank", fake_rerank)
    monkeypatch.setattr("app.rag.graph_service.get_graph", lambda: nx.DiGraph())
    monkeypatch.setattr("app.rag.ontology_service.load_ontology", lambda: None)
    monkeypatch.setattr("app.rag.ontology_service.detect_topics", lambda _: [])
    monkeypatch.setattr("app.rag.ontology_service.get_standards_for_topics", lambda _: [])
    monkeypatch.setattr("app.rag.ontology_service.expand_query", lambda query, _: query)

    agent = retrieval_agent.RetrievalAgent()
    events = [
        event
        async for event in agent.arun(
            query="VAS 01",
            scope=scope,
            tenant_id="174c7f5b-2cb9-4746-b1a7-b0c5e42591d1",
            tenant_collection="tenant_174c7f5b",
        )
    ]

    assert events
    assert set(queried) == expected_collections


@pytest.mark.asyncio
async def test_llm_provider_errors_are_not_converted_to_user_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_stream(*_: Any, **__: Any) -> AsyncIterator[str]:
        raise RuntimeError("api_key=do-not-leak")
        yield

    monkeypatch.setattr("app.llm.router.stream_chat", failing_stream)

    with pytest.raises(RuntimeError, match="do-not-leak"):
        _ = [token async for token in retrieval_agent._stream_llm("user", "system", "fast")]
