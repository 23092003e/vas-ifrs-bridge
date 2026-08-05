"""GL upload and account row schemas."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import UUID4, BaseModel


class GLUpload(BaseModel):
    id: UUID4
    tenant_id: str
    filename: str
    status: Literal["pending", "processing", "mapped", "failed"]


class AccountRow(BaseModel):
    code: str
    name: str
    debit: Decimal = Decimal(0)
    credit: Decimal = Decimal(0)
