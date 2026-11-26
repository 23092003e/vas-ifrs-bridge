from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from fastapi import HTTPException

from app.api.v1 import admin

EndpointCall = Callable[[], Awaitable[dict[str, Any]]]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "call",
    [
        lambda: admin.list_tenants(),
        lambda: admin.provision_tenant("174c7f5b-2cb9-4746-b1a7-b0c5e42591d1"),
    ],
)
async def test_stub_endpoints_report_not_implemented(call: EndpointCall) -> None:
    """A stub must not return a success response for work it never performed."""
    with pytest.raises(HTTPException) as exc_info:
        await call()

    assert exc_info.value.status_code == 501
