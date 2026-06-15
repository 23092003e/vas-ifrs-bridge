"""
Retrieval evaluation — measures Recall@K and MRR against labelled datasets.

Dataset format (JSONL, one record per line):
  {"question": "...", "ground_truth_doc_ids": ["uuid1", "uuid2"]}

Run:
  python -m app.eval.retrieval_eval --dataset app/eval/datasets/vas_qa_vi.jsonl --k 10
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------


def recall_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int) -> float:
    """Fraction of gold docs found in top-k retrieved."""
    if not gold_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    return len(top_k & set(gold_ids)) / len(gold_ids)


def mrr(retrieved_ids: list[str], gold_ids: list[str]) -> float:
    """Mean Reciprocal Rank — rank of first gold doc hit."""
    gold_set = set(gold_ids)
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in gold_set:
            return 1.0 / rank
    return 0.0


def precision_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int) -> float:
    """Fraction of top-k retrieved that are gold docs."""
    if not retrieved_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    gold_set = set(gold_ids)
    return sum(1 for d in top_k if d in gold_set) / k


# ---------------------------------------------------------------------------
# Dataset loader
# ---------------------------------------------------------------------------


def load_dataset(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------


async def _run_single(
    record: dict,
    k: int,
    tenant_id: str | None,
    tenant_collection: str | None,
    lang: str,
) -> dict:
    from app.rag.retriever import retrieve_multi

    question = record["question"]
    gold_ids: list[str] = record.get("ground_truth_doc_ids", [])

    try:
        chunks = await retrieve_multi(
            question,
            tenant_collection=tenant_collection,
            tenant_id=tenant_id,
            lang=lang,
            k=k,
        )
        retrieved_ids = [c.doc_id for c in chunks]
    except Exception as exc:
        logger.warning("retrieval failed for %r: %s", question[:60], exc)
        retrieved_ids = []

    return {
        "question": question,
        "retrieved_ids": retrieved_ids,
        "gold_ids": gold_ids,
        "recall_at_k": recall_at_k(retrieved_ids, gold_ids, k),
        "mrr": mrr(retrieved_ids, gold_ids),
        "precision_at_k": precision_at_k(retrieved_ids, gold_ids, k),
    }


async def evaluate_retrieval(
    dataset_path: str,
    *,
    k: int = 10,
    tenant_id: str | None = None,
    tenant_collection: str | None = None,
    lang: str = "vi",
    concurrency: int = 4,
) -> dict:
    """
    Run retrieval eval on dataset. Returns aggregate metrics + per-item results.

    Thresholds (from VAS_IFRS_ARCHITECTURE.md §15):
      recall@10 >= 0.85 (shared KB)
      recall@10 >= 0.80 (tenant KB)
    """
    records = load_dataset(dataset_path)
    logger.info("loaded %d records from %s", len(records), dataset_path)

    sem = asyncio.Semaphore(concurrency)

    async def _bounded(rec: dict) -> dict:
        async with sem:
            return await _run_single(rec, k, tenant_id, tenant_collection, lang)

    results = await asyncio.gather(*[_bounded(r) for r in records])

    n = len(results)
    avg_recall = sum(r["recall_at_k"] for r in results) / n if n else 0.0
    avg_mrr = sum(r["mrr"] for r in results) / n if n else 0.0
    avg_precision = sum(r["precision_at_k"] for r in results) / n if n else 0.0

    # Pass/fail vs thresholds
    threshold_shared = 0.85
    threshold_tenant = 0.80
    threshold = threshold_tenant if tenant_id else threshold_shared
    passed = avg_recall >= threshold

    summary = {
        "dataset": dataset_path,
        "n_questions": n,
        "k": k,
        "avg_recall_at_k": round(avg_recall, 4),
        "avg_mrr": round(avg_mrr, 4),
        "avg_precision_at_k": round(avg_precision, 4),
        "threshold": threshold,
        "passed": passed,
        "results": results,
    }

    status = "PASS" if passed else "FAIL"
    print(f"\n{'=' * 50}")
    print(f"Retrieval Eval — {status}")
    print(f"  Dataset    : {dataset_path}")
    print(f"  N          : {n}")
    print(f"  Recall@{k}  : {avg_recall:.4f}  (threshold >= {threshold})")
    print(f"  MRR        : {avg_mrr:.4f}")
    print(f"  Precision@{k}: {avg_precision:.4f}")
    print(f"{'=' * 50}\n")

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="VAS-IFRS retrieval eval")
    parser.add_argument("--dataset", required=True, help="Path to JSONL dataset")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--lang", default="vi")
    parser.add_argument("--tenant-id", default=None)
    parser.add_argument("--tenant-collection", default=None)
    parser.add_argument("--out", default=None, help="Write JSON results to file")
    args = parser.parse_args()

    results = asyncio.run(
        evaluate_retrieval(
            args.dataset,
            k=args.k,
            lang=args.lang,
            tenant_id=args.tenant_id,
            tenant_collection=args.tenant_collection,
        )
    )

    if args.out:
        Path(args.out).write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"Results written to {args.out}")

    raise SystemExit(0 if results["passed"] else 1)


if __name__ == "__main__":
    main()
