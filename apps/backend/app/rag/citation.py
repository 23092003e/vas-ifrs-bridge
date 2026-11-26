"""Citation key injection, wrapping, and resolution for LLM responses."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Keep standalone and grouped markers aligned with the chat and compare renderers.
_CITATION_GROUP_RE = re.compile(r"\[(C\d+(?:[,\s]+C\d+)*)\]")
_CITATION_KEY_RE = re.compile(r"C\d+")

# Wrapping template injected into system prompt context block
CHUNK_WRAP_TEMPLATE = '<<C{n} src="{doc_id}#{chunk_id}">>\\n{text}\\n<</C{n}>>'


@dataclass
class Citation:
    key: str  # "C1"
    doc_id: str
    chunk_id: str
    snippet: str
    standard_code: str | None = None
    section: str | None = None


def wrap_chunks_for_prompt(chunks: list) -> tuple[str, dict[str, Citation]]:
    """
    Wrap retrieved chunks for injection into system prompt.
    Returns (context_block, citation_map).
    citation_map keys = "C1", "C2", ...
    """
    parts: list[str] = []
    citation_map: dict[str, Citation] = {}

    for chunk in chunks:
        if isinstance(chunk, dict):
            key = chunk.get("citation_key") or f"C{len(citation_map) + 1}"
            doc_id = chunk.get("doc_id", "")
            chunk_id = chunk.get("id", "")
            text = chunk.get("text", "")
            metadata = chunk.get("metadata", {}) or {}
        else:
            key = getattr(chunk, "citation_key", "") or f"C{len(citation_map) + 1}"
            doc_id = getattr(chunk, "doc_id", "")
            chunk_id = getattr(chunk, "id", "")
            text = getattr(chunk, "text", "")
            metadata = getattr(chunk, "metadata", {}) or {}

        source_uri = metadata.get("source_uri", "")
        if source_uri:
            import os
            doc_id = os.path.basename(source_uri)

        chunk_index = metadata.get("chunk_index")
        if chunk_index is not None:
            chunk_id = str(chunk_index)

        wrapped = f'<<{key} src="{doc_id}#{chunk_id}">>\n{text}\n<</{key}>>'
        parts.append(wrapped)
        citation_map[key] = Citation(
            key=key,
            doc_id=doc_id,
            chunk_id=chunk_id,
            snippet=text[:200],
            standard_code=metadata.get("standard_code"),
            section=metadata.get("section"),
        )

    return "\n\n".join(parts), citation_map


def extract_used_keys(text: str) -> set[str]:
    """Return all [Cn] citation keys found in LLM answer text."""
    return {key for group in _CITATION_GROUP_RE.findall(text) for key in _CITATION_KEY_RE.findall(group)}


def validate_citations(answer: str, citation_map: dict[str, Citation]) -> tuple[bool, list[str]]:
    """
    Check all [Cn] in answer exist in citation_map.
    Returns (is_valid, list_of_unresolved_keys).
    """
    used = extract_used_keys(answer)
    unresolved = sorted(used - citation_map.keys())
    return len(unresolved) == 0, unresolved


def strip_unresolved_citations(answer: str, unresolved: list[str]) -> str:
    """Remove unresolved [Cn] markers from answer text."""
    invalid = set(unresolved)

    def clean_group(match: re.Match[str]) -> str:
        keys = _CITATION_KEY_RE.findall(match[1])
        kept = [key for key in keys if key not in invalid]
        if len(kept) == len(keys):
            return match[0]
        return f"[{', '.join(kept)}]" if kept else ""

    return _CITATION_GROUP_RE.sub(clean_group, answer).strip()


def build_citation_list(answer: str, citation_map: dict[str, Citation]) -> list[Citation]:
    """Return Citation objects for every [Cn] key found in answer (in order)."""
    seen: set[str] = set()
    result: list[Citation] = []
    for group in _CITATION_GROUP_RE.findall(answer):
        for key in _CITATION_KEY_RE.findall(group):
            if key in citation_map and key not in seen:
                result.append(citation_map[key])
                seen.add(key)
    return result
