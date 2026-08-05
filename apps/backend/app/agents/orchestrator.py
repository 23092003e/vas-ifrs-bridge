"""Top-level orchestrator — classifies intent and delegates to the correct agent."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Literal

from app.schemas.chat import ChatRequest

logger = logging.getLogger(__name__)

# Simple keyword-based intent classification (Phase 1).
# Replace with Qwen14B classifier in Phase 2.
_COMPARE_KEYWORDS = {"so sánh", "compare", "difference", "khác nhau", "vs", "versus", "đối chiếu"}
_MAPPING_KEYWORDS = {"mapping", "ánh xạ", "map account", "tài khoản", "chart of accounts"}
_REPORT_KEYWORDS = {"report", "báo cáo", "tổng hợp", "summary", "export"}
_ADJUSTMENT_KEYWORDS = {"adjustment", "điều chỉnh", "bút toán", "journal entry", "debit", "credit"}


def _classify_intent_keywords(text: str) -> str:
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


def _detect_query_lang(text: str) -> Literal["vi", "en"]:
    lower = text.lower()
    vi_diacritics = "àáảãạăắằẵặẳâấầẫậẩđèéẻẽẹêếềễệểìíỉĩịòóỏõọôốồỗộổơớờỡợởùúủũụưứừữựửỳýỷỹỵ"
    if any(c in vi_diacritics for c in lower):
        return "vi"
    # Common Vietnamese words without accents
    vi_no_accents = {"xin", "chao", "cam", "on", "viet", "nam", "ke", "toan", "thong", "tu"}
    words = set(lower.split())
    if words.intersection(vi_no_accents):
        return "vi"
    return "en"


INTENT_SYSTEM_PROMPT = """\
You are a routing assistant for a financial accounting platform bridging Vietnamese Accounting Standards (VAS) and IFRS.
Your task is to classify the user's intent into one of the following categories:
- "compare": If the user wants to compare, find differences, or contrast VAS and IFRS standards (e.g., "so sánh VAS 15 và IFRS 15", "khác biệt về ghi nhận doanh thu").
- "mapping": If the user wants to map general ledger accounts, configure charts of accounts, or establish relationships between accounts (e.g., "mapping tài khoản 242", "ánh xạ hệ thống tài khoản").
- "adjustment": If the user asks to generate, calculate, or propose adjusting journal entries, or discuss debit/credit adjustments (e.g., "tạo bút toán điều chỉnh thuê tài sản", "adjustment cho IFRS 16").
- "report": If the user wants to summarize, generate, export reports or financial statements (e.g., "báo cáo tài chính tổng hợp", "xuất báo cáo VAS-IFRS").
- "qa": For general questions, explanations of concepts, definitions, or queries that do not fit into the other categories.

Respond ONLY with a JSON object containing the classified intent, for example:
{"intent": "compare"}
Do NOT include any markdown formatting, code block markers (like ```json), or extra text.
"""


async def _classify_intent(text: str, hint: str | None) -> str:
    if hint:
        return hint
    return _classify_intent_keywords(text)


def _select_model(intent: str, reasoning: str) -> str:
    del intent  # Provider choice is controlled by the requested reasoning tier.
    return {
        "fast": "ollama",
        "balanced": "openai",
        "deep": "anthropic",
    }[reasoning]


class Orchestrator:
    """Classifies intent and delegates to the appropriate specialised agent."""

    async def run_stream(
        self,
        request: ChatRequest,
        *,
        tenant_id: str | None = None,
        tenant_collection: str | None = None,
    ) -> AsyncIterator[str]:
        intent = await _classify_intent(request.content, request.intent_hint)
        model = _select_model(intent, request.reasoning)

        lang = request.lang
        if lang == "auto":
            lang = _detect_query_lang(request.content)

        logger.info("orchestrator: intent=%s model=%s scope=%s lang=%s", intent, model, request.scope, lang)

        yield f"data: {json.dumps({'type': 'intent', 'intent': intent, 'model': model})}\n\n"

        from app.agents.base import AgentBase

        agent: AgentBase

        if intent == "compare":
            from app.agents.ifrs_compare_agent import IFRSCompareAgent

            agent = IFRSCompareAgent()
            async for token in agent.arun(
                query=request.content,
                lang=lang,
                tenant_id=tenant_id,
                tenant_collection=tenant_collection,
                scope=request.scope,
                model_hint=model,
            ):
                yield token
        elif intent == "mapping":
            from app.agents.gl_mapping_agent import GLMappingAgent

            agent = GLMappingAgent()
            async for token in agent.arun(
                query=request.content,
                lang=lang,
                tenant_id=tenant_id,
                tenant_collection=tenant_collection,
                scope=request.scope,
                model_hint=model,
            ):
                yield token
        elif intent == "adjustment":
            from app.agents.adjustment_agent import AdjustmentAgent

            agent = AdjustmentAgent()
            async for token in agent.arun(
                query=request.content,
                lang=lang,
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
                lang=lang,
                tenant_id=tenant_id,
                tenant_collection=tenant_collection,
                scope=request.scope,
                model_hint=model,
            ):
                yield token
