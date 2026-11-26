from __future__ import annotations

from app.agents.citation_validator import CitationValidator
from app.rag.citation import (
    Citation,
    build_citation_list,
    extract_used_keys,
    wrap_chunks_for_prompt,
)
from app.rag.retriever import RetrievedChunk


def test_dataclass_chunk_preserves_document_id_in_citation() -> None:
    chunk = RetrievedChunk(
        id="chunk-1",
        doc_id="document-1",
        text="Accounting evidence",
        score=0.9,
        rerank_score=0.95,
        metadata={"standard_code": "VAS 01"},
        citation_key="C1",
    )

    wrapped, citations = wrap_chunks_for_prompt([chunk])

    assert 'src="document-1#chunk-1"' in wrapped
    assert citations["C1"].doc_id == "document-1"


def test_invalid_grouped_citations_do_not_remove_valid_keys_or_bracketed_prose() -> None:
    citations = {key: Citation(key, "doc", key, "Evidence") for key in ("C1", "C2")}
    answer = "Rule [C1, C99, C2]. Exception[C98 C97]. See [appendix C99]."

    valid, missing, cleaned = CitationValidator().validate(answer, citations)

    assert not valid
    assert set(missing) == {"C97", "C98", "C99"}
    assert cleaned == "Rule [C1, C2]. Exception. See [appendix C99]."
    assert extract_used_keys(cleaned) == {"C1", "C2"}
    assert [cite.key for cite in build_citation_list(cleaned, citations)] == ["C1", "C2"]
