"""Document chunking: section-aware recursive splitter targeting 800 tokens."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import tiktoken

# Use cl100k_base (OpenAI) as a solid proxy for token counts
_enc = tiktoken.get_encoding("cl100k_base")

def get_token_count(text: str) -> int:
    return len(_enc.encode(text))

TARGET_TOKENS = 800
OVERLAP_TOKENS = 120
MAX_TABLE_TOKENS = 1500

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_TABLE_RE = re.compile(r"(\|.+\|\n)+", re.MULTILINE)


@dataclass
class Chunk:
    text: str
    chunk_index: int
    section_path: str = ""
    heading: str = ""
    lang: str = "bi"
    standard_code: str | None = None
    topic: str | None = None
    source_type: str | None = None
    paragraph: str | None = None
    section: str | None = None
    jurisdiction: str | None = None
    effective_date: str | None = None
    token_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.token_count = max(1, get_token_count(self.text))


def chunk_document(
    text: str,
    *,
    section_path: str = "",
    heading: str = "",
    lang: str = "bi",
    target_tokens: int = TARGET_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
) -> list[Chunk]:
    """
    Split document into chunks.
    Tables kept whole if ≤ MAX_TABLE_TOKENS; headings preserved as section boundaries.
    """
    if target_tokens <= 0:
        raise ValueError("target_tokens must be greater than zero")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens must be non-negative")

    segments = _split_on_headings(text)
    chunks: list[Chunk] = []
    index = 0

    for seg_heading, seg_text in segments:
        effective_heading = seg_heading or heading
        effective_path = _build_path(section_path, seg_heading)

        # Extract and handle tables first
        tables, remaining = _extract_tables(seg_text)
        for table in tables:
            if get_token_count(table) <= MAX_TABLE_TOKENS:
                chunks.append(Chunk(table, index, effective_path, effective_heading, lang))
                index += 1
            else:
                # Split large table into row groups
                for sub in _split_tokens(table, target_tokens, overlap_tokens):
                    chunks.append(Chunk(sub, index, effective_path, effective_heading, lang))
                    index += 1

        for piece in _split_tokens(remaining.strip(), target_tokens, overlap_tokens):
            if piece.strip():
                chunks.append(Chunk(piece, index, effective_path, effective_heading, lang))
                index += 1

    return chunks


def _split_on_headings(text: str) -> list[tuple[str, str]]:
    """Return [(heading, body)] segments split at markdown headings."""
    segments: list[tuple[str, str]] = []
    last_end = 0
    last_heading = ""

    for m in _HEADING_RE.finditer(text):
        body = text[last_end : m.start()].strip()
        if body or last_heading:
            segments.append((last_heading, body))
        last_heading = m.group(2).strip()
        last_end = m.end()

    segments.append((last_heading, text[last_end:].strip()))
    return segments


def _extract_tables(text: str) -> tuple[list[str], str]:
    tables: list[str] = []
    remaining = text
    for m in _TABLE_RE.finditer(text):
        tables.append(m.group(0).strip())
    remaining = _TABLE_RE.sub("", text)
    return tables, remaining


def _split_tokens(text: str, target_tokens: int, overlap_tokens: int) -> list[str]:
    tokens = _enc.encode(text)
    if len(tokens) <= target_tokens:
        return [text] if text else []
    
    # Guard against infinite loop
    if overlap_tokens >= target_tokens:
        overlap_tokens = target_tokens // 2
        
    pieces: list[str] = []
    start = 0
    while start < len(tokens):
        end = start + target_tokens
        if end >= len(tokens):
            pieces.append(_enc.decode(tokens[start:]))
            break
            
        # Optional: could adjust `end` to sentence boundary in decoded text,
        # but for safety and speed with token arrays, we decode directly.
        chunk = _enc.decode(tokens[start:end])
        pieces.append(chunk)
        start = end - overlap_tokens
    return pieces


def _build_path(base: str, heading: str) -> str:
    if not heading:
        return base
    return f"{base}/{heading}" if base else heading
