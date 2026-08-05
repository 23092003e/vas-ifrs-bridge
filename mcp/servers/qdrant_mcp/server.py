"""Qdrant MCP server — collection inspect, payload sample, similarity probe."""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from qdrant_client import AsyncQdrantClient

if __package__:
    from .embedding import embed_text
else:
    from embedding import embed_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qdrant_mcp")

# Initialize FastMCP server
mcp = FastMCP("Qdrant MCP Server")

# Get Qdrant connection details from environment
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

def _get_qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY or None,
        check_compatibility=False,
    )

async def _embed_text(text: str, target_dim: int) -> list[float]:
    """Generate a bge-m3 embedding using the same Ollama contract as the app."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await embed_text(
            text,
            target_dim=target_dim,
            base_url=OLLAMA_BASE_URL,
            client=client,
        )

@mcp.tool()
async def qdrant_list_collections() -> list[str]:
    """List all collection names in the Qdrant database."""
    client = _get_qdrant_client()
    try:
        response = await client.get_collections()
        return [c.name for c in response.collections]
    finally:
        await client.close()

@mcp.tool()
async def qdrant_get_collection_info(collection_name: str) -> dict[str, Any]:
    """Get detailed configuration, status, and vector dimension of a specific collection."""
    client = _get_qdrant_client()
    try:
        info = await client.get_collection(collection_name=collection_name)
        # Extract vector config
        vector_config = {}
        if hasattr(info.config, "params") and hasattr(info.config.params, "vectors"):
            vectors = info.config.params.vectors
            if hasattr(vectors, "size"):
                vector_config = {"size": vectors.size, "distance": str(vectors.distance)}
            elif isinstance(vectors, dict):
                vector_config = {k: {"size": v.size, "distance": str(v.distance)} for k, v in vectors.items()}

        return {
            "status": str(info.status),
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "segments_count": info.segments_count,
            "vector_config": vector_config,
        }
    finally:
        await client.close()

@mcp.tool()
async def qdrant_retrieve_points(collection_name: str, ids: list[str]) -> list[dict[str, Any]]:
    """Retrieve specific points by their UUIDs or integer IDs from a collection."""
    client = _get_qdrant_client()
    try:
        parsed_ids: list[int | str] = [int(i) if i.isdigit() else i for i in ids]
        records = await client.retrieve(
            collection_name=collection_name,
            ids=parsed_ids,
            with_payload=True,
            with_vectors=False,
        )
        return [
            {
                "id": str(r.id),
                "payload": r.payload,
            }
            for r in records
        ]
    finally:
        await client.close()

@mcp.tool()
async def qdrant_search(collection_name: str, query_text: str, limit: int = 5) -> list[dict[str, Any]]:
    """Run similarity search on a collection by embedding the input query text."""
    client = _get_qdrant_client()
    try:
        # Fetch collection info to get required vector size
        info = await client.get_collection(collection_name=collection_name)
        target_dim = 1024 # Default fallback
        if hasattr(info.config, "params") and hasattr(info.config.params, "vectors"):
            vectors = info.config.params.vectors
            if hasattr(vectors, "size"):
                target_dim = vectors.size
            elif isinstance(vectors, dict) and len(vectors) > 0:
                first_key = next(iter(vectors))
                target_dim = vectors[first_key].size

        # Generate embedding vector
        vector = await _embed_text(query_text, target_dim)
        # Perform query
        result = await client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in result.points
        ]
    finally:
        await client.close()

def main() -> None:
    """Start the Qdrant MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
