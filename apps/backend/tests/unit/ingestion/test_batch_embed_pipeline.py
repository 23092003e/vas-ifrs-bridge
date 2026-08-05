from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from ingestion.pipelines.embedders import batch_embed
from ingestion.pipelines.parsers import unstructured_runner


def _isolate_processed_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module_path = tmp_path / "ingestion" / "pipelines" / "embedders" / "batch_embed.py"
    module_path.parent.mkdir(parents=True)
    monkeypatch.setattr(batch_embed, "__file__", str(module_path))


def _stub_vector_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    *,
    vectors: list[list[float]],
) -> list[list[dict[str, Any]]]:
    async def fake_embed_batch(*_args: Any, **_kwargs: Any) -> list[list[float]]:
        return vectors

    batches: list[list[dict[str, Any]]] = []
    monkeypatch.setattr(batch_embed, "embed_batch_with_retry", fake_embed_batch)
    monkeypatch.setattr(batch_embed, "_get_qdrant", lambda: object())
    monkeypatch.setattr(batch_embed, "ensure_collection", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        batch_embed,
        "upsert_batch",
        lambda _client, _collection, points: batches.append(points),
    )
    return batches


@pytest.mark.asyncio
async def test_reingesting_document_reuses_point_ids_and_current_timestamp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Catches random point IDs and stale ingestion timestamps on repeat runs."""
    _isolate_processed_output(monkeypatch, tmp_path)
    batches = _stub_vector_boundaries(monkeypatch, vectors=[[0.1, 0.2, 0.3]])
    document = {
        "source_path": "ingestion/raw/shared/ifrs/ifrs-1.txt",
        "filename": "ifrs-1.txt",
        "lang": "en",
        "standard_code": "IFRS-1",
        "text": "First-time adoption requirements.",
        "sections": [],
    }

    await batch_embed.ingest([document], collection="kb_shared_ifrs", scope="shared")
    first_point = batches[-1][0]
    await batch_embed.ingest([document], collection="kb_shared_ifrs", scope="shared")
    second_point = batches[-1][0]

    assert first_point["id"] == second_point["id"]
    ingested_at = datetime.fromisoformat(second_point["ingested_at"])
    assert ingested_at.tzinfo is not None
    assert abs((datetime.now(UTC) - ingested_at).total_seconds()) < 10


@pytest.mark.asyncio
async def test_ingest_rejects_missing_vectors_before_qdrant_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Catches silent zip truncation when an embedding provider drops vectors."""
    _isolate_processed_output(monkeypatch, tmp_path)
    batches = _stub_vector_boundaries(monkeypatch, vectors=[])
    document = {
        "source_path": "ingestion/raw/shared/vas/vas-1.txt",
        "filename": "vas-1.txt",
        "lang": "vi",
        "standard_code": "VAS-1",
        "text": "Chuẩn mực chung.",
        "sections": [],
    }

    with pytest.raises(ValueError, match="embedding count"):
        await batch_embed.ingest([document], collection="kb_shared_vas", scope="shared")

    assert batches == []


@pytest.mark.asyncio
async def test_tenant_scope_requires_tenant_id() -> None:
    """Catches private documents being ingested without a tenant boundary."""
    with pytest.raises(ValueError, match="tenant_id"):
        await batch_embed.ingest(
            [],
            collection="tenant_missing",
            scope="tenant",
            tenant_id=None,
            dry_run=True,
        )


def test_load_parsed_docs_finds_nested_artifacts(tmp_path: Path) -> None:
    nested = tmp_path / "standards" / "ifrs"
    nested.mkdir(parents=True)
    (nested / "ifrs-1.json").write_text(
        '{"filename": "ifrs-1.pdf", "text": "requirements"}',
        encoding="utf-8",
    )

    docs = batch_embed.load_parsed_docs(tmp_path)

    assert [doc["filename"] for doc in docs] == ["ifrs-1.pdf"]


def test_load_parsed_docs_rejects_corrupt_artifacts(tmp_path: Path) -> None:
    (tmp_path / "broken.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(RuntimeError, match="failed to load 1 parsed document"):
        batch_embed.load_parsed_docs(tmp_path)


def test_load_raw_docs_reports_parser_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "broken.txt").write_text("content", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "unstructured_runner", unstructured_runner)

    def fail_parse(_path: Path) -> dict[str, Any]:
        raise RuntimeError("parser exploded")

    monkeypatch.setattr(unstructured_runner, "parse_document", fail_parse)

    with pytest.raises(RuntimeError, match="failed to parse 1 raw document"):
        batch_embed.load_raw_docs(tmp_path)


def test_standalone_parser_extracts_and_normalizes_visible_html(tmp_path: Path) -> None:
    source = tmp_path / "ifrs-1.html"
    source.write_text(
        "<html><head><style>.hidden {}</style></head>"
        "<body><h1>IFRS 1</h1><script>ignore()</script><p>First\u00a0time</p></body></html>",
        encoding="utf-8",
    )

    parsed = unstructured_runner.parse_document(source)

    assert parsed["text"] == "IFRS 1\n\nFirst time"
    assert parsed["standard_code"] == "IFRS-1"


def test_standalone_parser_normalizes_plain_text(tmp_path: Path) -> None:
    source = tmp_path / "vas-01.txt"
    source.write_text("Chuẩn\u00a0mực\r\n\r\n\r\nchung", encoding="utf-8")

    parsed = unstructured_runner.parse_document(source)

    assert parsed["text"] == "Chuẩn mực\n\nchung"


@pytest.mark.parametrize("suffix", [".doc", ".xls"])
def test_parse_document_rejects_legacy_office_formats(
    tmp_path: Path,
    suffix: str,
) -> None:
    source = tmp_path / f"legacy{suffix}"
    source.write_bytes(b"legacy office data")

    with pytest.raises(ValueError, match="unsupported file type"):
        unstructured_runner.parse_document(source)
