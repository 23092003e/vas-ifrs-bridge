"""Text normalizer — cleans and standardises extracted document text."""

from __future__ import annotations

import re
import unicodedata

_INLINE_WHITESPACE = re.compile(r"[^\S\n]+")
_EXCESS_BLANK_LINES = re.compile(r"\n{3,}")


def normalize(raw_text: str) -> str:
    """Normalize Unicode and whitespace without changing document wording."""
    if not raw_text:
        return ""

    text = unicodedata.normalize("NFC", raw_text)
    text = (
        text.replace("\ufeff", "")
        .replace("\u200b", " ")
        .replace("\u00a0", " ")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    lines = [_INLINE_WHITESPACE.sub(" ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines).strip()
    return _EXCESS_BLANK_LINES.sub("\n\n", text)
