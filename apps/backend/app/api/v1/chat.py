"""Chat streaming endpoints."""
from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.agents.orchestrator import Orchestrator
from app.core.tenant import TenantCtx
from app.schemas.chat import ChatRequest

router = APIRouter()
_orchestrator = Orchestrator()


@router.post("/stream")
async def chat_stream(body: ChatRequest, request: Request) -> StreamingResponse:
    """
    Stream token-by-token SSE response.
    Events: token | citation | intent | final | error
    """
    tenant: TenantCtx | None = getattr(request.state, "tenant", None)

    async def _generate() -> AsyncIterator[bytes]:
        try:
            async for event in _orchestrator.run_stream(
                body,
                tenant_id=tenant.id if tenant else None,
                tenant_collection=tenant.qdrant_collection if tenant else None,
            ):
                yield event.encode()
        except Exception as exc:
            err = json.dumps({"type": "error", "message": str(exc)})
            yield f"data: {err}\n\n".encode()

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
