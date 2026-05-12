"""GL file parser — normalises xlsx/csv exports into account rows."""
from __future__ import annotations


def parse(file_path: str) -> list[dict]:
    """Detect format and parse GL export into normalised account rows."""
    # TODO: detect format, delegate to xlsx or csv parser
    return []
