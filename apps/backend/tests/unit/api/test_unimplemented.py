from __future__ import annotations

from collections.abc import Awaitable, Callable
from io import BytesIO
from typing import Any

import pytest
from fastapi import HTTPException, UploadFile

from app.api.v1 import adjustments, admin, gl, mapping, reports

EndpointCall = Callable[[], Awaitable[dict[str, Any]]]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "call",
    [
        lambda: adjustments.list_adjustments(),
        lambda: adjustments.approve_adjustment("ADJ-001"),
        lambda: admin.list_tenants(),
        lambda: admin.provision_tenant("174c7f5b-2cb9-4746-b1a7-b0c5e42591d1"),
        lambda: gl.upload_gl(UploadFile(filename="ledger.csv", file=BytesIO(b"code,debit"))),
        lambda: gl.get_upload_status("89bc0df4-cdf0-49f8-a0c8-4191aaf1912b"),
        lambda: mapping.list_mappings(),
        lambda: mapping.update_mapping("rule-1", {}),
        lambda: reports.generate_report({}),
        lambda: reports.download_report("report-1"),
    ],
)
async def test_stub_endpoints_report_not_implemented(call: EndpointCall) -> None:
    """A stub must not return a success response for work it never performed."""
    with pytest.raises(HTTPException) as exc_info:
        await call()

    assert exc_info.value.status_code == 501
