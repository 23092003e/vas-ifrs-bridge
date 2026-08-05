from __future__ import annotations

from typing import Any

import pytest

from app.core.audit import log_audit
from app.db.models import AuditLog


class _Db:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.committed = False

    def add(self, value: Any) -> None:
        self.added.append(value)

    async def commit(self) -> None:
        self.committed = True


@pytest.mark.asyncio
async def test_log_audit_persists_structured_record() -> None:
    db = _Db()

    await log_audit(
        db=db,
        tenant_id="174c7f5b-2cb9-4746-b1a7-b0c5e42591d1",
        user_id="user-1",
        action="POST /v1/documents/upload",
        resource_type="documents/upload",
        request_id="request-1",
    )

    assert db.committed is True
    assert isinstance(db.added[0], AuditLog)
    assert db.added[0].tenant_id == "174c7f5b-2cb9-4746-b1a7-b0c5e42591d1"
    assert db.added[0].action == "POST /v1/documents/upload"
