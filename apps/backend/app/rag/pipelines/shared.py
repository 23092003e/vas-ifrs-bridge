"""RAG pipeline targeting the shared VAS/IFRS standards collection."""

from __future__ import annotations

from app.rag.retriever import RetrievedChunk, retrieve


async def run_shared_pipeline(query: str, top_k: int = 10) -> list[RetrievedChunk]:
    """Retrieve chunks from the shared standards collection."""
    return await retrieve(query, collection="shared_standards", k=top_k)
