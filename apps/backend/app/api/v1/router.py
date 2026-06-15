"""Central v1 API router — aggregates all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from . import adjustments, admin, chat, documents, gl, kb, mapping, reports

router = APIRouter()
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(kb.router, prefix="/kb", tags=["kb"])
router.include_router(gl.router, prefix="/gl", tags=["gl"])
router.include_router(mapping.router, prefix="/mappings", tags=["mapping"])
router.include_router(adjustments.router, prefix="/adjustments", tags=["adjustments"])
router.include_router(reports.router, prefix="/reports", tags=["reports"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
