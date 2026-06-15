"""RAG pipeline targeting the shared VAS/IFRS standards collection."""

from __future__ import annotations

from app.rag.citation import assign_citation_keys
from app.rag.retriever import retrieve


async def run_shared_pipeline(query: str, top_k: int = 10) -> list[dict]:
    """Retrieve and annotate chunks from the shared standards collection."""
    chunks = await retrieve(query, collection="shared_standards", top_k=top_k)
    return assign_citation_keys(chunks)
