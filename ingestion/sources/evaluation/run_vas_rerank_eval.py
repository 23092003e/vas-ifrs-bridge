"""Replay three context-ranking policies on the same real QA candidates."""

import argparse
import asyncio
import json
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

from app.agents.retrieval_agent import RetrievalAgent
from app.rag import reranker
from app.settings import settings
from run_vas_benchmark import ROOT, normalized, sha

TOP_K = 8


class CandidatesReady(BaseException):
    """Stop the agent at the reranking boundary before generation."""


async def measure(row):
    raw = []

    async def capture(query, chunks, top_k):
        assert query == row["question"] and top_k == TOP_K
        raw.extend(chunks)
        raise CandidatesReady

    started = perf_counter()
    with patch.object(reranker, "rerank", capture):
        try:
            async for _ in RetrievalAgent().arun(query=row["question"], scope="shared"):
                raise AssertionError("Expected to stop before streaming")
        except CandidatesReady:
            pass
    retrieval_seconds = perf_counter() - started
    assert raw, f"No candidates for {row['id']}"
    assert len({c["id"] for c in raw}) == len(raw)

    # shortcut: replay the bounded TEI workload used in SSE; use native TEI for the full 40.
    texts = [" ".join(c["text"].split()[:96]) for c in raw[:TOP_K]]
    started = perf_counter()
    scores = await reranker._call_reranker(row["question"], texts)
    tei_seconds = perf_counter() - started
    assert len(scores) == len(texts), f"Missing TEI scores for {row['id']}"

    async def replay(query, candidate_texts):
        assert query == row["question"] and len(candidate_texts) == len(raw)
        return scores + [0.0] * (len(raw) - len(scores))

    rrf_order = sorted(raw, key=lambda c: c["score"], reverse=True)
    with patch.object(reranker, "_call_reranker", replay):
        strict = await reranker.rerank(row["question"], raw, top_k=TOP_K)
    strict_ids = {c["id"] for c in strict}
    filled = (strict + [c for c in rrf_order if c["id"] not in strict_ids])[:TOP_K]
    markers = [normalized(m) for m in row["markers"]]

    def summarize(chunks):
        normalized_chunks = [normalized(c["text"]) for c in chunks]
        ranks = [
            [i for i, text in enumerate(normalized_chunks, 1) if marker in text]
            for marker in markers
        ]
        return {
            "ids": [c["id"] for c in chunks],
            "chars": sum(len(c["text"]) for c in chunks),
            "marker_ranks": ranks,
            "marker_hits": sum(bool(r) for r in ranks),
        }

    return {
        "id": row["id"],
        "marker_total": len(markers),
        "retrieval_seconds": retrieval_seconds,
        "tei_seconds": tei_seconds,
        "tei_scores": scores,
        "candidate_pool": summarize(raw),
        "rrf_top8": summarize(rrf_order[:TOP_K]),
        "tei_strict": summarize(strict),
        "tei_fill": summarize(filled),
    }


async def run(out):
    expected = ("http://127.0.0.1:16333", "http://127.0.0.1:11436", "http://127.0.0.1:18080")
    if (settings.qdrant_url, settings.ollama_base_url, settings.tei_url) != expected:
        raise ValueError("Expected the dedicated local benchmark services")
    if settings.qdrant_api_key:
        raise ValueError("Do not pass a Qdrant API key to the local benchmark")
    reranker.TIMEOUT_S = 60.0

    eval_dir = ROOT / "evaluation"
    labels_file = eval_dir / "vas-context-dev-labels.json"
    labels = json.loads(labels_file.read_text())
    dev = eval_dir / "pilot-v1.jsonl"
    holdout = eval_dir / "vas-api-new-v1.jsonl"
    lock = json.loads(holdout.with_suffix(".lock.json").read_text())
    assert sha(holdout) == lock["dataset_sha256"]
    assert all(sha(ROOT / p) == digest for p, digest in lock["source_sha256"].items())
    assert sha(dev) == json.loads(dev.with_suffix(".lock.json").read_text())["sha256"]

    results = {"dev": [], "holdout_replay": []}
    manifest = {"sha256": {p.name: sha(p) for p in (dev, holdout, labels_file)}, "results": results}
    for split, path in zip(results, (dev, holdout), strict=True):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if split == "dev":
                if row["id"] not in labels:
                    continue
                row["markers"] = labels[row["id"]]
            result = await measure(row)
            results[split].append(result)
            out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
            print(split, row["id"], round(result["tei_seconds"], 2), flush=True)
    assert len(results["dev"]) == len(labels)
    assert len(results["holdout_replay"]) == 6


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    asyncio.run(run(parser.parse_args().out))
