"""Celery tasks for financial report generation."""

from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="reports.generate", bind=True, max_retries=2)
def generate_report_task(self, report_id: str, report_type: str, period: str) -> dict:
    """Generate IFRS financial report and export to GCS."""
    # TODO: call ReportAgent and export_report tool
    return {"report_id": report_id, "status": "done"}
