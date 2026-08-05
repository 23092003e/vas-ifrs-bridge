from __future__ import annotations

from decimal import Decimal

import pytest

from app.gl.parser import _extract_data_rows


def test_parser_preserves_decimal_amounts_and_normalizes_excel_account_code() -> None:
    rows = _extract_data_rows(
        [[111.0, "Cash", "0.10", "0.20"]],
        {"account_code": 0, "account_name": 1, "debit": 2, "credit": 3},
    )

    assert rows[0]["account_code"] == "111"
    assert rows[0]["debit"] == Decimal("0.10")
    assert rows[0]["credit"] == Decimal("0.20")


def test_parser_rejects_invalid_nonempty_amount() -> None:
    with pytest.raises(ValueError, match="not-a-number"):
        _extract_data_rows(
            [["111", "Cash", "not-a-number", "0"]],
            {"account_code": 0, "account_name": 1, "debit": 2, "credit": 3},
        )
