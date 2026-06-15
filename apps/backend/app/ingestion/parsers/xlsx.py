"""Excel parser using openpyxl."""

from __future__ import annotations

import openpyxl


def parse_xlsx(path: str) -> str:
    """Extract rows and text from an Excel file using openpyxl."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    lines = []
    for sheet in wb.worksheets:
        lines.append(f"--- Sheet: {sheet.title} ---")
        for row in sheet.iter_rows(values_only=True):
            if any(row):
                lines.append("\t".join(str(cell) if cell is not None else "" for cell in row))
    return "\n".join(lines)
