"""Top-level orchestrator — classifies intent and delegates to the correct agent."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

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

    try:
        import re

        from app.llm.providers.gemini import stream_chat

        # Call Gemini in a non-streaming fashion by joining stream tokens
        tokens = []
        async for token in stream_chat(
            system=INTENT_SYSTEM_PROMPT,
            user=text,
            model_hint="fast",
            temperature=0.0,
            max_tokens=50
        ):
            tokens.append(token)

        response_text = "".join(tokens).strip()

        # Clean markdown formatting if LLM included it
        if response_text.startswith("```"):
            response_text = re.sub(r"^```[a-zA-Z]*\n|```$", "", response_text, flags=re.MULTILINE).strip()

        data = json.loads(response_text)
        intent = data.get("intent")
        if intent in {"compare", "mapping", "report", "adjustment", "qa"}:
            return intent
        else:
            logger.warning("orchestrator: invalid intent returned by LLM classifier: %s", intent)
    except Exception as exc:
        logger.warning("orchestrator: LLM intent classification failed: %s. Falling back to keywords.", exc)

    return _classify_intent_keywords(text)


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
        intent = await _classify_intent(request.content, request.intent_hint)
        model = _select_model(intent, request.reasoning)

        logger.info("orchestrator: intent=%s model=%s scope=%s", intent, model, request.scope)

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
