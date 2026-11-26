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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "entry",
    [
        {"debit_account": "Cash", "credit_account": "Payables", "amount": "Infinity"},
        {"debit_account": "Cash", "credit_account": "", "amount": "10"},
        {
            "debit_account": "Cash",
            "credit_account": "Payables",
            "debit_amount": "10.001",
            "credit_amount": "10.004",
        },
    ],
)
async def test_generate_entries_rejects_invalid_posting(monkeypatch, entry):
    import json

    from app.core.errors import UnbalancedJEError

    class Agent:
        async def arun(self, **_):
            yield "data: " + json.dumps({"type": "token", "delta": json.dumps([entry])})

    monkeypatch.setattr("app.agents.adjustment_agent.AdjustmentAgent", Agent)
    with pytest.raises((ValueError, UnbalancedJEError)):
        await generate_entries([])


@pytest.mark.asyncio
async def test_generate_entries_preserves_split_allocations(monkeypatch):
    import json

    class Agent:
        async def arun(self, **_):
            payload = {
                "adjustments": [
                    {
                        "entries": [
                            {"account": "A", "type": "debit", "amount": "0.10"},
                            {"account": "B", "type": "debit", "amount": "0.20"},
                            {"account": "C", "type": "credit", "amount": "0.30"},
                        ]
                    }
                ]
            }
            yield "data: " + json.dumps({"type": "token", "delta": json.dumps(payload)})

    monkeypatch.setattr("app.agents.adjustment_agent.AdjustmentAgent", Agent)
    (entry,) = await generate_entries([])
    assert [(line["account"], str(line["amount"])) for line in entry["lines"]] == [
        ("A", "0.10"),
        ("B", "0.20"),
        ("C", "0.30"),
    ]
