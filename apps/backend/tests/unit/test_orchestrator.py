"""Unit tests for the multi-agent Orchestrator and intent classifier."""
from __future__ import annotations

import pytest
from unittest.mock import patch
from app.agents.orchestrator import _classify_intent_keywords, _classify_intent


def test_classify_intent_keywords():
    """Verify that keyword-based classification works as expected for different inputs."""
    assert _classify_intent_keywords("Hãy so sánh VAS 15 và IFRS 15") == "compare"
    assert _classify_intent_keywords("Bảng ánh xạ tài khoản") == "mapping"
    assert _classify_intent_keywords("Báo cáo tài chính tổng hợp") == "report"
    assert _classify_intent_keywords("Bút toán điều chỉnh khấu hao") == "adjustment"
    assert _classify_intent_keywords("Làm thế nào để học kế toán?") == "qa"


@pytest.mark.asyncio
@patch("app.llm.providers.gemini.stream_chat")
async def test_classify_intent_llm_success(mock_stream_chat):
    """Verify that LLM-based classification returns the parsed intent on success."""
    # Mock LLM stream returning valid JSON
    async def mock_tokens(*args, **kwargs):
        yield '{"intent":'
        yield ' "compare"}'

    mock_stream_chat.return_value = mock_tokens()

    intent = await _classify_intent("So sánh doanh thu", hint=None)
    assert intent == "compare"


@pytest.mark.asyncio
@patch("app.llm.providers.gemini.stream_chat")
async def test_classify_intent_llm_markdown(mock_stream_chat):
    """Verify that LLM-based classification handles markdown wrapped JSON."""
    async def mock_tokens(*args, **kwargs):
        yield "```json\n"
        yield '{"intent": "mapping"}'
        yield "\n```"

    mock_stream_chat.return_value = mock_tokens()

    intent = await _classify_intent("Ánh xạ tài khoản", hint=None)
    assert intent == "mapping"


@pytest.mark.asyncio
@patch("app.llm.providers.gemini.stream_chat")
async def test_classify_intent_llm_failure_fallback(mock_stream_chat):
    """Verify that LLM failure falls back to keyword-based classification."""
    # Mock stream throwing exception
    async def mock_tokens(*args, **kwargs):
        raise Exception("LLM Timeout or Connection Error")
        yield ""  # to satisfy async generator syntax

    mock_stream_chat.return_value = mock_tokens()

    # Query has "so sánh" -> keyword is "compare"
    intent = await _classify_intent("Hãy so sánh hai thông tư", hint=None)
    assert intent == "compare"

    # Query has no keywords -> fallback to "qa"
    intent = await _classify_intent("Xin chào bạn nhé", hint=None)
    assert intent == "qa"


@pytest.mark.asyncio
@patch("app.llm.providers.gemini.stream_chat")
async def test_classify_intent_llm_invalid_intent_fallback(mock_stream_chat):
    """Verify that an invalid intent from LLM falls back to keyword-based classification."""
    async def mock_tokens(*args, **kwargs):
        yield '{"intent": "invalid_intent_name"}'

    mock_stream_chat.return_value = mock_tokens()

    # Query has "điều chỉnh" -> keyword is "adjustment"
    intent = await _classify_intent("Bút toán điều chỉnh thế nào", hint=None)
    assert intent == "adjustment"
