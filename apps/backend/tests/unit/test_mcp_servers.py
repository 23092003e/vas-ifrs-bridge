"""Unit tests for the Qdrant and n8n MCP servers."""
from __future__ import annotations

import os
import sys
import importlib.util
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock

# Dynamic import of qdrant_mcp server.py to avoid name clash with 'mcp' third-party library
workspace_root = Path(__file__).resolve().parents[4]
server_py_path = workspace_root / "mcp" / "servers" / "qdrant_mcp" / "server.py"

spec = importlib.util.spec_from_file_location("qdrant_mcp_server", str(server_py_path))
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for Qdrant MCP server at {server_py_path}")

qdrant_mcp_server = importlib.util.module_from_spec(spec)
sys.modules["qdrant_mcp_server"] = qdrant_mcp_server
spec.loader.exec_module(qdrant_mcp_server)

qdrant_mcp = qdrant_mcp_server.mcp


def test_qdrant_mcp_tools_registration():
    """Verify that all Qdrant MCP tools are registered correctly."""
    tools = set(qdrant_mcp._tool_manager._tools.keys())
    expected_tools = {
        "qdrant_list_collections",
        "qdrant_get_collection_info",
        "qdrant_retrieve_points",
        "qdrant_search",
    }
    assert expected_tools.issubset(tools)


@pytest.mark.asyncio
@patch("qdrant_client.AsyncQdrantClient.get_collections")
async def test_qdrant_list_collections_tool(mock_get_collections):
    """Test qdrant_list_collections tool logic."""
    # Mock return value from Qdrant get_collections
    mock_response = AsyncMock()
    mock_collection = AsyncMock()
    mock_collection.name = "kb_shared_vas"
    mock_response.collections = [mock_collection]
    mock_get_collections.return_value = mock_response

    # Find the tool in qdrant_mcp
    list_collections_tool = qdrant_mcp._tool_manager._tools["qdrant_list_collections"]
    
    # Execute the tool function
    result = await list_collections_tool.fn()
    assert result == ["kb_shared_vas"]
