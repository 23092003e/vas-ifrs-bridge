"""
Unit tests for GraphRAG components: graph_service and retrieval integration.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import networkx as nx
import pytest

from app.agents.retrieval_agent import RetrievalAgent
from app.rag import graph_service
from app.rag.retriever import RetrievedChunk


@pytest.fixture
def mock_graph():
    """Create a small, controlled graph for testing."""
    G = nx.DiGraph()
    # Add Document Nodes
    G.add_node("doc_vas_15", id="doc_vas_15", type="document", standard_code="VAS-15", lang="vi")
    G.add_node("doc_ifrs_15", id="doc_ifrs_15", type="document", standard_code="IFRS-15", lang="en")

    # Add Section Nodes
    G.add_node(
        "sec_vas_15_p1",
        id="sec_vas_15_p1",
        type="section",
        standard_code="VAS-15",
        doc_id="doc_vas_15",
        text_preview="Doanh thu bán hàng...",
        heading="1. Doanh thu",
    )
    G.add_node(
        "sec_ifrs_15_p1",
        id="sec_ifrs_15_p1",
        type="section",
        standard_code="IFRS-15",
        doc_id="doc_ifrs_15",
        text_preview="Revenue recognition steps...",
        heading="1. Revenue",
    )

    # Add Account Nodes
    G.add_node(
        "acc_511", id="acc_511", type="account", account_code="511", name_vi="Doanh thu bán hàng"
    )

    # Add Edges
    G.add_edge("doc_vas_15", "sec_vas_15_p1", relation="HAS_SECTION")
    G.add_edge("doc_ifrs_15", "sec_ifrs_15_p1", relation="HAS_SECTION")
    G.add_edge("sec_vas_15_p1", "doc_ifrs_15", relation="MAPS_TO")
    G.add_edge("acc_511", "doc_vas_15", relation="GOVERNED_BY")

    return G


def test_graph_service_lookup_empty():
    """Verify that graph_service functions handle empty/missing graphs without error."""
    with patch("app.rag.graph_service.get_graph") as mock_get_graph:
        mock_get_graph.return_value = nx.DiGraph()

        assert graph_service.get_related_sections("nonexistent") == []
        assert graph_service.get_ifrs_equivalents("nonexistent") == []
        assert graph_service.get_governed_sections_for_account("511") == []


def test_graph_service_lookup_populated(mock_graph):
    """Verify standard traversals on a mock graph."""
    with patch("app.rag.graph_service.get_graph") as mock_get_graph:
        mock_get_graph.return_value = mock_graph

        # Test MAPS_TO and children HAS_SECTION expansion
        equivalents = graph_service.get_ifrs_equivalents("sec_vas_15_p1")
        assert "sec_ifrs_15_p1" in equivalents

        # Test GOVERNED_BY expansion
        governed = graph_service.get_governed_sections_for_account("511")
        assert "sec_vas_15_p1" in governed


def test_graph_load_fallback_on_missing_file():
    """Verify that graph service initializes an empty graph if file doesn't exist."""
    # Reset singleton graph cache to force reloading
    graph_service._GRAPH = None

    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False

        G = graph_service.get_graph()
        assert isinstance(G, nx.DiGraph)
        assert G.number_of_nodes() == 0


@pytest.mark.asyncio
@patch("app.agents.retrieval_agent.retrieve")
@patch("app.rag.reranker.rerank")
@patch("app.agents.retrieval_agent._stream_llm")
async def test_retrieval_agent_graph_expansion(
    mock_stream_llm, mock_rerank, mock_retrieve, mock_graph
):
    """Verify RetrievalAgent graph expansion logic performs correctly."""
    # Mock original Qdrant search to return a VAS-15 chunk
    mock_chunk = RetrievedChunk(
        id="chunk_vas_15",
        doc_id="doc_vas_15",
        text="Doanh thu bán hàng và cung cấp dịch vụ được ghi nhận khi...",
        score=0.9,
        rerank_score=0.9,
        metadata={"standard_code": "VAS-15"},
    )
    mock_retrieve.return_value = [mock_chunk]

    # Mock reranker to just return whatever input list is passed to it
    async def mock_rerank_fn(query, chunks, top_k):
        return chunks[:top_k]

    mock_rerank.side_effect = mock_rerank_fn

    # Mock LLM stream
    async def mock_tokens(*args, **kwargs):
        yield "Response"

    mock_stream_llm.return_value = mock_tokens()

    # Patch graph service to return our mock graph
    with patch("app.rag.graph_service.get_graph", return_value=mock_graph):
        # Mock Qdrant client retrieve and scroll
        from unittest.mock import AsyncMock

        mock_client = MagicMock()
        mock_client.close = AsyncMock()

        # When client retrieves/scrolls, return IFRS equivalents or related sections
        mock_record = MagicMock()
        mock_record.id = "sec_ifrs_15_p1"
        mock_record.payload = {
            "doc_id": "doc_ifrs_15",
            "text": "IFRS 15 establishes a five-step model to account for revenue...",
            "standard_code": "IFRS-15",
        }

        mock_client.retrieve = AsyncMock(return_value=[mock_record])
        mock_client.scroll = AsyncMock(return_value=([], None))

        # Patch qdrant client creation inside retrieval agent
        with patch("app.rag.retriever._qdrant_client", return_value=mock_client):
            agent = RetrievalAgent()
            events = []

            # Query containing account code 511
            async for event in agent.arun(query="Doanh thu tài khoản 511", lang="vi"):
                events.append(event)

            assert len(events) > 0
            # Verify mock_client retrieve was called for graph expansion
            assert mock_client.retrieve.called
