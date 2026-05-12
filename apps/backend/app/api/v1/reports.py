"""Financial report generation endpoints."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def generate_report(body: dict) -> dict:
    """Enqueue a report generation job."""
    # TODO: enqueue report_tasks.generate
    return {"report_id": None}


@router.get("/{report_id}/download")
async def download_report(report_id: str) -> dict:
    """Return a signed GCS URL for the generated report."""
    # TODO: generate signed URL
    return {"url": None}
