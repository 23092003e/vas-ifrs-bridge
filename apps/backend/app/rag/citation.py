"""Citation key injection, wrapping, and resolution for LLM responses."""
from __future__ import annotations

import re
from dataclasses import dataclass

# Matches [C1], [C2], ... [C99]
_CITATION_RE = re.compile(r"\[C(\d+)\]")

# Wrapping template injected into system prompt context block
CHUNK_WRAP_TEMPLATE = "<<C{n} src=\"{doc_id}#{chunk_id}\">>\\n{text}\\n<</C{n}>>"


@dataclass
class Citation:
    key: str          # "C1"
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
        key = chunk.citation_key if hasattr(chunk, "citation_key") else f"C{len(citation_map) + 1}"
        n = key[1:]  # strip "C"
        doc_id = getattr(chunk, "doc_id", "") or chunk.get("doc_id", "") if isinstance(chunk, dict) else ""
        chunk_id = getattr(chunk, "id", "") or (chunk.get("id", "") if isinstance(chunk, dict) else "")
        text = getattr(chunk, "text", "") or (chunk.get("text", "") if isinstance(chunk, dict) else "")
        metadata = getattr(chunk, "metadata", {}) or (chunk.get("metadata", {}) if isinstance(chunk, dict) else {})

        wrapped = (
            f"<<{key} src=\"{doc_id}#{chunk_id}\">>\n"
            f"{text}\n"
            f"<</{key}>>"
        )
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
    return {f"C{m.group(1)}" for m in _CITATION_RE.finditer(text)}


def validate_citations(
    answer: str, citation_map: dict[str, Citation]
) -> tuple[bool, list[str]]:
    """
    Check all [Cn] in answer exist in citation_map.
    Returns (is_valid, list_of_unresolved_keys).
    """
    used = extract_used_keys(answer)
    unresolved = [k for k in used if k not in citation_map]
    return len(unresolved) == 0, unresolved


def strip_unresolved_citations(answer: str, unresolved: list[str]) -> str:
    """Remove unresolved [Cn] markers from answer text."""
    for key in unresolved:
        answer = answer.replace(f"[{key}]", "")
    return answer.strip()


def build_citation_list(answer: str, citation_map: dict[str, Citation]) -> list[Citation]:
    """Return Citation objects for every [Cn] key found in answer (in order)."""
    seen: set[str] = set()
    result: list[Citation] = []
    for m in _CITATION_RE.finditer(answer):
        key = f"C{m.group(1)}"
        if key in citation_map and key not in seen:
            result.append(citation_map[key])
            seen.add(key)
    return result
