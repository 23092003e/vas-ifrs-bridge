"""Chat streaming and conversation management endpoints."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import selectinload

from app.agents.orchestrator import Orchestrator
from app.core.errors import QdrantUnavailableError
from app.core.tenant import TenantCtx
from app.db.models import Conversation
from app.db.models import Message as DbMessage
from app.deps import DB
from app.schemas.chat import ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter()
_orchestrator = Orchestrator()


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    request: Request,
    db: DB,
) -> StreamingResponse:
    """
    Stream token-by-token SSE response and persist conversation history.
    Events: token | citation | intent | final | error
    """
    user_id = getattr(request.state, "user_id", "dev-user")
    tenant: TenantCtx | None = getattr(request.state, "tenant", None)
    tenant_id = tenant.id if tenant else None

    # 1. Resolve or create conversation
    conversation_id = str(body.conversation_id) if body.conversation_id else None
    if conversation_id:
        # Check if conversation exists for this user
        stmt = select(Conversation).where(
            Conversation.id == str(conversation_id),
            Conversation.user_id == user_id,
            Conversation.tenant_id == tenant_id,
        )
        res = await db.execute(stmt)
        conv = res.scalar_one_or_none()
        if not conv:
            conversation_id = None

    if not conversation_id:
        # Create new conversation
        from uuid import uuid4
        conversation_id = str(uuid4())
        title = body.content[:100]
        if len(body.content) > 100:
            title += "..."
        conv = Conversation(
            id=conversation_id,
            user_id=user_id,
            tenant_id=tenant_id,
            title=title,
        )
        db.add(conv)
        await db.commit()

    # 2. Save user message
    user_msg = DbMessage(
        conversation_id=conversation_id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)
    await db.commit()

    async def _generate() -> AsyncIterator[bytes]:
        from app.db.session import AsyncSessionLocal

        accumulated_tokens = []
        accumulated_citations = []
        model_used = None
        final_content: str | None = None

        try:
            async for event in _orchestrator.run_stream(
                body,
                tenant_id=tenant_id,
                tenant_collection=tenant.qdrant_collection if tenant else None,
                conversation_id=conversation_id,
            ):
                if event.startswith("data: "):
                    try:
                        data = json.loads(event.removeprefix("data: ").strip())
                        if data.get("type") == "token":
                            accumulated_tokens.append(data.get("delta", ""))
                        elif data.get("type") == "citation":
                            accumulated_citations.append({
                                "key": data.get("key"),
                                "doc_id": data.get("doc_id"),
                                "chunk_id": data.get("chunk_id"),
                                "snippet": data.get("snippet"),
                                "standard_code": data.get("standard_code"),
                            })
                        elif data.get("type") == "intent":
                            model_used = data.get("model")
                        elif data.get("type") == "final":
                            content = data.get("content")
                            if isinstance(content, str):
                                final_content = content
                            # Emit one enriched final event below with conversation_id.
                            continue
                    except (AttributeError, json.JSONDecodeError, TypeError) as e:
                        logger.error("Error parsing event during streaming: %s", e)

                yield event.encode()

            # Save assistant message on successful stream completion
            full_response = (
                final_content if final_content is not None else "".join(accumulated_tokens)
            )
            if full_response:
                async with AsyncSessionLocal() as db_session:
                    # Update conversation updated_at
                    await db_session.execute(
                        update(Conversation)
                        .where(Conversation.id == conversation_id)
                        .values(updated_at=func.now())
                    )

                    assistant_msg = DbMessage(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=full_response,
                        citations=accumulated_citations,
                        model_used=model_used,
                    )
                    db_session.add(assistant_msg)
                    await db_session.commit()

            # Always emit a final event with conversation_id
            final_payload = {
                "type": "final",
                "content": full_response,
                "conversation_id": conversation_id,
            }
            yield f"data: {json.dumps(final_payload)}\n\n".encode()

        except QdrantUnavailableError:
            logger.warning("Chat stream could not retrieve knowledge", exc_info=True)
            err = json.dumps({"type": "error", "message": "Knowledge retrieval is temporarily unavailable"})
            yield f"data: {err}\n\n".encode()
        except Exception as exc:
            logger.exception("Chat stream failed", exc_info=exc)
            err = json.dumps({"type": "error", "message": "Unable to complete chat stream"})
            yield f"data: {err}\n\n".encode()

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations")
async def list_conversations(request: Request, db: DB) -> dict:
    """List all conversations for the authenticated user and tenant."""
    user_id = getattr(request.state, "user_id", "dev-user")
    tenant = getattr(request.state, "tenant", None)
    tenant_id = tenant.id if tenant else None

    stmt = (
        select(Conversation)
        .where(
            Conversation.user_id == user_id,
            Conversation.tenant_id == tenant_id,
        )
        .order_by(Conversation.updated_at.desc())
    )

    result = await db.execute(stmt)
    conversations = result.scalars().all()

    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in conversations
        ]
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, request: Request, db: DB) -> dict:
    """Get conversation details with all messages."""
    user_id = getattr(request.state, "user_id", "dev-user")
    tenant: TenantCtx | None = getattr(request.state, "tenant", None)
    tenant_id = tenant.id if tenant else None

    stmt = (
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.tenant_id == tenant_id,
        )
        .options(selectinload(Conversation.messages))
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "citations": m.citations or [],
                "created_at": m.created_at.isoformat(),
            }
            for m in conversation.messages
        ]
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, request: Request, db: DB) -> dict:
    """Delete a conversation and its messages."""
    user_id = getattr(request.state, "user_id", "dev-user")
    tenant: TenantCtx | None = getattr(request.state, "tenant", None)
    tenant_id = tenant.id if tenant else None

    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
        Conversation.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.execute(delete(DbMessage).where(DbMessage.conversation_id == conversation_id))
    await db.execute(delete(Conversation).where(Conversation.id == conversation_id))
    await db.commit()

    return {"status": "success"}
