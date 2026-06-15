"""FastAPI dependency injection helpers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.core.tenant import TenantCtx
from app.db.session import AsyncSession


async def get_db(request: Request) -> AsyncSession:
    return request.state.db


async def get_tenant(request: Request) -> TenantCtx | None:
    return getattr(request.state, "tenant", None)


DB = Annotated[AsyncSession, Depends(get_db)]
Tenant = Annotated[TenantCtx | None, Depends(get_tenant)]
