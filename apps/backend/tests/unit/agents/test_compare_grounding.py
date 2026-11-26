from __future__ import annotations

import pytest

from app.agents import ifrs_compare_agent as compare
from app.core.errors import QdrantUnavailableError
from app.rag.retriever import RetrievedChunk


def chunk(id: str, standard: str) -> RetrievedChunk:
    return RetrievedChunk(id, id, f"Fixture for {standard}", 0.9, 0.9, {"standard_code": standard})


@pytest.mark.asyncio
async def test_compare_reserves_sources_for_explicit_standard_codes(monkeypatch):
    calls = []

    async def retrieve(query, *, collection, standard_codes, **kwargs):
        calls.append((collection, standard_codes, kwargs))
        if collection == "kb_shared_vas":
            return [chunk("v", "VAS 05"), chunk("wrong_code", "VAS 03")]
        if "IAS 40" in standard_codes:
            return [chunk("i", "IAS 40"), chunk("wrong_side", "VAS 05")]
        return []

    monkeypatch.setattr(compare, "retrieve", retrieve)
    rows, keys, missing = await compare._retrieve_sides(
        "VAS05 với IAS-40 và IFRS 17",
        tenant_collection=None,
        tenant_id=None,
        scope="shared",
        lang="vi",
    )
    assert [row.id for row in rows] == ["v", "i"]
    assert keys == {"VAS": {"C1"}, "IFRS": {"C2"}}
    assert missing == ["IFRS 17"]
    assert [(collection, len(codes) > 0) for collection, codes, _ in calls] == [
        ("kb_shared_vas", True),
        ("kb_shared_ifrs", True),
        ("kb_shared_ifrs", True),
    ]


@pytest.mark.asyncio
async def test_compare_tenant_scope_and_total_failure(monkeypatch):
    calls = []

    async def retrieve(query, *, collection, scope, tenant_id, **kwargs):
        calls.append((collection, scope, tenant_id))
        raise QdrantUnavailableError("test")

    monkeypatch.setattr(compare, "retrieve", retrieve)
    with pytest.raises(QdrantUnavailableError):
        await compare._retrieve_sides(
            "Compare", tenant_collection="own", tenant_id="tenant", scope="tenant", lang="en"
        )
    assert calls == [("own", "tenant", "tenant")] * 2


def test_compare_checks_citations_per_claim_and_requires_both_sides():
    text = (
        "VAS: verified VAS [C1]\n"
        "VAS: wrong side [C2]\n"
        "IFRS: mixed invalid IDs [C2,C9]\n"
        "IFRS: verified IFRS [C2]\n"
        "COMPARE: one side only [C1]\n"
        "COMPARE: verified comparison [C1,C2]\n"
        "Unlabelled [C2]"
    )
    answer = compare._grounded_answer(text, {"VAS": {"C1"}, "IFRS": {"C2"}}, [], "en")
    assert "verified VAS" in answer
    assert "verified IFRS" in answer
    assert "verified comparison" in answer
    assert "wrong side" not in answer
    assert "mixed invalid" not in answer
    assert "one side only" not in answer
    assert "Unlabelled" not in answer


@pytest.mark.asyncio
async def test_compare_does_not_stream_an_unverified_partial_comparison(monkeypatch):
    import json

    async def retrieve(query, *, collection, **kwargs):
        return [chunk("v", "VAS 05")] if collection == "kb_shared_vas" else []

    async def model(*args):
        yield "VAS: Supported "
        yield "claim [C1]\nIFRS: Fake [C1]\nCOMPARE: Unsupported [C1]"

    monkeypatch.setattr(compare, "retrieve", retrieve)
    monkeypatch.setattr(compare, "_call_llm", model)
    events = [
        json.loads(event.removeprefix("data: "))
        async for event in compare.IFRSCompareAgent().arun(
            query="Compare VAS 05 and IAS 40", scope="shared", lang="en"
        )
    ]
    assert [event["type"] for event in events] == ["token", "citation", "final"]
    assert "Supported claim" in events[-1]["content"]
    assert "missing for IAS 40" in events[-1]["content"]
    assert "Fake" not in events[0]["delta"]
    assert "Unsupported" not in events[0]["delta"]
    assert events[1]["key"] == "C1"


def test_compare_resolves_standard_alias_only_when_it_selects_one_visible_chunk():
    from app.rag.citation import wrap_chunks_for_prompt

    _, citation_map = wrap_chunks_for_prompt(
        [chunk("v", "VAS 05"), chunk("i1", "IAS 40"), chunk("i2", "IAS 40")]
    )
    answer = compare._grounded_answer(
        "VAS 05: verified [VAS 05]\nIAS 40: ambiguous [IAS 40]\n"
        "IFRS: code absent [IFRS 17]\nIAS 40: explicit [C2]",
        {"VAS": {"C1"}, "IFRS": {"C2", "C3"}},
        [],
        "en",
        citation_map,
    )
    assert "[C1]" in answer and "verified" in answer
    assert "[C2]" in answer and "explicit" in answer
    assert "ambiguous" not in answer and "code absent" not in answer


@pytest.mark.asyncio
async def test_evidence_mode_returns_ranked_excerpts_without_calling_model(monkeypatch):
    import json

    async def retrieve(query, *, collection, **kwargs):
        if collection == "kb_shared_vas":
            preferred = chunk("v", "VAS 24")
            preferred.metadata["text"] = "A noncash transfer is disclosed separately. [C2]"
            return [preferred, chunk("v2", "VAS 24")]
        preferred = chunk("i", "IAS 7")
        preferred.metadata["text"] = "A transfer without cash is excluded from the statement."
        return [preferred]

    async def model(*args):
        pytest.fail("Evidence view must not call a model")
        yield ""

    monkeypatch.setattr(compare.settings, "compare_mode", "evidence")
    monkeypatch.setattr(compare, "retrieve", retrieve)
    monkeypatch.setattr(compare, "_call_llm", model)
    events = [
        json.loads(e.removeprefix("data: "))
        async for e in compare.IFRSCompareAgent().arun(
            query="VAS 24 and IAS 7", scope="shared", lang="en"
        )
    ]
    assert [e["type"] for e in events] == ["token", "citation", "citation", "final"]
    assert events[0]["delta"] == events[-1]["content"]
    assert [e["doc_id"] for e in events[1:3]] == ["v", "i"]
    assert "Source excerpts for review." in events[-1]["content"]
    assert "separately. ［C2]" in events[-1]["content"]
    assert "Fixture for VAS 24" not in events[-1]["content"]


@pytest.mark.asyncio
@pytest.mark.parametrize("vas_available", [True, False])
async def test_evidence_mode_reports_missing_standard_codes(monkeypatch, vas_available):
    import json

    async def retrieve(query, *, collection, **kwargs):
        if vas_available and collection == "kb_shared_vas":
            return [chunk("v", "VAS 05")]
        return []

    monkeypatch.setattr(compare.settings, "compare_mode", "evidence")
    monkeypatch.setattr(compare, "retrieve", retrieve)
    events = [
        json.loads(e.removeprefix("data: "))
        async for e in compare.IFRSCompareAgent().arun(
            query="VAS 05 và IFRS 17", scope="shared", lang="vi"
        )
    ]
    assert "IFRS 17" in events[-1]["content"]
    if vas_available:
        assert "Fixture for VAS 05" in events[-1]["content"]
        assert [e["doc_id"] for e in events if e["type"] == "citation"] == ["v"]
    else:
        assert len(events) == 1 and "VAS 05" in events[-1]["content"]
