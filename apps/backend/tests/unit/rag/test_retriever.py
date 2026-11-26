from __future__ import annotations

import inspect
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.core.errors import QdrantUnavailableError
from app.rag import retriever


@pytest.mark.asyncio
@pytest.mark.parametrize("full_text", ["Opening. Material exception.", "", None])
async def test_retrieve_sends_full_text_to_reranker(
    monkeypatch: pytest.MonkeyPatch, full_text: str | None,
) -> None:
    payload = {"doc_id": "doc", "text_preview": "Opening."}
    if full_text is not None:
        payload["text"] = full_text
    hit = SimpleNamespace(id="chunk", score=1.0, payload=payload)
    rerank = AsyncMock(side_effect=lambda query, chunks, **kwargs: chunks)
    monkeypatch.setattr(retriever, "embed_query", AsyncMock(return_value=[1.0]))
    monkeypatch.setattr(retriever, "_qdrant_client", lambda: SimpleNamespace(close=AsyncMock()))
    monkeypatch.setattr(retriever, "_hybrid_search", AsyncMock(return_value=[hit]))
    monkeypatch.setattr(retriever, "rerank", rerank)

    chunks = await retriever.retrieve("exception", collection="kb_shared_vas")

    expected = full_text or payload["text_preview"]
    assert rerank.await_args is not None
    assert rerank.await_args.args[1][0]["text"].endswith(expected)
    assert chunks[0].text.endswith(expected)


def test_tenant_scope_requires_tenant_id() -> None:
    with pytest.raises(ValueError, match="tenant_id"):
        retriever._build_filter(lang="auto", scope="tenant", tenant_id=None)


def test_invalid_scope_is_rejected() -> None:
    with pytest.raises(ValueError, match="scope"):
        retriever._build_filter(lang="auto", scope="invalid", tenant_id=None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scope", "expected"),
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
        ("tenant", {"tenant_test"}),
    ],
)
async def test_retrieve_multi_honors_scope(
    scope: str,
    expected: set[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert "scope" in inspect.signature(retriever.retrieve_multi).parameters
    queried: list[str] = []

    async def fake_retrieve(*_: Any, collection: str, **__: Any) -> list[Any]:
        queried.append(collection)
        return []

    async def fake_rerank(*_: Any, **__: Any) -> list[Any]:
        return []

    monkeypatch.setattr(retriever, "retrieve", fake_retrieve)
    monkeypatch.setattr(retriever, "rerank", fake_rerank)

    await retriever.retrieve_multi(
        "query",
        tenant_collection="tenant_test",
        tenant_id="174c7f5b-2cb9-4746-b1a7-b0c5e42591d1",
        scope=scope,
    )

    assert set(queried) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["empty", "partial", "failed"])
async def test_retrieve_multi_distinguishes_outage_from_empty_and_partial(
    monkeypatch: pytest.MonkeyPatch, state: str,
) -> None:
    async def retrieve(*_: Any, collection: str, **__: Any) -> list[retriever.RetrievedChunk]:
        if state == "failed" or (state == "partial" and collection != "kb_shared_vas"):
            raise QdrantUnavailableError("offline")
        if state == "empty":
            return []
        return [retriever.RetrievedChunk("chunk", "doc", "Evidence", 1.0, 1.0, {})]

    monkeypatch.setattr(retriever, "retrieve", retrieve)
    monkeypatch.setattr(retriever, "rerank", AsyncMock(side_effect=lambda query, chunks, **_: chunks))

    if state == "failed":
        with pytest.raises(QdrantUnavailableError):
            await retriever.retrieve_multi("Question?", scope="shared", require_available=True)
        assert await retriever.retrieve_multi("Question?", scope="shared") == []
    else:
        chunks = await retriever.retrieve_multi("Question?", scope="shared", require_available=True)
        assert [c.id for c in chunks] == (["chunk"] if state == "partial" else [])
