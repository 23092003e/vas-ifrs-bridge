from __future__ import annotations

import json
from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import networkx as nx
import pytest

from app.agents import retrieval_agent
from app.core.errors import QdrantUnavailableError
from app.rag.retriever import RetrievedChunk


@pytest.mark.asyncio
@pytest.mark.parametrize("direct_hit", [True, False])
async def test_graph_expansion_passes_full_text_to_prompt(
    monkeypatch: pytest.MonkeyPatch, direct_hit: bool,
) -> None:
    preview = "Opening."
    full_text = f"{preview} Material exception."
    graph = nx.DiGraph()
    graph.add_node(
        "section", type="section", standard_code="VAS-01", doc_id="doc", text_preview=preview,
    )
    hit = SimpleNamespace(
        id="section", payload={"doc_id": "doc", "text": full_text, "text_preview": preview},
    )
    client = SimpleNamespace(
        retrieve=AsyncMock(return_value=[hit] if direct_hit else []),
        scroll=AsyncMock(return_value=([hit], None)),
        close=AsyncMock(),
    )
    rerank = AsyncMock(side_effect=lambda query, chunks, **kwargs: chunks)
    monkeypatch.setattr(retrieval_agent, "retrieve", AsyncMock(return_value=[]))
    monkeypatch.setattr("app.rag.retriever._qdrant_client", lambda: client)
    monkeypatch.setattr("app.rag.reranker.rerank", rerank)
    monkeypatch.setattr("app.rag.graph_service.get_graph", lambda: graph)
    monkeypatch.setattr("app.rag.graph_service.get_related_sections", lambda *a, **kw: [])
    monkeypatch.setattr("app.rag.ontology_service.load_ontology", lambda: None)
    monkeypatch.setattr("app.rag.ontology_service.detect_topics", lambda _: [])
    monkeypatch.setattr("app.rag.ontology_service.get_standards_for_topics", lambda _: ["VAS-01"])
    monkeypatch.setattr("app.rag.ontology_service.expand_query", lambda query, _: query)
    prompts: list[str] = []

    async def stream(query: str, system: str, *args: Any) -> AsyncIterator[str]:
        prompts.append(system)
        yield "Answer [C1]"

    monkeypatch.setattr(retrieval_agent, "_stream_llm", stream)
    _ = [event async for event in retrieval_agent.RetrievalAgent().arun(query="Exception?")]

    assert rerank.await_args is not None
    assert rerank.await_args.args[1][0]["text"] == full_text
    assert full_text in prompts[0]


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


@pytest.mark.asyncio
@pytest.mark.parametrize("retry", ["Retry [C1, C99]", "   "])
async def test_final_rechecks_retry_citations(monkeypatch: pytest.MonkeyPatch, retry: str) -> None:
    chunk = RetrievedChunk("chunk", "doc", "Evidence", 1.0, 1.0, {})
    monkeypatch.setattr(retrieval_agent, "retrieve", AsyncMock(return_value=[chunk]))
    monkeypatch.setattr("app.rag.reranker.rerank", AsyncMock(side_effect=lambda query, chunks, **_: chunks))
    answers = iter(["Original [C1, C98]", retry])

    async def stream(*_: Any) -> AsyncIterator[str]:
        yield next(answers)

    monkeypatch.setattr(retrieval_agent, "_stream_llm", stream)
    events = [json.loads(event.removeprefix("data: ")) async for event in
              retrieval_agent.RetrievalAgent().arun(query="Question?", scope="shared")]

    assert [e["key"] for e in events if e["type"] == "citation"] == ["C1"]
    expected = "Retry [C1]" if retry.strip() else "Original [C1]"
    assert events[-1] == {"type": "final", "content": expected}


@pytest.mark.asyncio
async def test_chat_raises_when_all_retrieval_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retrieval_agent, "retrieve", AsyncMock(side_effect=QdrantUnavailableError("offline")))
    monkeypatch.setattr(retrieval_agent, "_stream_llm", _empty_llm)

    with pytest.raises(QdrantUnavailableError):
        _ = [event async for event in retrieval_agent.RetrievalAgent().arun(query="Question?", scope="shared")]
