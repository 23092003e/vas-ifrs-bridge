"""Top-level orchestrator — classifies intent and delegates to the correct agent."""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

from app.schemas.chat import ChatRequest

logger = logging.getLogger(__name__)

# Simple keyword-based intent classification (Phase 1).
# Replace with Qwen14B classifier in Phase 2.
_COMPARE_KEYWORDS = {
    "so sánh", "compare", "difference", "khác nhau", "vs", "versus", "đối chiếu"
}
_MAPPING_KEYWORDS = {
    "mapping", "ánh xạ", "map account", "tài khoản", "chart of accounts"
}
_REPORT_KEYWORDS = {
    "report", "báo cáo", "tổng hợp", "summary", "export"
}
_ADJUSTMENT_KEYWORDS = {
    "adjustment", "điều chỉnh", "bút toán", "journal entry", "debit", "credit"
}


def _classify_intent(text: str, hint: str | None) -> str:
    if hint:
        return hint
    lower = text.lower()
    if any(k in lower for k in _COMPARE_KEYWORDS):
        return "compare"
    if any(k in lower for k in _MAPPING_KEYWORDS):
        return "mapping"
    if any(k in lower for k in _REPORT_KEYWORDS):
        return "report"
    if any(k in lower for k in _ADJUSTMENT_KEYWORDS):
        return "adjustment"
    return "qa"


def _select_model(intent: str, reasoning: str) -> str:
    if reasoning == "deep":
        return "claude"
    if intent in {"compare", "report"}:
        return "openai"
    return "qwen"


class Orchestrator:
    """Classifies intent and delegates to the appropriate specialised agent."""

    async def run_stream(
        self,
        request: ChatRequest,
        *,
        tenant_id: str | None = None,
        tenant_collection: str | None = None,
    ) -> AsyncIterator[str]:
        intent = _classify_intent(request.content, request.intent_hint)
        model = _select_model(intent, request.reasoning)

        logger.info(
            "orchestrator: intent=%s model=%s scope=%s", intent, model, request.scope
        )

        yield f"data: {json.dumps({'type': 'intent', 'intent': intent, 'model': model})}\n\n"

        from app.agents.base import AgentBase
        agent: AgentBase

        if intent == "compare":
            from app.agents.ifrs_compare_agent import IFRSCompareAgent
            agent = IFRSCompareAgent()
            async for token in agent.arun(
                query=request.content,
                lang=request.lang if request.lang != "auto" else "vi",
                tenant_id=tenant_id,
                tenant_collection=tenant_collection,
                model_hint=model,
            ):
                yield token
        elif intent == "mapping":
            from app.agents.gl_mapping_agent import GLMappingAgent
            agent = GLMappingAgent()
            async for token in agent.arun(
                query=request.content,
                lang=request.lang if request.lang != "auto" else "vi",
                tenant_id=tenant_id,
                tenant_collection=tenant_collection,
                model_hint=model,
            ):
                yield token
        elif intent == "adjustment":
            from app.agents.adjustment_agent import AdjustmentAgent
            agent = AdjustmentAgent()
            async for token in agent.arun(
                query=request.content,
                lang=request.lang if request.lang != "auto" else "vi",
                tenant_id=tenant_id,
                tenant_collection=tenant_collection,
                model_hint=model,
            ):
                yield token
        else:
            # qa / fallback
            from app.agents.retrieval_agent import RetrievalAgent
            agent = RetrievalAgent()
            async for token in agent.arun(
                query=request.content,
                lang=request.lang if request.lang != "auto" else "vi",
                tenant_id=tenant_id,
                tenant_collection=tenant_collection,
                scope=request.scope,
                model_hint=model,
            ):
                yield token
