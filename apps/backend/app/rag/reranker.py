"""Cross-encoder reranker for improving retrieval precision."""
from __future__ import annotations


async def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank retrieved chunks by relevance to query."""
    # TODO: call cross-encoder model
    return chunks[:top_k]
