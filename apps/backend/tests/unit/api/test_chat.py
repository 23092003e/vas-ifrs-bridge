from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Self
from uuid import UUID

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.v1 import chat
from app.schemas.chat import ChatRequest

TENANT_ID = "174c7f5b-2cb9-4746-b1a7-b0c5e42591d1"
CONVERSATION_ID = "89bc0df4-cdf0-49f8-a0c8-4191aaf1912b"


def _request(method: str) -> Request:
    request = Request({"type": "http", "method": method, "path": "/v1/chat", "headers": []})
    request.state.user_id = "user-1"
    request.state.tenant = SimpleNamespace(id=TENANT_ID, qdrant_collection="tenant_test")
    return request


class _EmptyResult:
    def scalar_one_or_none(self) -> None:
        return None


class _CapturingDb:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    async def execute(self, statement: Any) -> _EmptyResult:
        self.statements.append(statement)
        return _EmptyResult()

    def add(self, value: Any) -> None:
        return None

    async def commit(self) -> None:
        return None


def _assert_tenant_scoped(statement: Any) -> None:
    assert "conversations.tenant_id" in str(statement.whereclause)


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", [chat.get_conversation, chat.delete_conversation])
async def test_conversation_detail_operations_are_tenant_scoped(endpoint: Any) -> None:
    db = _CapturingDb()

    with pytest.raises(HTTPException) as exc_info:
        await endpoint(CONVERSATION_ID, _request("GET"), db)

    assert exc_info.value.status_code == 404
    _assert_tenant_scoped(db.statements[0])


@pytest.mark.asyncio
async def test_stream_cannot_reuse_conversation_from_another_tenant() -> None:
    db = _CapturingDb()
    body = ChatRequest(
        conversation_id=UUID(CONVERSATION_ID),
        content="So sánh VAS và IFRS",
    )

    await chat.chat_stream(body, _request("POST"), db)

    _assert_tenant_scoped(db.statements[0])


@pytest.mark.asyncio
async def test_stream_does_not_expose_internal_exception_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FailingOrchestrator:
        async def run_stream(self, *_: Any, **__: Any) -> Any:
            raise RuntimeError("database password=do-not-leak")
            yield  # pragma: no cover - makes this an async generator

    monkeypatch.setattr(chat, "_orchestrator", _FailingOrchestrator())
    response = await chat.chat_stream(
        ChatRequest(content="Câu hỏi"),
        _request("POST"),
        _CapturingDb(),
    )

    payload = b"".join([chunk async for chunk in response.body_iterator]).decode()

    assert "do-not-leak" not in payload
    assert '"type": "error"' in payload


@pytest.mark.asyncio
async def test_stream_uses_agent_validated_final_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FinalizingOrchestrator:
        async def run_stream(self, *_: Any, **__: Any) -> Any:
            yield 'data: {"type":"token","delta":"draft [C99]"}\n\n'
            yield 'data: {"type":"final","content":"draft"}\n\n'

    persisted: list[Any] = []

    class _PersistenceSession(_CapturingDb):
        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        def add(self, value: Any) -> None:
            persisted.append(value)

    session = _PersistenceSession()
    monkeypatch.setattr(chat, "_orchestrator", _FinalizingOrchestrator())
    monkeypatch.setattr("app.db.session.AsyncSessionLocal", lambda: session)

    response = await chat.chat_stream(
        ChatRequest(content="Câu hỏi"),
        _request("POST"),
        _CapturingDb(),
    )
    payload = b"".join([chunk async for chunk in response.body_iterator]).decode()

    assert '"content": "draft"' in payload
    assert persisted[-1].content == "draft"
