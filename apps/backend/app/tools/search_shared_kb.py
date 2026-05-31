"""Tool: search the shared VAS/IFRS knowledge base."""

from __future__ import annotations


async def search_shared_kb(query: str, top_k: int = 5) -> list[dict]:
    """Return top_k chunks from the shared Qdrant collection."""
    # TODO: embed query and call Qdrant shared collection
    return []
