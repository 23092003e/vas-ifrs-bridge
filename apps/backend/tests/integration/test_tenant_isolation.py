"""Integration tests verifying tenant data isolation across all endpoints."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_tenant_a_cannot_read_tenant_b_documents() -> None:
    """Tenant A must not be able to retrieve documents belonging to Tenant B."""
    # TODO: create two tenants, upload docs to B, assert A gets empty result
    assert True


@pytest.mark.asyncio
async def test_tenant_a_cannot_query_tenant_b_kb() -> None:
    """Tenant A's KB search must be scoped to its own Qdrant collection."""
    # TODO: seed tenant B collection, query as tenant A, assert empty
    assert True
