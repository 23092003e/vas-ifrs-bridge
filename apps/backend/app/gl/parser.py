"""GL file parser — normalises xlsx/csv exports into account rows."""

from __future__ import annotations

import csv
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import openpyxl

_HEADERS = {
    "account_code": (
        "tài khoản",
        "số hiệu",
        "số hiệu tk",
        "mã tài khoản",
        "mã tk",
        "account code",
        "code",
        "acct",
    ),
    "account_name": ("tên tài khoản", "tên tk", "account name", "description", "name"),
    "debit": ("nợ", "debit", "dr"),
    "credit": ("có", "credit", "cr"),
    "balance": ("số dư", "dư cuối kỳ", "dư", "balance", "closing balance", "amount"),
    "opening_debit": ("dư đầu kỳ nợ", "số dư đầu kỳ nợ", "nợ đầu kỳ", "opening debit"),
    "opening_credit": ("dư đầu kỳ có", "số dư đầu kỳ có", "có đầu kỳ", "opening credit"),
    "movement_debit": ("phát sinh nợ", "nợ phát sinh", "movement debit"),
    "movement_credit": ("phát sinh có", "có phát sinh", "movement credit"),
    "closing_debit": ("dư cuối kỳ nợ", "số dư cuối kỳ nợ", "nợ cuối kỳ", "closing debit"),
    "closing_credit": ("dư cuối kỳ có", "số dư cuối kỳ có", "có cuối kỳ", "closing credit"),
}
_HEADER_ROLE = {alias: role for role, aliases in _HEADERS.items() for alias in aliases}
_PERIODS = frozenset(
    role for role in _HEADERS if role.startswith(("opening_", "movement_", "closing_"))
)
_MOVEMENTS = {"movement_debit", "movement_credit"}
_SIMPLE_AMOUNTS = {"debit", "credit", "balance"}
_GROUPED_AMOUNT = re.compile(r"[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?")


def parse(file_path: str) -> list[dict[str, Any]]:
    """Detect format and parse GL export into normalised account rows."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".xlsx":
        return _parse_xlsx(path)
    elif suffix == ".csv":
        return _parse_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def _find_header_and_mapping(rows: list[list[Any]]) -> tuple[int, dict[str, int]]:
    """Find an explicit simple GL or full trial balance header."""
    for idx, row in enumerate(rows):
        mapping = {}
        duplicates = set()
        for position, cell in enumerate(row):
            if not isinstance(cell, str):
                continue
            normalized = " ".join(
                unicodedata.normalize("NFC", cell).casefold().replace("_", " ").split()
            )
            role = _HEADER_ROLE.get(normalized)
            if role:
                if role in mapping:
                    duplicates.add(role)
                mapping[role] = position

        if not {"account_code", "account_name"} <= mapping.keys():
            continue
        if duplicates:
            raise ValueError(
                f"Ambiguous GL header: duplicate columns for {', '.join(sorted(duplicates))}"
            )

        periods = _PERIODS & mapping.keys()
        simple = _SIMPLE_AMOUNTS & mapping.keys()
        if periods and (
            (periods == _PERIODS and not simple)
            or (periods == _MOVEMENTS and simple <= {"balance"})
        ):
            return idx, mapping
        if not periods and ({"debit", "credit"} <= simple or simple == {"balance"}):
            return idx, mapping
        raise ValueError(
            "Unsupported GL header: expected a complete trial balance or simple debit/credit or balance"
        )

    raise ValueError("GL header not found: expected account code, account name and amount columns")


def _parse_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[list[str]] = []
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.reader(f))

    if not rows:
        return []

    header_idx, mapping = _find_header_and_mapping(rows)
    return _extract_data_rows(rows[header_idx + 1 :], mapping)


def _parse_xlsx(path: Path) -> list[dict[str, Any]]:
    # Open spreadsheet in read-only and data-only modes
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    sheet = wb.active
    if sheet is None:
        wb.close()
        return []

    rows: list[list[Any]] = []
    for row in sheet.iter_rows(values_only=True):
        rows.append(list(row))
    wb.close()

    if not rows:
        return []

    header_idx, mapping = _find_header_and_mapping(rows)
    return _extract_data_rows(rows[header_idx + 1 :], mapping)


def _to_decimal(val: Any) -> Decimal:
    if val is None:
        return Decimal(0)
    raw = str(val).strip()
    if not raw:
        return Decimal(0)
    cleaned = raw.strip("$đĐ").strip()
    if "," in cleaned:
        if not _GROUPED_AMOUNT.fullmatch(cleaned):
            raise ValueError(f"Invalid amount: {val}")
        cleaned = cleaned.replace(",", "")
    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount: {val}") from exc
    if not amount.is_finite():
        raise ValueError(f"Invalid amount: {val}")
    return amount


def _account_code(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _extract_data_rows(data_rows: list[list[Any]], mapping: dict[str, int]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    full_trial_balance = _PERIODS <= mapping.keys()

    for row in data_rows:
        cells = {role: row[index] if index < len(row) else None for role, index in mapping.items()}
        code = cells.get("account_code")
        account_code = _account_code(code) if code is not None else ""
        if not account_code:
            continue
        name = cells.get("account_name")
        account_name = str(name).strip() if name is not None else ""

        amounts = {
            role: _to_decimal(value)
            for role, value in cells.items()
            if role in _PERIODS or role in _SIMPLE_AMOUNTS
        }
        debit = amounts.get("movement_debit", amounts.get("debit", Decimal(0)))
        credit = amounts.get("movement_credit", amounts.get("credit", Decimal(0)))
        explicit_balance = cells.get("balance")
        if full_trial_balance:
            balance = amounts["closing_debit"] - amounts["closing_credit"]
        else:
            balance = (
                amounts["balance"]
                if explicit_balance is not None and str(explicit_balance).strip()
                else debit - credit
            )
            if debit == credit == 0 and not _MOVEMENTS.intersection(mapping):
                debit, credit = max(balance, Decimal(0)), max(-balance, Decimal(0))

        normalized.append(
            {
                "account_code": account_code,
                "account_name": account_name,
                **{role: amount for role, amount in amounts.items() if role in _PERIODS},
                "debit": debit,
                "credit": credit,
                "balance": balance,
            }
        )

    return normalized
