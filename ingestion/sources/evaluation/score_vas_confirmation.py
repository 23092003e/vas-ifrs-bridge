"""Export masked VAS answers and apply the locked decision thresholds."""

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
MODES = ("tei_current", "rrf_bounded")


def pairs(dataset, results):
    by_id = {row["id"]: {} for row in dataset}
    for result in results:
        variants = by_id[result["id"]]
        mode = result["trace"]["mode"]
        if mode not in MODES or mode in variants:
            raise ValueError(f"Unexpected or duplicate result for {result['id']} / {mode}")
        variants[mode] = result
    for row in dataset:
        variants = by_id[row["id"]]
        if len(variants) == 2:
            order = MODES[::-1] if hashlib.sha256(row["id"].encode()).digest()[0] % 2 else MODES
            yield row, dict(zip(("X", "Y"), (variants[m] for m in order), strict=True))


def blinded(row, responses):
    return {
        **row,
        "responses": {
            alias: {
                "answer": response["final"],
                "citations": [
                    {**citation, **response["trace"].get("prompt_chunks", {}).get(citation["key"], {})}
                    for citation in response["citations"]
                ],
            }
            for alias, response in responses.items()
        },
    }


def summarize(matched, grades, independent):
    if len(matched) != 24 or set(grades) != {row["id"] for row, _ in matched}:
        raise ValueError("Need grades for all 24 completed pairs")
    stats = {mode: Counter() for mode in MODES}
    latencies = {mode: [] for mode in MODES}
    new_serious = []
    per_case = {}
    for row, responses in matched:
        qid = row["id"]
        if set(grades[qid]) != set(responses):
            raise ValueError(f"Grades must specify both masked responses for {qid}")
        decision = {}
        for alias, response in responses.items():
            grade = grades[qid][alias]
            fields = ("correct", "supported", "serious")
            if not all(type(grade.get(field)) is bool for field in fields) or not grade.get("reason"):
                raise ValueError(f"Invalid grade for {qid}/{alias}")
            mode = response["trace"]["mode"]
            ok = bool(response["persisted"] and not response["errors"] and response["final"])
            if (grade["correct"] and (not ok or grade["serious"])) or (
                grade["supported"] and (not grade["correct"] or not response["citations"])
            ):
                raise ValueError(f"Inconsistent grade for {qid}/{alias}")
            stats[mode].update({**{field: grade[field] for field in fields}, "sse_ok": ok})
            stats[mode][response["trace"].get("rerank", {}).get("status", "not_called")] += 1
            latencies[mode].append(response["seconds"])
            decision[mode] = grade
        if decision["rrf_bounded"]["serious"] and not decision["tei_current"]["serious"]:
            new_serious.append(qid)
        per_case[qid] = decision

    for mode, seconds in latencies.items():
        stats[mode]["p50_seconds"] = median(seconds)
        stats[mode]["p95_seconds"] = sorted(seconds)[math.ceil(0.95 * len(seconds)) - 1]
    baseline, candidate = (stats[mode] for mode in MODES)
    gates = {
        "independent_review": independent,
        "tei_scored_majority": baseline["scored"] > 12,
        "all_sse_completed": baseline["sse_ok"] == candidate["sse_ok"] == 24,
        "correct_delta_at_least_three": candidate["correct"] >= baseline["correct"] + 3,
        "supported_not_lower": candidate["supported"] >= baseline["supported"],
        "no_new_serious_errors": not new_serious,
        "p95_within_20_percent": candidate["p95_seconds"] <= baseline["p95_seconds"] * 1.2,
    }
    return {
        "recommend_default_change": all(gates.values()), "gates": gates,
        "new_serious_case_ids": new_serious, "summary": stats, "grades": per_case,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--grades", type=Path, help="Masked grade JSON including reviewer metadata")
    args = parser.parse_args()
    dataset = HERE / "vas-confirmation-v1.jsonl"
    saved = json.loads(args.results.read_text())
    if not saved.get("confirmation") or saved["dataset_sha256"] != hashlib.sha256(dataset.read_bytes()).hexdigest():
        raise ValueError("Expected results for the locked confirmation set")
    rows = [json.loads(line) for line in dataset.read_text().splitlines()]
    matched = list(pairs(rows, saved["results"]))
    if args.grades:
        review = json.loads(args.grades.read_text())
        independent = review.get("labels_verified_before_run") is True and review.get("independent_reviewer") is True
        report = summarize(matched, review["grades"], independent)
        report["reviewer"] = review["reviewer"]
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    else:
        args.out.write_text("".join(json.dumps(blinded(row, pair), ensure_ascii=False) + "\n" for row, pair in matched))


if __name__ == "__main__":
    main()
