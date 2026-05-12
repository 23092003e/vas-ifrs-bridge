"""Document chunking strategies for ingestion."""
from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    # TODO: implement semantic or fixed-size chunking
    return []
