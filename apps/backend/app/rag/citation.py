"""Citation key injection and resolution utilities."""
from __future__ import annotations


def assign_citation_keys(chunks: list[dict]) -> list[dict]:
    """Add a [cit:N] key to each retrieved chunk for inline citation."""
    return [{**c, "citation_key": f"cit:{i + 1}"} for i, c in enumerate(chunks)]


def resolve_citations(text: str, keyed_chunks: list[dict]) -> list[dict]:
    """Return citation metadata for all [cit:N] keys found in text."""
    # TODO: parse keys from text and match to keyed_chunks
    return []
