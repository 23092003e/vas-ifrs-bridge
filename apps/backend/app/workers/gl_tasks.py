"""Celery tasks for GL file processing pipeline."""

from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="gl.process_upload", bind=True, max_retries=3)
def process_gl_upload(self, upload_id: str) -> dict:
    """Parse GL file, map accounts, generate adjustments."""
    # TODO: orchestrate GL pipeline steps
    return {"upload_id": upload_id, "status": "done"}
