from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.agents import orchestrator
from app.schemas.chat import ChatRequest


@pytest.mark.asyncio
async def test_classify_intent_keywords() -> None:
    # Compare
    assert await orchestrator._classify_intent("So sánh VAS 15 và IFRS 15", None) == "compare"
    assert await orchestrator._classify_intent("What is the difference between them?", None) == "compare"

    # Mapping
    assert await orchestrator._classify_intent("Mapping tài khoản 242", None) == "mapping"
    assert await orchestrator._classify_intent("Ánh xạ chart of accounts", None) == "mapping"

    # Adjustment
    assert await orchestrator._classify_intent("Tạo bút toán điều chỉnh cho thuê tài sản", None) == "adjustment"
    assert await orchestrator._classify_intent("Propose adjustment entries for IFRS 16", None) == "adjustment"

    # Report
    assert await orchestrator._classify_intent("Tổng hợp báo cáo tài chính", None) == "report"

    # Hint override
    assert await orchestrator._classify_intent("so sánh", "qa") == "qa"


@pytest.mark.asyncio
async def test_classify_intent_llm_fallback_json() -> None:
    # Ambiguous query that doesn't trigger keywords
    ambiguous_query = "Liệu có cần ghi nhận quyền sử dụng không?"

    with patch("app.llm.router.complete_chat", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = '{"intent": "adjustment"}'
        result = await orchestrator._classify_intent(ambiguous_query, None)
        assert result == "adjustment"
        mock_complete.assert_awaited_once()


@pytest.mark.asyncio
async def test_classify_intent_llm_fallback_markdown_block() -> None:
    ambiguous_query = "Nêu sự khác biệt trong hạch toán doanh thu"

    with patch("app.llm.router.complete_chat", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = '```json\n{"intent": "compare"}\n```'
        result = await orchestrator._classify_intent(ambiguous_query, None)
        assert result == "compare"


@pytest.mark.asyncio
async def test_classify_intent_llm_fallback_failure_defaults_qa() -> None:
    ambiguous_query = "Một câu hỏi kế toán chung"

    with patch("app.llm.router.complete_chat", new_callable=AsyncMock) as mock_complete:
        mock_complete.side_effect = RuntimeError("LLM unavailable")
        result = await orchestrator._classify_intent(ambiguous_query, None)
        assert result == "qa"


@pytest.mark.asyncio
async def test_orchestrator_run_stream_avoids_duplicate_user_message_in_history() -> None:
    class FakeAgent:
        def __init__(self) -> None:
            self.passed_messages: list[dict[str, str]] | None = None

        async def arun(self, **kwargs: Any):
            self.passed_messages = kwargs.get("messages")
            yield 'data: {"type": "token", "delta": "ok"}\n\n'

    fake_agent = FakeAgent()

    class FakeMessage:
        def __init__(self, role: str, content: str):
            self.role = role
            self.content = content

    # Simulate existing messages in DB: previous QA pair + the newly saved user message
    mock_db_messages = [
        FakeMessage(role="user", content="previous question"),
        FakeMessage(role="assistant", content="previous answer"),
        FakeMessage(role="user", content="current question"),
    ]

    class FakeScalars:
        def all(self):
            return list(reversed(mock_db_messages))  # descending created_at

    class FakeScalarResult:
        def scalars(self):
            return FakeScalars()

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args: object):
            pass

        async def execute(self, stmt: Any):
            return FakeScalarResult()

    with (
        patch("app.agents.retrieval_agent.RetrievalAgent", return_value=fake_agent),
        patch("app.db.session.AsyncSessionLocal", return_value=FakeSession()),
    ):
        orch = orchestrator.Orchestrator()
        req = ChatRequest(content="current question", intent_hint="qa")
        events = [
            e
            async for e in orch.run_stream(
                req,
                conversation_id="conv-123",
            )
        ]

        assert events
        # Verify that history contains only previous messages, and the current question is not duplicated!
        assert fake_agent.passed_messages == [
            {"role": "user", "content": "previous question"},
            {"role": "assistant", "content": "previous answer"},
        ]
