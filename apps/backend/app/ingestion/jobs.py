"""Ingestion job definitions — called by Celery workers."""

from __future__ import annotations


async def ingest_document(document_id: str, gcs_path: str, collection: str) -> None:
    """Full ingestion pipeline: parse -> normalise -> chunk -> embed -> upsert."""
    # TODO: orchestrate parsers, chunker, embedder, Qdrant upsert
