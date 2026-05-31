"""
Hallucination evaluation — LLM-as-judge via Gemini.

Implements 4 RAGAS-equivalent metrics without the ragas library:
  1. faithfulness       — are claims grounded in retrieved context?
  2. answer_relevancy   — does answer address the question?
  3. context_recall     — does context contain info needed for ground truth?
  4. context_precision  — is context relevant (not noisy)?

Dataset format (JSONL):
  {
    "question": "...",
    "answer": "...",               # LLM generated answer
    "contexts": ["chunk1", ...],   # retrieved chunks
    "ground_truth": "..."          # reference answer (optional)
  }

Run:
  python -m app.eval.hallucination_eval --dataset app/eval/datasets/vas_qa_vi.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Judge prompts
# ---------------------------------------------------------------------------

_FAITHFULNESS_PROMPT = """\
You are an expert evaluator for a RAG system about Vietnamese Accounting Standards (VAS) and IFRS.

Given:
QUESTION: {question}
ANSWER: {answer}
CONTEXT (retrieved chunks):
{context}

Task: Evaluate if every factual claim in the ANSWER is supported by the CONTEXT.
- Score 1.0 = all claims fully supported by context
- Score 0.5 = most claims supported, minor unsupported details
- Score 0.0 = answer contains significant claims not in context (hallucination)

Respond ONLY with a JSON object: {{"score": <float 0-1>, "reason": "<one sentence>"}}
"""

_ANSWER_RELEVANCY_PROMPT = """\
You are an expert evaluator for a Q&A system about VAS and IFRS accounting standards.

QUESTION: {question}
ANSWER: {answer}

Task: Evaluate how completely and directly the ANSWER addresses the QUESTION.
- Score 1.0 = answer directly and completely answers the question
- Score 0.5 = answer partially addresses the question
- Score 0.0 = answer does not address the question at all

Respond ONLY with a JSON object: {{"score": <float 0-1>, "reason": "<one sentence>"}}
"""

_CONTEXT_RECALL_PROMPT = """\
You are an expert evaluator for a RAG retrieval system about VAS and IFRS.

QUESTION: {question}
GROUND TRUTH ANSWER: {ground_truth}
RETRIEVED CONTEXT:
{context}

Task: Evaluate what fraction of information needed to answer the question correctly
is present in the retrieved context.
- Score 1.0 = context contains all necessary information
- Score 0.5 = context has partial information
- Score 0.0 = context is missing key information needed

Respond ONLY with a JSON object: {{"score": <float 0-1>, "reason": "<one sentence>"}}
"""

_CONTEXT_PRECISION_PROMPT = """\
You are an expert evaluator for a RAG retrieval system about VAS and IFRS.

QUESTION: {question}
RETRIEVED CONTEXT (chunks, in retrieval order):
{context_numbered}

Task: Evaluate the ranking quality — are relevant chunks ranked higher than irrelevant ones?
For each chunk, indicate if it is relevant (1) or not (0), then compute:
  precision@k = (number of relevant chunks in top k) / k

Focus on whether the most relevant chunks appear first.
- Score 1.0 = all top chunks are highly relevant
- Score 0.5 = mixed relevance in top chunks
- Score 0.0 = top chunks are mostly irrelevant

Respond ONLY with a JSON object: {{"score": <float 0-1>, "reason": "<one sentence>"}}
"""


# ---------------------------------------------------------------------------
# Gemini judge caller
# ---------------------------------------------------------------------------


async def _judge(prompt: str) -> tuple[float, str]:
    """Call Gemini with a judge prompt, parse JSON score."""
    try:
        from google import genai
        from google.genai import types

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            from app.settings import settings

            api_key = settings.gemini_api_key

        client = genai.Client(api_key=api_key)
        resp = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=256,
            ),
        )
        text = resp.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        return float(data["score"]), str(data.get("reason", ""))
    except Exception as exc:
        logger.warning("judge call failed: %s", exc)
        return 0.0, f"error: {exc}"


# ---------------------------------------------------------------------------
# Per-metric evaluators
# ---------------------------------------------------------------------------


async def score_faithfulness(question: str, answer: str, contexts: list[str]) -> tuple[float, str]:
    context = "\n---\n".join(contexts)
    return await _judge(
        _FAITHFULNESS_PROMPT.format(question=question, answer=answer, context=context)
    )


async def score_answer_relevancy(question: str, answer: str) -> tuple[float, str]:
    return await _judge(_ANSWER_RELEVANCY_PROMPT.format(question=question, answer=answer))


async def score_context_recall(
    question: str, contexts: list[str], ground_truth: str
) -> tuple[float, str]:
    context = "\n---\n".join(contexts)
    return await _judge(
        _CONTEXT_RECALL_PROMPT.format(question=question, context=context, ground_truth=ground_truth)
    )


async def score_context_precision(question: str, contexts: list[str]) -> tuple[float, str]:
    numbered = "\n".join(f"[{i + 1}] {c[:400]}" for i, c in enumerate(contexts))
    return await _judge(
        _CONTEXT_PRECISION_PROMPT.format(question=question, context_numbered=numbered)
    )


# ---------------------------------------------------------------------------
# Full record evaluator
# ---------------------------------------------------------------------------


async def _eval_record(record: dict, semaphore: asyncio.Semaphore) -> dict:
    question = record["question"]
    answer = record.get("answer", "")
    contexts = record.get("contexts", [])
    ground_truth = record.get("ground_truth", "")

    async with semaphore:
        tasks = [
            score_faithfulness(question, answer, contexts),
            score_answer_relevancy(question, answer),
        ]
        if ground_truth:
            tasks.append(score_context_recall(question, contexts, ground_truth))
        if contexts:
            tasks.append(score_context_precision(question, contexts))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    faith_score, faith_reason = (
        results[0] if not isinstance(results[0], Exception) else (0.0, str(results[0]))
    )
    rel_score, rel_reason = (
        results[1] if not isinstance(results[1], Exception) else (0.0, str(results[1]))
    )
    recall_score, recall_reason = (
        results[2] if len(results) > 2 and not isinstance(results[2], Exception) else (None, "")
    )
    prec_score, prec_reason = (
        results[3] if len(results) > 3 and not isinstance(results[3], Exception) else (None, "")
    )

    return {
        "question": question,
        "faithfulness": {"score": faith_score, "reason": faith_reason},
        "answer_relevancy": {"score": rel_score, "reason": rel_reason},
        "context_recall": {"score": recall_score, "reason": recall_reason}
        if recall_score is not None
        else None,
        "context_precision": {"score": prec_score, "reason": prec_reason}
        if prec_score is not None
        else None,
    }


# ---------------------------------------------------------------------------
# Main eval runner
# ---------------------------------------------------------------------------


async def evaluate_hallucination(
    dataset_path: str,
    *,
    concurrency: int = 3,
) -> dict:
    """
    Run full RAGAS-equivalent eval on dataset.

    Thresholds (from VAS_IFRS_ARCHITECTURE.md §15):
      faithfulness      >= 0.85
      answer_relevancy  >= 0.85
      hallucination_rate <= 0.03  (faithfulness < 0.5 = hallucination)
    """
    records: list[dict] = []
    with open(dataset_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    logger.info("evaluating %d records (concurrency=%d)...", len(records), concurrency)
    sem = asyncio.Semaphore(concurrency)
    results = await asyncio.gather(*[_eval_record(r, sem) for r in records])

    n = len(results)
    avg_faith = sum(r["faithfulness"]["score"] for r in results) / n if n else 0.0
    avg_rel = sum(r["answer_relevancy"]["score"] for r in results) / n if n else 0.0
    halluc_count = sum(1 for r in results if r["faithfulness"]["score"] < 0.5)
    halluc_rate = halluc_count / n if n else 0.0

    recall_items = [r["context_recall"]["score"] for r in results if r["context_recall"]]
    avg_recall = sum(recall_items) / len(recall_items) if recall_items else None

    prec_items = [r["context_precision"]["score"] for r in results if r["context_precision"]]
    avg_prec = sum(prec_items) / len(prec_items) if prec_items else None

    passed = avg_faith >= 0.85 and avg_rel >= 0.85 and halluc_rate <= 0.03
    status = "PASS" if passed else "FAIL"

    print(f"\n{'=' * 55}")
    print(f"RAG Evaluation (RAGAS-equivalent) — {status}")
    print(f"  Dataset          : {dataset_path}")
    print(f"  N                : {n}")
    print(f"  Faithfulness     : {avg_faith:.4f}  (threshold >= 0.85)")
    print(f"  Answer Relevancy : {avg_rel:.4f}  (threshold >= 0.85)")
    print(f"  Hallucination    : {halluc_rate:.4f}  (threshold <= 0.03)")
    if avg_recall is not None:
        print(f"  Context Recall   : {avg_recall:.4f}")
    if avg_prec is not None:
        print(f"  Context Precision: {avg_prec:.4f}")
    print(f"{'=' * 55}\n")

    return {
        "dataset": dataset_path,
        "n": n,
        "faithfulness": round(avg_faith, 4),
        "answer_relevancy": round(avg_rel, 4),
        "hallucination_rate": round(halluc_rate, 4),
        "context_recall": round(avg_recall, 4) if avg_recall is not None else None,
        "context_precision": round(avg_prec, 4) if avg_prec is not None else None,
        "passed": passed,
        "results": list(results),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="VAS-IFRS RAG hallucination eval")
    parser.add_argument("--dataset", required=True, help="Path to JSONL dataset")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--out", default=None, help="Write JSON results to file")
    args = parser.parse_args()

    results = asyncio.run(evaluate_hallucination(args.dataset, concurrency=args.concurrency))

    if args.out:
        Path(args.out).write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"Results written to {args.out}")

    raise SystemExit(0 if results["passed"] else 1)


if __name__ == "__main__":
    main()
