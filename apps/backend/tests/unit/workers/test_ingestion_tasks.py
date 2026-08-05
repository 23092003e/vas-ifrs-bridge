from __future__ import annotations

from typing import Any

from app.workers import ingestion_tasks


def test_celery_task_runs_real_ingestion(monkeypatch: Any) -> None:
    assert hasattr(ingestion_tasks, "ingest_document")
    calls: list[dict[str, str]] = []

    async def fake_ingest(**kwargs: str) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(ingestion_tasks, "ingest_document", fake_ingest)

    result = ingestion_tasks.ingest_document_task.run(
        "document-1",
        "/tmp/document.pdf",
        "tenant-1",
    )

    assert calls == [
        {
            "document_id": "document-1",
            "local_path": "/tmp/document.pdf",
            "tenant_id": "tenant-1",
        }
    ]
    assert result == {"document_id": "document-1", "status": "done"}
