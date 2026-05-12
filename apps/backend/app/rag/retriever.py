"""Hybrid retriever: dense Qdrant search + optional BM25 sparse."""
from __future__ import annotations


async def retrieve(
    query: str,
    collection: str,
    top_k: int = 10,
    use_reranker: bool = True,
) -> list[dict]:
    """Retrieve and optionally rerank chunks from a Qdrant collection."""
    # TODO: embed query, search Qdrant, rerank
    return []
