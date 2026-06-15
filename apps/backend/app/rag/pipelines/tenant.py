"""RAG pipeline targeting a tenant-specific document collection."""

from __future__ import annotations

from app.rag.citation import assign_citation_keys
from app.rag.retriever import retrieve


async def run_tenant_pipeline(query: str, tenant_collection: str, top_k: int = 10) -> list[dict]:
    """Retrieve and annotate chunks from the tenant's private collection."""
    chunks = await retrieve(query, collection=tenant_collection, top_k=top_k)
    return assign_citation_keys(chunks)
