from __future__ import annotations

import inspect
from io import BytesIO
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException, UploadFile
from starlette.requests import Request

from app.api.v1 import documents


def _request() -> Request:
    request = Request({"type": "http", "method": "POST", "path": "/v1/documents/upload", "headers": []})
    request.state.tenant = SimpleNamespace(
        id="174c7f5b-2cb9-4746-b1a7-b0c5e42591d1",
        qdrant_collection="tenant_test",
    )
    return request


class _Db:
    def add(self, document: Any) -> None:
        self.document = document

    async def commit(self) -> None:
        return None

    async def refresh(self, document: Any) -> None:
        document.id = "89bc0df4-cdf0-49f8-a0c8-4191aaf1912b"


class _BackgroundTasks:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, dict[str, Any]]] = []

    def add_task(self, function: Any, **kwargs: Any) -> None:
        self.calls.append((function, kwargs))


class _FailingDb(_Db):
    def __init__(self) -> None:
        self.rolled_back = False

    async def commit(self) -> None:
        raise RuntimeError("database unavailable")

    async def rollback(self) -> None:
        self.rolled_back = True


@pytest.mark.asyncio
async def test_upload_rejects_filename_that_escapes_tenant_storage(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A client-controlled filename must never select a path outside its tenant directory."""
    workdir = tmp_path / "work"
    workdir.mkdir()
    monkeypatch.chdir(workdir)

    upload = UploadFile(filename="../../escaped.pdf", file=BytesIO(b"not a real pdf"))

    with pytest.raises(HTTPException) as exc_info:
        await documents.upload_document(upload, _request(), _Db(), _BackgroundTasks())

    assert exc_info.value.status_code == 400
    assert not (workdir / "storage" / "escaped.pdf").exists()


@pytest.mark.asyncio
async def test_upload_stops_and_removes_partial_file_when_size_limit_is_exceeded(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workdir = tmp_path / "work"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    monkeypatch.setattr(documents, "MAX_UPLOAD_SIZE_BYTES", 8, raising=False)

    upload = UploadFile(filename="large.pdf", file=BytesIO(b"123456789"))

    with pytest.raises(HTTPException) as exc_info:
        await documents.upload_document(upload, _request(), _Db(), _BackgroundTasks())

    assert exc_info.value.status_code == 413
    assert list((workdir / "storage").rglob("*large.pdf")) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("filename", ["payload.exe", "legacy.xls"])
async def test_upload_rejects_unsupported_file_extension(
    filename: str, tmp_path: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    upload = UploadFile(filename=filename, file=BytesIO(b"binary"))

    with pytest.raises(HTTPException) as exc_info:
        await documents.upload_document(upload, _request(), _Db(), _BackgroundTasks())

    assert exc_info.value.status_code == 415


@pytest.mark.asyncio
async def test_valid_upload_schedules_managed_ingestion_task(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert "background_tasks" in inspect.signature(documents.upload_document).parameters
    monkeypatch.chdir(tmp_path)
    tasks = _BackgroundTasks()

    result = await documents.upload_document(
        UploadFile(filename="standard.pdf", file=BytesIO(b"pdf")),
        _request(),
        _Db(),
        tasks,
    )

    assert result["status"] == "pending"
    assert tasks.calls[0][0] is documents.ingest_document
    assert tasks.calls[0][1]["tenant_id"] == "174c7f5b-2cb9-4746-b1a7-b0c5e42591d1"


@pytest.mark.asyncio
async def test_upload_removes_file_and_rolls_back_when_database_write_fails(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    db = _FailingDb()

    with pytest.raises(HTTPException) as exc_info:
        await documents.upload_document(
            UploadFile(filename="standard.pdf", file=BytesIO(b"pdf")),
            _request(),
            db,
            _BackgroundTasks(),
        )

    assert exc_info.value.status_code == 503
    assert db.rolled_back is True
    assert list((tmp_path / "storage").rglob("*standard.pdf")) == []
