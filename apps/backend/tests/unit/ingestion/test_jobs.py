from __future__ import annotations

import inspect
from typing import Any, Self

import pytest

from app.ingestion import jobs


class _EmptyResult:
    def scalar_one_or_none(self) -> None:
        return None


class _Session:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def execute(self, statement: Any) -> _EmptyResult:
        self.statements.append(statement)
        return _EmptyResult()


@pytest.mark.asyncio
async def test_ingestion_fetches_document_with_tenant_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert "tenant_id" in inspect.signature(jobs.ingest_document).parameters
    session = _Session()
    monkeypatch.setattr(jobs, "AsyncSessionLocal", lambda: session)

    await jobs.ingest_document(
        document_id="89bc0df4-cdf0-49f8-a0c8-4191aaf1912b",
        local_path="document.pdf",
        tenant_id="174c7f5b-2cb9-4746-b1a7-b0c5e42591d1",
    )

    assert "documents.tenant_id" in str(session.statements[0].whereclause)


def test_ingestion_point_ids_are_idempotent() -> None:
    assert hasattr(jobs, "_point_id")

    first = jobs._point_id("document-1", 3)
    retry = jobs._point_id("document-1", 3)
    other_chunk = jobs._point_id("document-1", 4)

    assert first == retry
    assert first != other_chunk
