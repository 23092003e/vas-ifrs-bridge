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


@pytest.mark.asyncio
async def test_generate_entries_parses_standard_list_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _ListAgent:
        async def arun(self, **_: Any) -> AsyncIterator[str]:
            yield 'data: {"type":"token","delta":"```json\\n[\\n"}\n\n'
            yield 'data: {"type":"token","delta":"  {\\"entry_id\\": \\"ADJ-001\\", \\"debit_account\\": \\"IFRS ROU Asset\\", \\"credit_account\\": \\"IFRS Lease Liability\\", \\"amount\\": 50000.0, \\"standard\\": \\"IFRS 16\\"}\\n"}\n\n'
            yield 'data: {"type":"token","delta":"]\\n```"}\n\n'

    monkeypatch.setattr("app.agents.adjustment_agent.AdjustmentAgent", _ListAgent)

    entries = await generate_entries([{"account_code": "242"}])
    assert len(entries) == 1
    assert entries[0]["entry_id"] == "ADJ-001"
    assert entries[0]["debit_account"] == "IFRS ROU Asset"
    assert entries[0]["credit_account"] == "IFRS Lease Liability"
    assert entries[0]["amount"] == 50000.0
    assert entries[0]["debit_amount"] == 50000.0
    assert entries[0]["credit_amount"] == 50000.0


@pytest.mark.asyncio
async def test_generate_entries_parses_nested_object_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _ObjectAgent:
        async def arun(self, **_: Any) -> AsyncIterator[str]:
            yield 'data: {"type":"token","delta":"```json\\n{\\"adjustments\\": [{\\"description\\": \\"Capitalise lease\\", \\"entries\\": [{\\"account\\": \\"ROU Asset\\", \\"type\\": \\"debit\\", \\"amount\\": 120000}, {\\"account\\": \\"Lease Liability\\", \\"type\\": \\"credit\\", \\"amount\\": 120000}]}]}\\n```"}\n\n'

    monkeypatch.setattr("app.agents.adjustment_agent.AdjustmentAgent", _ObjectAgent)

    entries = await generate_entries([{"account_code": "242"}])
    assert len(entries) == 1
    assert entries[0]["debit_account"] == "ROU Asset"
    assert entries[0]["credit_account"] == "Lease Liability"
    assert entries[0]["amount"] == 120000.0


@pytest.mark.asyncio
async def test_generate_entries_rejects_unbalanced_amounts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.errors import UnbalancedJEError

    class _UnbalancedAgent:
        async def arun(self, **_: Any) -> AsyncIterator[str]:
            yield 'data: {"type":"token","delta":"```json\\n[{\\"debit_amount\\": 100.0, \\"credit_amount\\": 200.0}]\\n```"}\n\n'

    monkeypatch.setattr("app.agents.adjustment_agent.AdjustmentAgent", _UnbalancedAgent)

    with pytest.raises(UnbalancedJEError):
        await generate_entries([{"account_code": "111"}])

