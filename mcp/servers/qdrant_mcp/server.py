"""Qdrant MCP server — collection inspect, payload sample, similarity probe."""
from __future__ import annotations

import os
import asyncio
import logging
from typing import Any
from mcp.server.fastmcp import FastMCP
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qdrant_mcp")

# Initialize FastMCP server
mcp = FastMCP("Qdrant MCP Server")

# Get Qdrant connection details from environment
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

# TEI and Gemini API configurations
TEI_URL = os.environ.get("TEI_URL", "http://localhost:8080")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def _get_qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY or None,
        check_compatibility=False,
    )

async def _embed_text(text: str, target_dim: int) -> list[float] | None:
    """Generate embedding vector using TEI or Gemini based on target dimension."""
    # 1. Try TEI (bge-m3 dim 1024)
    if target_dim == 1024:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {"inputs": [text], "normalize": True}
                resp = await client.post(f"{TEI_URL}/embed", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]
                    elif isinstance(data, dict) and "embeddings" in data:
                        return data["embeddings"][0]
        except Exception as e:
            logger.warning("TEI embedding failed: %s. Trying Gemini fallback.", e)

    # 2. Try Gemini fallback (gemini-embedding-001 or text-embedding-004)
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            # Match model to target dimension if possible
            model = "models/text-embedding-004"
            resp = await client.aio.models.embed_content(
                model=model,
                contents=text,
            )
            if resp.embeddings and len(resp.embeddings) > 0:
                vec = list(resp.embeddings[0].values)
                # If dimension mismatch, print warning
                if len(vec) != target_dim:
                    logger.warning(
                        "Gemini embedded dimension %d does not match target collection dimension %d",
                        len(vec),
                        target_dim
                    )
                return vec
        except Exception as e:
            logger.error("Gemini embedding failed: %s", e)

    return None

@mcp.tool()
async def qdrant_list_collections() -> list[str]:
    """List all collection names in the Qdrant database."""
    client = _get_qdrant_client()
    try:
        response = await client.get_collections()
        return [c.name for c in response.collections]
    except Exception as e:
        logger.error("Failed to list Qdrant collections: %s", e)
        return [f"Error listing collections: {str(e)}"]
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
    except UnexpectedResponse as e:
        return {"error": f"Collection '{collection_name}' not found: {str(e)}"}
    except Exception as e:
        return {"error": f"Error getting collection info: {str(e)}"}
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
    except Exception as e:
        return [{"error": f"Error retrieving points: {str(e)}"}]
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
        if not vector:
            return [{"error": "Failed to generate query embedding. Check TEI_URL or GEMINI_API_KEY."}]

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
    except Exception as e:
        return [{"error": f"Search failed: {str(e)}"}]
    finally:
        await client.close()

def main() -> None:
    """Start the Qdrant MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
