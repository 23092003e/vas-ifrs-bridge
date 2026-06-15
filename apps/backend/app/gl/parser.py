"""GL file parser — normalises xlsx/csv exports into account rows."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

import openpyxl

logger = logging.getLogger(__name__)


def parse(file_path: str) -> list[dict[str, Any]]:
    """Detect format and parse GL export into normalised account rows."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in (".xlsx", ".xls"):
        return _parse_xlsx(path)
    elif suffix == ".csv":
        return _parse_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def _find_header_and_mapping(rows: list[list[Any]]) -> tuple[int, dict[str, int]]:
    """
    Search for a header row containing GL keywords.
    Returns (header_row_index, column_name_to_index_mapping).
    """
    keywords = {
        "account_code": [
            "tài khoản",
            "số hiệu",
            "mã tk",
            "account code",
            "account_code",
            "code",
            "acct",
        ],
        "account_name": [
            "tên tài khoản",
            "tên tk",
            "account name",
            "account_name",
            "description",
            "name",
        ],
        "debit": ["nợ", "debit", "dr", "nợ đầu kỳ", "nợ phát sinh"],
        "credit": ["có", "credit", "cr", "có đầu kỳ", "có phát sinh"],
        "balance": ["số dư", "dư cuối kỳ", "dư", "balance", "amount"],
    }

    for idx, row in enumerate(rows):
        # Convert row cells to lower-case strings
        str_cells = [str(c).lower().strip() if c is not None else "" for c in row]

        # Determine if this row looks like a header
        matches = {}
        for col_name, kw_list in keywords.items():
            for c_idx, cell in enumerate(str_cells):
                if any(kw in cell for kw in kw_list):
                    matches[col_name] = c_idx
                    break

        # If we matched at least account_code and account_name (and either debit/credit or balance)
        if "account_code" in matches and "account_name" in matches:
            if "balance" in matches or ("debit" in matches and "credit" in matches):
                return idx, matches

    # Default fallback: assume first row is header, search best-effort
    fallback_matches = {"account_code": 0, "account_name": 1, "debit": 2, "credit": 3, "balance": 4}
    return 0, fallback_matches


def _parse_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[list[str]] = []
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)

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


def _to_float(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    # Clean string from commas, currency symbols, and spaces
    str_val = str(val).replace(",", "").replace("$", "").replace("đ", "").strip()
    try:
        return float(str_val)
    except ValueError:
        return 0.0


def _extract_data_rows(data_rows: list[list[Any]], mapping: dict[str, int]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    code_idx = mapping.get("account_code")
    name_idx = mapping.get("account_name")
    debit_idx = mapping.get("debit")
    credit_idx = mapping.get("credit")
    balance_idx = mapping.get("balance")

    for row in data_rows:
        if not row:
            continue

        # Check that we have enough columns in this row
        row_len = len(row)

        account_code = (
            str(row[code_idx]).strip()
            if code_idx is not None and code_idx < row_len and row[code_idx] is not None
            else ""
        )
        account_name = (
            str(row[name_idx]).strip()
            if name_idx is not None and name_idx < row_len and row[name_idx] is not None
            else ""
        )

        # Ignore empty account code rows
        if not account_code:
            continue

        debit = _to_float(row[debit_idx]) if debit_idx is not None and debit_idx < row_len else 0.0
        credit = (
            _to_float(row[credit_idx]) if credit_idx is not None and credit_idx < row_len else 0.0
        )
        balance = (
            _to_float(row[balance_idx])
            if balance_idx is not None and balance_idx < row_len
            else 0.0
        )

        # If debit/credit is zero but balance is given, use balance for amount normalization
        if debit == 0.0 and credit == 0.0 and balance != 0.0:
            if balance > 0:
                debit = balance
            else:
                credit = abs(balance)

        normalized.append(
            {
                "account_code": account_code,
                "account_name": account_name,
                "debit": debit,
                "credit": credit,
                "balance": balance or (debit - credit),
            }
        )

    return normalized
