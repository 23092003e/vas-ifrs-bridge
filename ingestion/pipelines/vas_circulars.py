"""Ingestion pipeline for VAS Ministry of Finance circulars."""
from __future__ import annotations


async def ingest_vas_circulars(source_dir: str, collection: str = "shared_standards") -> None:
    """Parse, chunk, embed and upsert VAS circular PDFs."""
    # TODO: discover PDFs, run unstructured_runner, batch_embed
