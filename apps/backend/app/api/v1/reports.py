"""Financial report generation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/generate")
async def generate_report(body: dict) -> dict:
    """Enqueue a report generation job."""
    raise HTTPException(status_code=501, detail="Report generation is not implemented")


@router.get("/{report_id}/download")
async def download_report(report_id: str) -> dict:
    """Return a signed GCS URL for the generated report."""
    raise HTTPException(status_code=501, detail="Report download is not implemented")
