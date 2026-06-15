"""Report generation request and status schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import UUID4, BaseModel


class ReportRequest(BaseModel):
    report_type: Literal["balance_sheet", "income_statement", "cash_flow", "notes"]
    period: str
    lang: Literal["vi", "en"] = "vi"


class ReportStatus(BaseModel):
    id: UUID4
    status: Literal["pending", "generating", "done", "failed"]
    download_url: str | None = None
