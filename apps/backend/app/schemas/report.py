"""Report generation request and status schemas."""
from __future__ import annotations

from pydantic import BaseModel, UUID4
from typing import Literal


class ReportRequest(BaseModel):
    report_type: Literal["balance_sheet", "income_statement", "cash_flow", "notes"]
    period: str
    lang: Literal["vi", "en"] = "vi"


class ReportStatus(BaseModel):
    id: UUID4
    status: Literal["pending", "generating", "done", "failed"]
    download_url: str | None = None
