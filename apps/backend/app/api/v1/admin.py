"""Admin-only endpoints for tenant and user management."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/tenants")
async def list_tenants() -> dict:
    """List all tenants (super-admin only)."""
    # TODO: query tenants table with admin guard
    return {"tenants": []}


@router.post("/tenants/{tenant_id}/provision")
async def provision_tenant(tenant_id: str) -> dict:
    """Provision Qdrant collection and storage for a new tenant."""
    # TODO: call tenant provisioner
    return {"tenant_id": tenant_id, "status": "provisioning"}
