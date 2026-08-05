from __future__ import annotations

import inspect
from typing import Any

import pytest

from app.rag import retriever


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
