"""Tool: search a tenant-specific knowledge base."""

from __future__ import annotations


async def search_tenant_kb(query: str, tenant_collection: str, top_k: int = 5) -> list[dict]:
    """Return top_k chunks from the tenant's Qdrant collection."""
    # TODO: embed query and call tenant Qdrant collection
    return []
