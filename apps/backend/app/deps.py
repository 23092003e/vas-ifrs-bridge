"""FastAPI dependency injection helpers."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from app.db.session import AsyncSession
from app.core.tenant import TenantCtx


async def get_db(request: Request) -> AsyncSession:
    return request.state.db


async def get_tenant(request: Request) -> TenantCtx:
    return request.state.tenant


DB = Annotated[AsyncSession, Depends(get_db)]
Tenant = Annotated[TenantCtx, Depends(get_tenant)]
