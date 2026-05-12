"""Text embedding — wraps the configured embedding model."""
from __future__ import annotations


async def embed(texts: list[str]) -> list[list[float]]:
    """Return dense embeddings for a batch of texts."""
    # TODO: call embedding model (e.g. text-embedding-3-small or local bge-m3)
    return []
