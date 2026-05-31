"""Unit tests for agents in the VAS-IFRS Bridge."""

from __future__ import annotations

from unittest.mock import patch
import pytest
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.ifrs_compare_agent import IFRSCompareAgent
from app.agents.gl_mapping_agent import GLMappingAgent
from app.agents.adjustment_agent import AdjustmentAgent
from app.gl.adjustments import validate_balance, generate_entries
from app.core.errors import UnbalancedJE


def test_agent_initialization():
    """Verify that all agents can be instantiated and have correct loggers assigned."""
    retrieval_agent = RetrievalAgent()
    compare_agent = IFRSCompareAgent()
    mapping_agent = GLMappingAgent()
    adjustment_agent = AdjustmentAgent()

    assert retrieval_agent.logger.name == "agent.RetrievalAgent"
    assert compare_agent.logger.name == "agent.IFRSCompareAgent"
    assert mapping_agent.logger.name == "agent.GLMappingAgent"
    assert adjustment_agent.logger.name == "agent.AdjustmentAgent"


@pytest.mark.asyncio
@patch("app.agents.retrieval_agent.retrieve")
@patch("app.rag.reranker.rerank")
@patch("app.agents.retrieval_agent._stream_llm")
async def test_retrieval_agent_run(mock_stream_llm, mock_rerank, mock_retrieve):
    """Test RetrievalAgent.arun runs and formats streaming response correctly."""
    # Mock retrieve to return a simple RetrievedChunk
    from app.rag.retriever import RetrievedChunk

    mock_chunk = RetrievedChunk(
        id="123",
        doc_id="doc_1",
        text="VAS 01 standard text content",
        score=0.9,
        rerank_score=0.95,
        metadata={"lang": "vi", "standard_code": "VAS01"},
        citation_key="C1",
    )
    mock_retrieve.return_value = [mock_chunk]

    # Mock rerank to return same format
    mock_rerank.return_value = [
        {
            "id": "123",
            "doc_id": "doc_1",
            "text": "VAS 01 standard text content",
            "score": 0.9,
            "rerank_score": 0.95,
            "metadata": {"lang": "vi", "standard_code": "VAS01"},
        }
    ]

    # Mock LLM stream generator
    async def mock_tokens(*args, **kwargs):
        yield "Mẫu"
        yield " phản"
        yield " hồi"

    mock_stream_llm.return_value = mock_tokens()

    agent = RetrievalAgent()
    tokens = []
    async for event in agent.arun(query="Tìm hiểu VAS 01", lang="vi"):
        tokens.append(event)

    assert len(tokens) > 0
    # The output should contain token events, citation events, and a final event
    assert any("token" in t for t in tokens)
    assert any("final" in t for t in tokens)


@pytest.mark.asyncio
@patch("app.agents.gl_mapping_agent.retrieve_multi")
@patch("app.rag.retriever.retrieve")
@patch("app.agents.gl_mapping_agent._call_llm")
async def test_gl_mapping_agent_run(mock_call_llm, mock_retrieve, mock_retrieve_multi):
    """Test GLMappingAgent.arun runs and streams correctly."""
    from app.rag.retriever import RetrievedChunk

    mock_retrieve_multi.return_value = [
        RetrievedChunk(
            id="1",
            doc_id="doc_1",
            text="VAS account 1111 is cash",
            score=0.9,
            rerank_score=0.9,
            metadata={"lang": "vi"},
        )
    ]
    mock_retrieve.return_value = [
        RetrievedChunk(
            id="2",
            doc_id="doc_2",
            text="IFRS cash equivalents line",
            score=0.8,
            rerank_score=0.8,
            metadata={"lang": "vi"},
        )
    ]

    async def mock_tokens(*args, **kwargs):
        yield "Bảng"
        yield " ánh"
        yield " xạ"

    mock_call_llm.return_value = mock_tokens()

    agent = GLMappingAgent()
    events = []
    async for event in agent.arun(query="Ánh xạ tài khoản 1111", lang="vi"):
        events.append(event)

    assert len(events) > 0
    assert any("token" in e for e in events)
    assert any("final" in e for e in events)


def test_validate_balance():
    """Verify validate_balance behavior for balanced and unbalanced amounts."""
    # Balanced should pass without errors
    validate_balance(100.0, 100.0)
    validate_balance(1234.56, 1234.56)

    # Unbalanced should raise UnbalancedJE
    with pytest.raises(UnbalancedJE):
        validate_balance(100.0, 200.0)


@pytest.mark.asyncio
@patch("app.agents.adjustment_agent._call_llm")
async def test_adjustment_agent_run(mock_call_llm):
    """Test AdjustmentAgent.arun streams response successfully."""

    async def mock_tokens(*args, **kwargs):
        yield "Overview paragraph\n"
        yield "```json\n"
        yield '[{"entry_id": "1", "amount": 100}]'
        yield "\n```"

    mock_call_llm.return_value = mock_tokens()

    agent = AdjustmentAgent()
    events = []
    async for event in agent.arun(query="Test lease adjustment"):
        events.append(event)

    assert len(events) > 0
    assert any("token" in e for e in events)
    assert any("final" in e for e in events)


@pytest.mark.asyncio
@patch("app.agents.adjustment_agent._call_llm")
async def test_generate_entries_balanced(mock_call_llm):
    """Verify generate_entries returns successfully parsed balanced entries."""

    async def mock_tokens(*args, **kwargs):
        yield "Overview: Adjustments\n"
        yield "```json\n"
        yield '[\n  {\n    "entry_id": "ADJ-01",\n    "debit_account": "ROU",\n    "credit_account": "Lease Liab",\n    "amount": 500.0\n  }\n]'
        yield "\n```"

    mock_call_llm.return_value = mock_tokens()

    results = await generate_entries([{"test": "data"}])
    assert len(results) == 1
    assert results[0]["entry_id"] == "ADJ-01"
    assert results[0]["amount"] == 500.0


@pytest.mark.asyncio
@patch("app.agents.adjustment_agent._call_llm")
async def test_generate_entries_unbalanced(mock_call_llm):
    """Verify generate_entries raises UnbalancedJE if debit and credit are not equal."""

    async def mock_tokens(*args, **kwargs):
        yield "```json\n"
        yield '[\n  {\n    "entry_id": "ADJ-02",\n    "debit_account": "ROU",\n    "credit_account": "Lease Liab",\n    "debit_amount": 500.0,\n    "credit_amount": 600.0\n  }\n]'
        yield "\n```"

    mock_call_llm.return_value = mock_tokens()

    with pytest.raises(UnbalancedJE):
        await generate_entries([{"test": "data"}])
