from __future__ import annotations

from typing import Any

import pytest

from app.eval import hallucination_eval


@pytest.mark.asyncio
async def test_precision_result_is_not_mislabelled_as_recall(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def faith(*_: Any) -> tuple[float, str]:
        return 0.9, "faith"

    async def relevancy(*_: Any) -> tuple[float, str]:
        return 0.8, "relevant"

    async def precision(*_: Any) -> tuple[float, str]:
        return 0.7, "precision"

    monkeypatch.setattr(hallucination_eval, "score_faithfulness", faith)
    monkeypatch.setattr(hallucination_eval, "score_answer_relevancy", relevancy)
    monkeypatch.setattr(hallucination_eval, "score_context_precision", precision)

    result = await hallucination_eval._eval_record(
        {"question": "q", "answer": "a", "contexts": ["c"]},
        hallucination_eval.asyncio.Semaphore(1),
    )

    assert result["context_recall"] is None
    assert result["context_precision"] == {"score": 0.7, "reason": "precision"}
