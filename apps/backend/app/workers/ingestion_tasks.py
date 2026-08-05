"""Celery tasks for document ingestion pipeline."""

from __future__ import annotations

import asyncio

from app.ingestion.jobs import ingest_document
from app.workers.celery_app import celery_app


@celery_app.task(
    name="ingestion.ingest_document",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def ingest_document_task(self, document_id: str, local_path: str, tenant_id: str) -> dict:
    """Parse, chunk, embed, and upsert a document into Qdrant."""
    asyncio.run(
        ingest_document(
            document_id=document_id,
            local_path=local_path,
            tenant_id=tenant_id,
        )
    )
    return {"document_id": document_id, "status": "done"}
