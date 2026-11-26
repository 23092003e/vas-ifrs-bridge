from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

import openpyxl
import pytest

from app.gl.parser import _extract_data_rows, parse


@pytest.mark.parametrize("suffix", ["csv", "xlsx"])
def test_parse_trial_balance_template_keeps_all_periods(tmp_path: Path, suffix: str) -> None:
    header = [
        "Mã TK",
        "Tên Tài Khoản",
        "Dư Đầu Kỳ Nợ",
        "Dư Đầu Kỳ Có",
        "Phát Sinh Nợ",
        "Phát Sinh Có",
        "Dư Cuối Kỳ Nợ",
        "Dư Cuối Kỳ Có",
    ]
    rows: list[list[str | int]] = [
        ["Bảng cân đối phát sinh"],
        list(header),
        ["0111", "Tiền mặt", 1250, 0, 8450, 8100, 1600, 0],
        ["331", "Phải trả", 0, 200, 0, 0, 0, 200],
    ]
    path = tmp_path / f"trial-balance.{suffix}"
    if suffix == "csv":
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            csv.writer(handle).writerows(rows)
    else:
        book = openpyxl.Workbook()
        for row in rows:
            book.active.append(row)
        book.save(path)
        book.close()

    cash, payable = parse(str(path))

    assert cash == {
        "account_code": "0111",
        "account_name": "Tiền mặt",
        "opening_debit": Decimal(1250),
        "opening_credit": Decimal(0),
        "movement_debit": Decimal(8450),
        "movement_credit": Decimal(8100),
        "closing_debit": Decimal(1600),
        "closing_credit": Decimal(0),
        "debit": Decimal(8450),
        "credit": Decimal(8100),
        "balance": Decimal(1600),
    }
    assert payable["debit"] == payable["credit"] == Decimal(0)
    assert payable["balance"] == Decimal(-200)


def test_simple_csv_uses_code_header_and_respects_explicit_zero_balance(tmp_path: Path) -> None:
    path = tmp_path / "simple.csv"
    path.write_text("Tên tài khoản,Số hiệu,Nợ,Có,Số dư\nTiền mặt,111,200,100,0\n")

    assert parse(str(path)) == [
        {
            "account_code": "111",
            "account_name": "Tiền mặt",
            "debit": Decimal(200),
            "credit": Decimal(100),
            "balance": Decimal(0),
        }
    ]


@pytest.mark.parametrize(
    "header",
    [
        "A,B,C,D",
        "Mã TK,Tên TK,Nợ,Debit,Có",
        "Mã TK,Tên TK,Dư đầu kỳ Nợ,Nợ,Có",
    ],
)
def test_ambiguous_or_unknown_headers_are_rejected(tmp_path: Path, header: str) -> None:
    path = tmp_path / "bad.csv"
    path.write_text(f"{header}\n111,Cash,0,0,0\n")

    with pytest.raises(ValueError, match="header"):
        parse(str(path))


def test_parser_preserves_decimal_amounts_and_normalizes_excel_account_code() -> None:
    rows = _extract_data_rows(
        [[111.0, "Cash", "0.10", "0.20"]],
        {"account_code": 0, "account_name": 1, "debit": 2, "credit": 3},
    )

    assert rows[0]["account_code"] == "111"
    assert rows[0]["debit"] == Decimal("0.10")
    assert rows[0]["credit"] == Decimal("0.20")


@pytest.mark.parametrize("amount", ["not-a-number", "NaN", "Infinity", float("inf"), "1,23"])
def test_parser_rejects_invalid_nonempty_amount(amount: object) -> None:
    with pytest.raises(ValueError, match="Invalid amount"):
        _extract_data_rows(
            [["111", "Cash", amount, "0"]],
            {"account_code": 0, "account_name": 1, "debit": 2, "credit": 3},
        )
