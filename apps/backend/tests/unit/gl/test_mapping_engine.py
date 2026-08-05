from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.gl.mapping_engine import _map_with_llm


@pytest.mark.asyncio
async def test_llm_percentage_confidence_is_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    class _MappingAgent:
        async def arun(self, **_: Any) -> AsyncIterator[str]:
            table = "| 999 | Other | Cash | Asset | 85% | Suggested by model |"
            yield f'data: {{"type":"token","delta":{table!r}}}\n\n'.replace("'", '"')

    monkeypatch.setattr("app.agents.gl_mapping_agent.GLMappingAgent", _MappingAgent)

    mappings = await _map_with_llm([{"account_code": "999", "account_name": "Other"}])

    assert mappings[0]["confidence"] == 0.85
