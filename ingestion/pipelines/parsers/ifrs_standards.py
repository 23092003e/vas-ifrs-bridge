"""Ingestion pipeline for IFRS Foundation standards and amendments."""
from __future__ import annotations


async def ingest_ifrs_standards(source_dir: str, collection: str = "shared_standards") -> None:
    """Parse, chunk, embed and upsert IFRS standard PDFs."""
    # TODO: discover PDFs, run unstructured_runner, batch_embed
