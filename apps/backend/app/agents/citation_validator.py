"""Post-generation citation grounding validator."""
from __future__ import annotations


class CitationValidator:
    """Verifies that every [cit:N] key in an LLM response maps to a real chunk."""

    def validate(self, text: str, retrieved_chunks: list[dict]) -> list[str]:
        """Return a list of unresolvable citation keys found in text."""
        # TODO: parse [cit:N] markers and cross-check against retrieved_chunks
        return []
