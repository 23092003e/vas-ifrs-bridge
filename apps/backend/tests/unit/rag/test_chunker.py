from __future__ import annotations

import pytest

from app.rag.chunker import chunk_document


def test_chunker_rejects_negative_overlap() -> None:
    with pytest.raises(ValueError, match="overlap_tokens"):
        chunk_document("a" * 20, target_tokens=1, overlap_tokens=-1)
