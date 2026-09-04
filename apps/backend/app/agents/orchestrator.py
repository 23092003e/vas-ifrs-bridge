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
    
    # Fast path: keyword matching
    keyword_intent = _classify_intent_keywords(text)
    if keyword_intent != "qa":
        return keyword_intent
        
    # Slow path: LLM confirmation for ambiguous queries
    try:
        import re

        from app.llm.router import complete_chat

        response = await complete_chat(
            system=INTENT_SYSTEM_PROMPT,
            user=text,
            model_hint="fast",
            max_tokens=100,
        )
        # Check regex match first in case response contains markdown or extra formatting
        match = re.search(r'["\']intent["\']\s*:\s*["\'](compare|mapping|adjustment|report|qa)["\']', response, re.IGNORECASE)
        if match:
            return match.group(1).lower()

        try:
            data = json.loads(response)
            intent = data.get("intent", "qa")
            if intent in {"compare", "mapping", "adjustment", "report", "qa"}:
                return intent
        except json.JSONDecodeError:
            pass
    except Exception as e:  # noqa: BLE001 - fallback to default QA intent
        logger.warning("LLM intent classification failed: %s, falling back to 'qa'", e)
        
    return "qa"


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
        conversation_id: str | None = None,
    ) -> AsyncIterator[str]:
        intent = await _classify_intent(request.content, request.intent_hint)
        model = _select_model(intent, request.reasoning)

        lang = request.lang
        if lang == "auto":
            lang = _detect_query_lang(request.content)

        logger.info("orchestrator: intent=%s model=%s scope=%s lang=%s", intent, model, request.scope, lang)

        yield f"data: {json.dumps({'type': 'intent', 'intent': intent, 'model': model})}\n\n"

        history: list[dict[str, str]] = []
        if conversation_id:
            try:
                from sqlalchemy import select

                from app.db.models import Message as DbMessage
                from app.db.session import AsyncSessionLocal
                async with AsyncSessionLocal() as db_session:
                    stmt = select(DbMessage).where(
                        DbMessage.conversation_id == conversation_id
                    ).order_by(DbMessage.created_at.desc()).limit(10)
                    res = await db_session.execute(stmt)
                    db_messages = res.scalars().all()
                    for m in reversed(db_messages):
                        if m.role in {"user", "assistant"}:
                            history.append({"role": m.role, "content": m.content})

                    # Since chat_stream saves the current user message in DB before calling orchestrator,
                    # pop the trailing user message if it matches request.content so it is not sent twice
                    if history and history[-1]["role"] == "user" and history[-1]["content"] == request.content:
                        history.pop()
            except Exception as e:  # noqa: BLE001 - history retrieval is best-effort
                logger.warning("Failed to fetch conversation history: %s", e)

        from app.agents.base import AgentBase

        agent: AgentBase

        # We will pass history to agents in Stage 4, but for now we'll just prepare it
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
                messages=history,
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
                messages=history,
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
                scope=request.scope,
                model_hint=model,
                messages=history,
            ):
                yield token
        elif intent == "report":
            from app.agents.report_agent import ReportAgent
            
            agent = ReportAgent()
            async for token in agent.arun(
                query=request.content,
                lang=lang,
                tenant_id=tenant_id,
                tenant_collection=tenant_collection,
                scope=request.scope,
                model_hint=model,
                messages=history,
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
                messages=history,
            ):
                yield token
