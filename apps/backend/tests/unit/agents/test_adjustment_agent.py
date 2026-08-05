from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.agents import adjustment_agent


@pytest.mark.asyncio
async def test_final_event_contains_generated_adjustment_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_llm(*_: Any, **__: Any) -> AsyncIterator[str]:
        yield "entry "
        yield "content"

    monkeypatch.setattr(adjustment_agent, "_call_llm", fake_llm)

    events = [
        event
        async for event in adjustment_agent.AdjustmentAgent().arun(query="Create adjustment")
    ]
    final_payload = json.loads(events[-1].removeprefix("data: "))

    assert final_payload == {"type": "final", "content": "entry content"}
