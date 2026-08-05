from __future__ import annotations

from app.rag.citation import wrap_chunks_for_prompt
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
