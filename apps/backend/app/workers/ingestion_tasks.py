"""Celery tasks for document ingestion pipeline."""

from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="ingestion.ingest_document", bind=True, max_retries=3)
def ingest_document_task(self, document_id: str, gcs_path: str, collection: str) -> dict:
    """Parse, chunk, embed, and upsert a document into Qdrant."""
    # TODO: call async ingestion.jobs.ingest_document via asyncio.run
    return {"document_id": document_id, "status": "done"}
