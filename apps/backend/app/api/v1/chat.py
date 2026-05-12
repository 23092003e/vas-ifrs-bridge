"""Chat streaming endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest

router = APIRouter()


@router.post("/stream")
async def chat_stream(body: ChatRequest) -> StreamingResponse:
    """Stream token-by-token SSE response from the orchestrator."""
    # TODO: delegate to orchestrator.run_stream()
    async def _gen():
        yield "data: {}\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")
