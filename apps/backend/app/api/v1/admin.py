"""Admin-only endpoints for tenant and user management."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/tenants")
async def list_tenants() -> dict:
    """List all tenants (super-admin only)."""
    raise HTTPException(status_code=501, detail="Tenant listing is not implemented")


@router.post("/tenants/{tenant_id}/provision")
async def provision_tenant(tenant_id: str) -> dict:
    """Provision Qdrant collection and storage for a new tenant."""
    raise HTTPException(status_code=501, detail="Tenant provisioning is not implemented")
