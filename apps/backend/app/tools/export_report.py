"""Tool: export a generated report to GCS as PDF/XLSX."""

from __future__ import annotations


async def export_report(report_id: str, format: str = "xlsx") -> str:
    """Render report to file, upload to GCS, return signed URL."""
    # TODO: render and upload
    return ""
