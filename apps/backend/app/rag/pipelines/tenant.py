"""RAG pipeline targeting a tenant-specific document collection."""

from __future__ import annotations

from app.rag.retriever import RetrievedChunk, retrieve


async def run_tenant_pipeline(query: str, tenant_collection: str, top_k: int = 10) -> list[RetrievedChunk]:
    """Retrieve chunks from the tenant's private collection."""
    return await retrieve(query, collection=tenant_collection, k=top_k)
