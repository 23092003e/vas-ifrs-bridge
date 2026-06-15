"""PDF parser using PyMuPDF."""

from __future__ import annotations

import fitz


def parse_pdf(path: str) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    doc = fitz.open(path)
    return "\n\n".join(page.get_text() for page in doc)
