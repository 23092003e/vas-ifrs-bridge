from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest
from app.schemas.gl import AccountRow, GLUpload
from app.schemas.mapping import MappingRule


def test_chat_rejects_blank_content() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(content="   ")


def test_account_amounts_preserve_decimal_precision() -> None:
    row = AccountRow(code="111", name="Cash", debit="0.10", credit="0.20")

    assert row.debit == Decimal("0.10")
    assert row.credit == Decimal("0.20")


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_mapping_confidence_must_be_a_probability(confidence: float) -> None:
    with pytest.raises(ValidationError):
        MappingRule(
            id=uuid4(),
            vas_code="111",
            ifrs_code="CASH",
            confidence=confidence,
        )


def test_gl_upload_uses_database_status_vocabulary() -> None:
    upload = GLUpload(
        id=uuid4(),
        tenant_id=str(uuid4()),
        filename="ledger.csv",
        status="mapped",
    )

    assert upload.status == "mapped"
