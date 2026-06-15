"""Post-generation citation grounding validator."""

from __future__ import annotations

import logging

from app.rag.citation import Citation, strip_unresolved_citations, validate_citations

logger = logging.getLogger(__name__)


class CitationValidator:
    """Verifies every [Cn] key in LLM response maps to a retrieved chunk."""

    def validate(
        self,
        answer: str,
        citation_map: dict[str, Citation],
    ) -> tuple[bool, list[str], str]:
        """
        Returns (is_valid, unresolved_keys, cleaned_answer).
        Strips unresolved markers from cleaned_answer.
        """
        is_valid, unresolved = validate_citations(answer, citation_map)
        if not is_valid:
            logger.warning("citation_validator: unresolved keys %s", unresolved)
            cleaned = strip_unresolved_citations(answer, unresolved)
        else:
            cleaned = answer
        return is_valid, unresolved, cleaned
