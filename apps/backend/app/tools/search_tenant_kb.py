"""Tool: search a tenant-specific knowledge base."""

from __future__ import annotations

from app.rag.retriever import retrieve


async def search_tenant_kb(
    query: str,
    tenant_collection: str,
    tenant_id: str,
    top_k: int = 5,
) -> list[dict]:
    """Return top_k chunks from the tenant's Qdrant collection."""
    chunks = await retrieve(
        query,
        collection=tenant_collection,
        tenant_id=tenant_id,
        scope="tenant",
        k=top_k,
    )
    return [
        {
            "id": chunk.id,
            "doc_id": chunk.doc_id,
            "text": chunk.text,
            "score": chunk.score,
            "rerank_score": chunk.rerank_score,
            "metadata": chunk.metadata,
            "citation_key": chunk.citation_key,
        }
        for chunk in chunks
    ]
