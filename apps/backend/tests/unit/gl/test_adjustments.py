from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.gl.adjustments import generate_entries


@pytest.mark.asyncio
async def test_generate_entries_rejects_llm_response_without_valid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _InvalidAgent:
        async def arun(self, **_: Any) -> AsyncIterator[str]:
            yield 'data: {"type":"token","delta":"not structured"}\n\n'

    monkeypatch.setattr("app.agents.adjustment_agent.AdjustmentAgent", _InvalidAgent)

    with pytest.raises(ValueError, match="JSON"):
        await generate_entries([{"account_code": "111"}])
