"""Measure actual FastAPI SSE using isolated local services and an eval-only context selector."""

import argparse
import asyncio
import json
import logging
import re
from contextvars import ContextVar
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import httpx
import uvicorn
from app.agents import retrieval_agent
from app.main import app
from app.rag import graph_service, reranker
from app.rag.citation import extract_used_keys
from app.settings import settings
from run_vas_benchmark import (
    GENERATOR,
    GENERATOR_REV,
    ROOT,
    normalized,
    select_windows,
    sha,
)
from transformers import AutoTokenizer

API = "http://127.0.0.1:18081"
TRACE = ContextVar("vas_eval_trace", default=None)
TRACES = {}
_wrap = retrieval_agent.wrap_chunks_for_prompt
_rerank = reranker._call_reranker
_related = graph_service.get_related_sections
_stream = retrieval_agent._stream_llm
STEPWISE = """Follow this step-by-step reasoning process before providing your final answer:
1. Analyze the query carefully.
2. Identify the relevant accounting standards and principles from the context.
3. Differentiate clearly between "Initial Recognition" (Ghi nhận ban đầu) and "Subsequent Measurement" (Đo lường sau ghi nhận) if applicable.
4. Formulate your answer based strictly on the extracted information."""
CONCLUSION_FIRST = """Start the answer with the direct conclusion in one short sentence. Then state the relevant conditions or exceptions and cite the supporting context.
Distinguish initial recognition from subsequent measurement when applicable. Base the answer strictly on the provided context."""


def bounded_rrf_chunks(chunks, question, tokenizer):
    budget = 3000

    def encode(text):
        return tokenizer.encode(text, add_special_tokens=False)

    packed = []
    for index, chunk in enumerate(chunks):
        cap = 850 if index < 2 else min(350, budget // (len(chunks) - index))
        tokens = encode(chunk.text)
        if len(tokens) <= cap:
            text = chunk.text
        else:
            windows = select_windows([chunk.text], question, tokenizer, cap, 110)
            text = (
                "\n\n".join(w[2] for w in sorted(windows))
                if windows
                else tokenizer.decode(tokens[:cap])
            )
        packed.append(replace(chunk, text=text))
        budget -= len(encode(text))
    assert sum(len(encode(chunk.text)) for chunk in packed) <= 3000
    return packed


class RecordRerankFallback(logging.Handler):
    def emit(self, record):
        if (trace := TRACE.get()) is not None:
            message = record.getMessage()
            if message.startswith("reranker timeout"):
                trace["tei_failure"] = "timeout"
            elif message.startswith("reranker unavailable"):
                trace["tei_failure"] = "unavailable"


def install_hooks(rerank_limit, max_tokens, rrf_only=False, bounded_rrf=False):
    if rerank_limit:
        reranker.TIMEOUT_S = 60.0
    tokenizer = AutoTokenizer.from_pretrained(
        GENERATOR, revision=GENERATOR_REV, local_files_only=True
    )
    pair_candidates = {}
    reranker.logger.addHandler(RecordRerankFallback())

    @app.middleware("http")
    async def capture(request, call_next):
        token = TRACE.set(TRACES.get(request.headers.get("x-eval-key")))
        try:
            return await call_next(request)
        finally:
            TRACE.reset(token)

    def wrap(chunks):
        trace = TRACE.get()
        if trace is None:
            return _wrap(chunks)
        if bounded_rrf:
            frozen = pair_candidates.setdefault(trace["question"], chunks)
            trace["live_rank_matches_pair"] = [c.id for c in chunks] == [c.id for c in frozen]
            chunks = frozen
        including = chunks
        budget = None
        if trace["mode"] in {"bounded", "stepwise", "conclusion_first", "rrf_bounded"} and chunks:
            budget = 3000
            including = bounded_rrf_chunks(chunks, trace["question"], tokenizer)
        elif trace["mode"] == "adaptive" and chunks:
            multiple = bool(
                re.search(
                    r"ngoại lệ|thay thế|đồng thời|điều kiện|\bvà\b|[;,]",
                    trace["question"].casefold(),
                )
            )
            budget, width = (1024, 110) if multiple else (512, 70)
            windows = select_windows(
                [c.text for c in chunks], trace["question"], tokenizer, budget, width
            )
            grouped = {}
            for index, start, text in windows:
                grouped.setdefault(index, []).append((start, text))
            if grouped:
                including = [
                    replace(chunks[i], text="\n\n".join(t for _, t in sorted(parts)))
                    for i, parts in grouped.items()
                ]
        block, citations = _wrap(including)
        trace.update(
            retrieved=[
                {
                    "id": c.id,
                    "source": c.metadata.get("source_uri"),
                    "key": c.citation_key,
                }
                for c in chunks
            ],
            context=block,
            prompt_chunks={
                c.citation_key: {"source": c.metadata.get("source_uri"), "text": c.text}
                for c in including
            },
            context_tokens=len(tokenizer.encode(block, add_special_tokens=False)),
            body_budget=budget,
            uncompressed_fallback=budget is not None and including is chunks,
        )
        return block, citations

    async def rerank(query, texts):
        start = perf_counter()
        trace = TRACE.get()
        bypass = rrf_only or (trace is not None and trace["mode"] == "rrf_bounded")
        candidates = [] if bypass else (texts[:rerank_limit] if rerank_limit else texts)
        if rerank_limit:
            # shortcut: bound cross-encoder input on emulated CPU; replay defaults on native TEI.
            candidates = [" ".join(text.split()[:96]) for text in candidates]
        scores = await _rerank(query, candidates) if candidates else []
        if trace is not None:
            status = trace.get("tei_failure", "fallback")
            if bypass:
                status = "bypassed"
            elif scores and len(scores) == len(candidates):
                status = "scored"
            trace["rerank"] = {
                "candidates": len(texts),
                "sent_to_tei": len(candidates),
                "scores": len(scores),
                "seconds": perf_counter() - start,
                "status": status,
            }
        return scores + [0.0] * (len(texts) - len(candidates)) if scores else []

    def related(*args, **kwargs):
        if (trace := TRACE.get()) is not None:
            trace["graph_calls"] += 1
        return _related(*args, **kwargs)

    async def stream(user_msg, system, model_hint, messages=None):
        if (trace := TRACE.get()) is not None:
            if trace["mode"] in {"stepwise", "conclusion_first"}:
                assert (STEPWISE in system) != (CONCLUSION_FIRST in system)
                system = (
                    system.replace(STEPWISE, CONCLUSION_FIRST, 1)
                    if trace["mode"] == "conclusion_first"
                    else system.replace(CONCLUSION_FIRST, STEPWISE, 1)
                )
            trace.setdefault("system_prompt_tokens", []).append(
                len(tokenizer.encode(system, add_special_tokens=False))
            )
        if max_tokens:
            from app.llm.router import stream_chat

            tokens = stream_chat(
                system=system,
                user=user_msg,
                messages=messages,
                model_hint=model_hint,
                max_tokens=max_tokens,
            )
        else:
            tokens = _stream(user_msg, system, model_hint, messages)
        async for token in tokens:
            yield token

    retrieval_agent.wrap_chunks_for_prompt = wrap
    reranker._call_reranker = rerank
    graph_service.get_related_sections = related
    retrieval_agent._stream_llm = stream


async def evaluate(client, row, mode):
    key = uuid4().hex
    trace = {"mode": mode, "question": row["question"], "graph_calls": 0}
    TRACES[key] = trace
    first_token, final, citations, errors = None, None, [], []
    start = perf_counter()
    body = {
        "content": row["question"],
        "scope": "shared",
        "lang": row.get("lang", "vi"),
        "intent_hint": "qa",
        "reasoning": "fast",
    }
    async with client.stream(
        "POST", "/v1/chat/stream", json=body, headers={"x-eval-key": key}
    ) as response:
        response.raise_for_status()
        assert "text/event-stream" in response.headers.get("content-type", "")
        async for line in response.aiter_lines():
            if not line.startswith("data: "):
                continue
            event = json.loads(line[6:])
            if event["type"] == "token" and first_token is None and event.get("delta"):
                first_token = perf_counter() - start
            elif event["type"] == "final":
                final = event
            elif event["type"] == "citation":
                citations.append(event)
            elif event["type"] == "error":
                errors.append(event)
    elapsed = perf_counter() - start
    TRACES.pop(key)
    markers = [normalized(m) for m in row["markers"]]
    context = normalized(trace.get("context", ""))
    cited_text = (
        normalized(
            " ".join(
                trace["prompt_chunks"].get(c["key"], {}).get("text", "")
                for c in citations
            )
        )
        if citations
        else ""
    )
    content = final.get("content", "") if final else ""
    persisted = False
    if final and content:
        saved = (
            (await client.get(f"/v1/chat/conversations/{final['conversation_id']}"))
            .raise_for_status()
            .json()
        )
        persisted = any(
            m["role"] == "assistant" and m["content"] == content
            for m in saved["messages"]
        )
    return {
        "id": row["id"],
        "reference": row["ground_truth"],
        "final": content,
        "persisted": persisted,
        "ttft_seconds": first_token,
        "seconds": elapsed,
        "errors": errors,
        "citations": citations,
        "unresolved_keys": sorted(
            extract_used_keys(content) - {c["key"] for c in citations}
        ),
        "evidence_in_context": sum(m in context for m in markers),
        "evidence_in_cited_chunks": sum(m in cited_text for m in markers),
        "marker_total": len(markers),
        "trace": trace,
    }


async def run(args):
    expected = (
        "http://127.0.0.1:16333",
        "http://127.0.0.1:11436",
        "redis://127.0.0.1:16379/0",
        "postgresql+asyncpg://vas_eval:vas_eval@127.0.0.1:15432/vas_eval",
        "http://127.0.0.1:18080",
    )
    actual = (
        settings.qdrant_url,
        settings.ollama_base_url,
        settings.redis_url,
        settings.database_url,
        settings.tei_url,
    )
    if actual != expected or settings.app_env != "test" or not settings.dev_auth_bypass:
        raise ValueError("Expected isolated benchmark services and test auth")
    if settings.qdrant_api_key:
        raise ValueError("Do not pass a Qdrant API key to the local benchmark")
    file = ROOT / "evaluation" / (
        "vas-confirmation-v1.jsonl" if args.confirmation
        else "vas-bilingual-v1.jsonl" if args.bilingual
        else "vas-api-new-v1.jsonl" if args.new else "pilot-v1.jsonl"
    )
    rows = [json.loads(line) for line in file.read_text().splitlines()]
    if args.new or args.confirmation or args.bilingual:
        lock = json.loads(file.with_suffix(".lock.json").read_text())
        assert sha(file) == lock["dataset_sha256"]
        assert all(
            sha(ROOT / source) == digest
            for source, digest in lock["source_sha256"].items()
        )
        if args.confirmation:
            assert len(rows) == len({row["id"] for row in rows}) == 24
    else:
        labels = json.loads(
            (ROOT / "evaluation/vas-context-dev-labels.json").read_text()
        )
        rows = [{**r, "markers": labels[r["id"]]} for r in rows if r["id"] in labels]
    if args.smoke:
        rows = rows[:1]
    if args.conclusion_first:
        selected = {
            "vas-inventory-02", "vas-revenue-01", "vas-events-02", "vas-regime-01",
            "abstain-inventory-01",
        }
        rows = [row for row in rows if row["id"] in selected]
        assert {row["id"] for row in rows} == selected
    install_hooks(args.rerank_limit, args.max_tokens, args.rrf_only, args.bounded_rrf)
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=18081, log_level="warning")
    )
    serving = asyncio.create_task(server.serve())
    output = []
    try:
        while not server.started:
            if serving.done():
                await serving
                raise RuntimeError("Benchmark API did not start")
            await asyncio.sleep(0.05)
        async with httpx.AsyncClient(base_url=API, timeout=240) as client:
            (await client.get("/readyz")).raise_for_status()
            for index, row in enumerate(rows):
                modes = ["full", "bounded" if args.bounded_rrf else "adaptive"]
                if args.conclusion_first:
                    modes = ["stepwise", "conclusion_first"]
                if args.confirmation:
                    modes = ["tei_current", "rrf_bounded"]
                if args.smoke or (args.rrf_only and not args.bounded_rrf):
                    modes = ["full"]
                elif index % 2:
                    modes.reverse()
                if args.bilingual:
                    modes = ["rrf_bounded"]
                for mode in modes:
                    result = await evaluate(client, row, mode)
                    output.append(result)
                    print(
                        row["id"],
                        mode,
                        result["persisted"],
                        result["trace"].get("rerank"),
                        flush=True,
                    )
                    checkpoint = args.out.with_suffix(".tmp")
                    checkpoint.write_text(
                        json.dumps(
                            {
                                "dataset_sha256": sha(file),
                                "graph_nodes": graph_service.get_graph().number_of_nodes(),
                                "results": output,
                                "rerank_limit": args.rerank_limit,
                                "max_tokens": args.max_tokens,
                                "rrf_only": args.rrf_only,
                                "bounded_rrf": args.bounded_rrf,
                                "conclusion_first": args.conclusion_first,
                                "confirmation": args.confirmation,
                                "bilingual": args.bilingual,
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                        + "\n"
                    )
                    checkpoint.replace(args.out)
    finally:
        server.should_exit = True
        await serving


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--new", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--rerank-limit", type=int, default=0)
    parser.add_argument("--max-tokens", type=int, default=0)
    parser.add_argument("--rrf-only", action="store_true")
    parser.add_argument("--bounded-rrf", action="store_true")
    parser.add_argument("--conclusion-first", action="store_true")
    parser.add_argument("--confirmation", action="store_true")
    parser.add_argument("--bilingual", action="store_true")
    args = parser.parse_args()
    if args.bounded_rrf and not args.rrf_only:
        parser.error("--bounded-rrf requires --rrf-only")
    if args.conclusion_first and (not args.bounded_rrf or args.new or args.smoke):
        parser.error("--conclusion-first requires the paired bounded RRF dev run")
    if args.confirmation and any((args.new, args.smoke, args.rerank_limit, args.rrf_only,
                                  args.bounded_rrf, args.conclusion_first, args.bilingual)):
        parser.error("--confirmation uses the default TEI configuration and paired 3,000-token RRF")
    if args.bilingual and any((args.new, args.smoke, args.rerank_limit, args.rrf_only,
                               args.bounded_rrf, args.conclusion_first, args.confirmation)):
        parser.error("--bilingual uses the locked QA pairs and bounded RRF")
    asyncio.run(run(args))
