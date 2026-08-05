from __future__ import annotations

from typing import Any

import pytest

from app.tools import (
    export_report,
    generate_adjustment,
    map_account,
    parse_gl_file,
    search_tenant_kb,
)


@pytest.mark.asyncio
async def test_parse_gl_file_delegates_to_real_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = [{"account_code": "111"}]
    monkeypatch.setattr("app.gl.parser.parse", lambda _: expected)

    assert await parse_gl_file.parse_gl_file("ledger.csv") == expected


@pytest.mark.asyncio
async def test_tenant_search_passes_tenant_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    async def fake_retrieve(*_: Any, **kwargs: Any) -> list[Any]:
        calls.append(kwargs)
        return []

    monkeypatch.setattr(search_tenant_kb, "retrieve", fake_retrieve, raising=False)

    result = await search_tenant_kb.search_tenant_kb(
        "query",
        "tenant_collection",
        "174c7f5b-2cb9-4746-b1a7-b0c5e42591d1",
    )

    assert result == []
    assert calls[0]["scope"] == "tenant"
    assert calls[0]["tenant_id"] == "174c7f5b-2cb9-4746-b1a7-b0c5e42591d1"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "call",
    [
        lambda: export_report.export_report("report-1"),
        lambda: generate_adjustment.generate_adjustment("mapping-1"),
    ],
)
async def test_unimplemented_tools_do_not_return_fake_success(call: Any) -> None:
    with pytest.raises(NotImplementedError):
        await call()


@pytest.mark.asyncio
async def test_map_account_delegates_to_mapping_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = {"src_account_code": "111", "target_account_code": "CASH"}

    async def fake_map(*_: Any, **__: Any) -> list[dict[str, str]]:
        return [expected]

    monkeypatch.setattr("app.gl.mapping_engine.map_accounts", fake_map)

    result = await map_account.map_account("111", "tenant-1")

    assert result == expected
