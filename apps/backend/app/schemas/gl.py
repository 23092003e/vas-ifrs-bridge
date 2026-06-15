"""GL upload and account row schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import UUID4, BaseModel


class GLUpload(BaseModel):
    id: UUID4
    tenant_id: str
    filename: str
    status: Literal["pending", "processing", "done", "failed"]


class AccountRow(BaseModel):
    code: str
    name: str
    debit: float = 0.0
    credit: float = 0.0
