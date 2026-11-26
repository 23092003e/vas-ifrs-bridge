"""Agent that produces a structured VAS ↔ IFRS standard comparison."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator
from dataclasses import replace
from typing import Any

from app.agents.base import AgentBase
from app.core.errors import QdrantUnavailableError
from app.rag.citation import (
    Citation,
    build_citation_list,
    extract_used_keys,
    wrap_chunks_for_prompt,
)
from app.rag.retriever import DENSE_K, RetrievedChunk, retrieve
from app.settings import settings

logger = logging.getLogger(__name__)


_STANDARD = re.compile(r"(?<!\w)(VAS|IAS|IFRS)[\s_-]*0*(\d{1,2})(?!\w)", re.IGNORECASE)
_SIDE_NAMES = ("VAS", "IFRS")
_PER_SIDE = 5


def _standard_ids(text: str) -> set[tuple[str, int]]:
    return {(family.upper(), int(number)) for family, number in _STANDARD.findall(text)}


def _aliases(ids: set[tuple[str, int]]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                f"{family}{separator}{number}"
                for family, index in ids
                for separator in (" ", "", "-", "_")
                for number in (str(index), f"{index:02d}")
            }
        )
    )


def _side(standard_id: tuple[str, int]) -> str:
    return "VAS" if standard_id[0] == "VAS" else "IFRS"


async def _retrieve_sides(
    query: str,
    *,
    tenant_collection: str | None,
    tenant_id: str | None,
    scope: str,
    lang: str,
) -> tuple[list[RetrievedChunk], dict[str, set[str]], list[str]]:
    if scope not in {"shared", "tenant", "both"}:
        raise ValueError(f"Invalid retrieval scope: {scope}")
    if scope == "tenant" and not (tenant_collection and tenant_id):
        raise ValueError("tenant_collection and tenant_id are required for tenant scope")

    requested = _standard_ids(query)
    wanted = {side: {std for std in requested if _side(std) == side} for side in _SIDE_NAMES}
    plans = []
    for side in _SIDE_NAMES:
        groups = [{standard} for standard in sorted(wanted[side])[:_PER_SIDE]] or [set()]
        for group in groups:
            if scope in {"shared", "both"}:
                plans.append(
                    (
                        side,
                        retrieve(
                            query,
                            collection=f"kb_shared_{side.lower()}",
                            scope="shared",
                            lang=lang,
                            standard_codes=_aliases(group),
                            k=_PER_SIDE,
                        ),
                    )
                )
            if scope in {"tenant", "both"} and tenant_collection and tenant_id:
                plans.append(
                    (
                        side,
                        retrieve(
                            query,
                            collection=tenant_collection,
                            tenant_id=tenant_id,
                            scope="tenant",
                            lang=lang,
                            standard_codes=_aliases(group),
                            k=DENSE_K,
                            skip_rerank=True,
                        ),
                    )
                )
    results = await asyncio.gather(*(search for _, search in plans), return_exceptions=True)
    if all(isinstance(result, Exception) for result in results):
        raise QdrantUnavailableError("All comparison source requests failed")

    selected: dict[str, list[tuple[RetrievedChunk, tuple[str, int]]]] = {
        side: [] for side in _SIDE_NAMES
    }
    seen: set[tuple[str, str, str]] = set()
    for (side, _), result in zip(plans, results, strict=True):
        if isinstance(result, Exception):
            logger.warning("compare retrieval partial failure for %s: %s", side, result)
            continue
        if isinstance(result, BaseException):
            raise result
        for chunk in result:
            identifiers = _standard_ids(str(chunk.metadata.get("standard_code") or ""))
            if len(identifiers) != 1:
                continue
            standard_id = next(iter(identifiers))
            identity = (side, chunk.doc_id, chunk.id)
            if (
                _side(standard_id) != side
                or (wanted[side] and standard_id not in wanted[side])
                or identity in seen
            ):
                continue
            seen.add(identity)
            selected[side].append((chunk, standard_id))

    chunks: list[RetrievedChunk] = []
    keys: dict[str, set[str]] = {side: set() for side in _SIDE_NAMES}
    missing: list[str] = []
    for side in _SIDE_NAMES:
        ranked = selected[side]
        first_by_standard: dict[tuple[str, int], int] = {}
        for i, (_, standard_id) in enumerate(ranked):
            first_by_standard.setdefault(standard_id, i)
        # Reserve room for each requested code before filling from the ranked results.
        first = sorted(i for std, i in first_by_standard.items() if std in wanted[side])
        positions = [*first, *(i for i in range(len(ranked)) if i not in first)]
        visible = set()
        for i in positions[:_PER_SIDE]:
            chunk, standard_id = ranked[i]
            key = f"C{len(chunks) + 1}"
            chunks.append(replace(chunk, citation_key=key))
            keys[side].add(key)
            visible.add(standard_id)
        missing.extend(
            f"{family} {index:02d}" if family == "VAS" else f"{family} {index}"
            for family, index in sorted(wanted[side] - visible)
        )
        if not wanted[side] and not keys[side]:
            missing.append(side)
    return chunks, keys, missing


_CLAIM = re.compile(
    r"^\s*(?:[-*]\s+)?(?:\*\*)?((?:VAS|IAS|IFRS)(?:[\s_-]*\d{1,2})?|COMPARE)"
    r"(?:\*\*)?\s*:\s*(.+)$",
    re.IGNORECASE,
)
_STANDARD_CITATION = re.compile(r"\[((?:VAS|IAS|IFRS)[\s_-]*\d{1,2})\]", re.IGNORECASE)


def _grounded_answer(
    raw: str,
    keys: dict[str, set[str]],
    missing: list[str],
    lang: str,
    citation_map: dict[str, Citation] | None = None,
) -> str:
    standard_keys: dict[tuple[str, int], list[str]] = {}
    for key, citation in (citation_map or {}).items():
        for standard in _standard_ids(citation.standard_code or ""):
            standard_keys.setdefault(standard, []).append(key)

    def resolve(match: re.Match[str]) -> str:
        standard = next(iter(_standard_ids(match[1])))
        matches = standard_keys.get(standard, [])
        return f"[{matches[0]}]" if len(matches) == 1 else match[0]

    claims = []
    labels = {
        "VAS": "VAS",
        "IFRS": "IFRS",
        "COMPARE": "Comparison" if lang == "en" else "Đối chiếu",
    }
    for line in raw.splitlines():
        match = _CLAIM.fullmatch(line)
        if not match:
            continue
        label = match[1].upper()
        side = "VAS" if label.startswith("VAS") else "COMPARE" if label == "COMPARE" else "IFRS"
        claim = _STANDARD_CITATION.sub(resolve, match[2].strip())
        sources = extract_used_keys(claim)
        if not sources or _STANDARD_CITATION.search(claim):
            continue
        if side == "COMPARE":
            if (
                missing
                or not sources <= (keys["VAS"] | keys["IFRS"])
                or not all(sources & keys[standard] for standard in _SIDE_NAMES)
            ):
                continue
        else:
            requested = _standard_ids(label)
            allowed = set(standard_keys.get(next(iter(requested)), [])) if requested else keys[side]
            if not sources <= (allowed & keys[side]):
                continue
        claims.append(f"**{labels[side]}** — {claim}")

    if missing:
        claims.append(_missing_sources(missing, lang))
    if not claims:
        return (
            "The available sources did not support a comparison with verifiable citations."
            if lang == "en"
            else "Chưa đủ căn cứ để đưa ra kết luận đối chiếu có thể kiểm chứng."
        )
    return "\n\n".join(claims)


def _missing_sources(missing: list[str], lang: str) -> str:
    codes = ", ".join(missing)
    return (
        f"Sources are missing for {codes}. A full comparison is unavailable."
        if lang == "en"
        else f"Chưa có nguồn cho {codes}. Chưa đủ căn cứ để đối chiếu đầy đủ."
    )


def _evidence_answer(
    query: str,
    chunks: list[RetrievedChunk],
    missing: list[str],
    lang: str,
) -> str:
    requested = _standard_ids(query)
    selected: set[tuple[str, int] | str] = set()
    excerpts = ["Source excerpts for review." if lang == "en" else "Trích đoạn nguồn để đối chiếu."]
    for chunk in chunks:
        family, number = next(iter(_standard_ids(str(chunk.metadata["standard_code"]))))
        standard_id = family, number
        # Reserve one excerpt for each named standard, or one per side for a general query.
        selection = standard_id if standard_id in requested else _side(standard_id)
        if selection in selected:
            continue
        text = str(
            chunk.metadata.get("text") or chunk.metadata.get("text_preview") or chunk.text
        ).strip()
        if not text:
            continue
        selected.add(selection)
        # Citation markers written inside documents are text rather than references in this answer.
        text = re.sub(r"\[(?=C\d)", "［", text)
        code = f"{family} {number:02d}" if family == "VAS" else f"{family} {number}"
        excerpts.append(f"**{code}** [{chunk.citation_key}]\n{text}")
    if missing:
        excerpts.append(_missing_sources(missing, lang))
    return "\n\n".join(excerpts)


class IFRSCompareAgent(AgentBase):
    """Retrieves VAS + IFRS content on a topic and generates structured comparison."""

    async def arun(  # type: ignore[override]
        self,
        *,
        query: str,
        lang: str = "vi",
        tenant_id: str | None = None,
        tenant_collection: str | None = None,
        scope: str = "both",
        model_hint: str = "openai",
        messages: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        chunks, keys, missing = await _retrieve_sides(
            query,
            tenant_collection=tenant_collection,
            tenant_id=tenant_id,
            scope=scope,
            lang=lang,
        )

        if not chunks:
            answer = (
                "No relevant sources were found for this comparison."
                if lang == "en"
                else "Không tìm thấy nguồn phù hợp để thực hiện đối chiếu này."
            )
            if settings.compare_mode == "evidence" and missing:
                answer = _missing_sources(missing, lang)
            yield f"data: {json.dumps({'type': 'final', 'content': answer})}\n\n"
            return

        context_block, citation_map = wrap_chunks_for_prompt(chunks)
        if settings.compare_mode == "evidence":
            cleaned = _evidence_answer(query, chunks, missing, lang)
        else:
            from app.prompts.composer import render

            system = render(
                "system/ifrs_compare_grounded.j2",
                lang=lang,
                context=context_block,
                tenant_name=kwargs.get("tenant_name"),
                side_keys={side: sorted(values) for side, values in keys.items()},
                missing=missing,
            )

            collected: list[str] = []
            async for token in _call_llm(query, system, model_hint, messages):
                collected.append(token)

            cleaned = _grounded_answer("".join(collected), keys, missing, lang, citation_map)
        # Buffer model text so the client only receives claims that pass citation checks.
        yield f"data: {json.dumps({'type': 'token', 'delta': cleaned})}\n\n"

        for cite in build_citation_list(cleaned, citation_map):
            payload = {
                "type": "citation",
                "key": cite.key,
                "doc_id": cite.doc_id,
                "chunk_id": cite.chunk_id,
                "snippet": cite.snippet,
                "standard_code": cite.standard_code,
            }
            yield f"data: {json.dumps(payload)}\n\n"

        yield f"data: {json.dumps({'type': 'final', 'content': cleaned})}\n\n"


async def _call_llm(
    user: str, system: str, model_hint: str, messages: list[dict[str, str]] | None = None
) -> AsyncIterator[str]:
    from app.llm.router import stream_chat

    async for tok in stream_chat(
        system=system, user=user, messages=messages, model_hint=model_hint
    ):
        yield tok
