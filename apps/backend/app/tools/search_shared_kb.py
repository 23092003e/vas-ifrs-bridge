"""Tool: search the shared VAS/IFRS knowledge base."""

from __future__ import annotations

from app.rag.retriever import retrieve_multi


async def search_shared_kb(query: str, top_k: int = 5) -> list[dict]:
    """Return top_k chunks from the shared Qdrant collections."""
    chunks = await retrieve_multi(query, k=top_k)
    return [
        {
            "id": c.id,
            "doc_id": c.doc_id,
            "text": c.text,
            "score": c.score,
            "rerank_score": c.rerank_score,
            "metadata": c.metadata,
            "citation_key": c.citation_key,
        }
        for c in chunks
    ]
