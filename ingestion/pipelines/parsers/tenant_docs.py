"""Ingestion pipeline for tenant-uploaded documents."""
from __future__ import annotations


async def ingest_tenant_doc(document_id: str, gcs_path: str, tenant_collection: str) -> None:
    """Parse, chunk, embed and upsert a tenant document into their private collection."""
    # TODO: download from GCS, run parsers, chunk, embed, upsert
