from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app import main


class _Db:
    async def execute(self, statement: Any) -> None:
        return None


class _FailingDb:
    async def execute(self, statement: Any) -> None:
        raise RuntimeError("database unavailable")


@pytest.mark.asyncio
async def test_readiness_checks_database() -> None:
    assert hasattr(main, "readiness")

    assert await main.readiness(SimpleNamespace(state=SimpleNamespace(db=_Db()))) == {
        "status": "ready"
    }

    with pytest.raises(HTTPException) as exc_info:
        await main.readiness(SimpleNamespace(state=SimpleNamespace(db=_FailingDb())))

    assert exc_info.value.status_code == 503


def test_metrics_endpoint_exposes_prometheus_payload() -> None:
    assert hasattr(main, "metrics")

    response = main.metrics()

    assert response.media_type == "text/plain"
    assert b"vasifrs_requests_total" in response.body
