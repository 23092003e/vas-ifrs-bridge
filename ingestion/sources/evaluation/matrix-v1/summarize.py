"""Recompute the pilot metrics from completed run artifacts."""
import argparse
import json
import re
from pathlib import Path
from statistics import median, quantiles


def answer_only(row):
    match = re.match(
        r"^\s*(?:(?:answer|đáp án)\s*:\s*)?([A-D])(?=$|[\s.\]:)|])",
        row["answer"],
        re.IGNORECASE,
    )
    return match is not None and match[1].upper() == row["expected"]



def metrics(rows, *, rag=False):
    def count(key):
        return sum(bool(row[key]) for row in rows)

    timings = [row.get("total_seconds", row["generation_seconds"]) for row in rows]
    summary = {
        "questions": len(rows),
        "answer_correct": sum(answer_only(row) for row in rows),
        "strict_correct": count("correct"),
        "valid_format": count("format_valid"),
        "ttft_p50_s": median(row["ttft_seconds"] for row in rows),
        "total_p50_s": median(timings),
        "total_p95_s": quantiles(timings, n=20, method="inclusive")[-1],
        "input_tokens_p50": median(row["input_tokens"] for row in rows),
        "output_tokens_p50": median(row["output_tokens"] for row in rows),
    }
    if rag:
        summary.update(
            all_evidence_retrieved=count("all_evidence_retrieved"),
            recall_at_4=sum(
                len(set(row["retrieved"]) & set(row["gold_citations"])) / len(row["gold_citations"])
                for row in rows
            ) / len(rows),
            grounded_correct=count("grounded_correct"),
            citations_emitted=sum(len(row["citations"]) for row in rows),
            citations_supported=sum(len(row["valid_citations"]) for row in rows),
        )
    if "abstain" in {row["group"] for row in rows}:
        summary["by_group"] = {
            group: sum(answer_only(row) for row in rows if row["group"] == group)
            for group in sorted({row["group"] for row in rows})
        }
        summary["by_language"] = {
            lang: sum(answer_only(row) for row in rows if row["lang"] == lang)
            for lang in sorted({row["lang"] for row in rows})
        }
    return summary


def summarize(work):
    base, tuned = [json.loads((work / f"{name}.json").read_text()) for name in ("base", "tuned")]
    for key in ("base", "revision", "device", "dtype", "torch"):
        assert base[key] == tuned[key], f"Checkpoint runs disagree on {key}"
    train = json.loads((work / "train.json").read_text())
    assert train["adapter_sha256"] == tuned["adapter_sha256"]
    cells = {
        f"{stage}_{mode}": run["results"][mode]
        for stage, run in (("base", base), ("tuned", tuned))
        for mode in ("none", "hybrid")
    }
    align = lambda rows: {row["id"]: row for row in rows}
    paired = {name: align(rows) for name, rows in cells.items()}
    ids = set(paired["base_none"])
    for rows in paired.values():
        assert set(rows) == ids and len(rows) == 20
    for row_id in ids:
        assert len({rows[row_id]["expected"] for rows in paired.values()}) == 1
        assert paired["base_hybrid"][row_id]["retrieved"] == paired["tuned_hybrid"][row_id]["retrieved"]
    summary = {name: metrics(rows, rag=name.endswith("_hybrid")) for name, rows in cells.items()}
    summary["dev"] = {
        stage: metrics(run["results"]["dev"]) for stage, run in (("base", base), ("tuned", tuned))
    }
    checks = {
        "rag_on_base": ("base_none", "base_hybrid"),
        "rag_on_tuned": ("tuned_none", "tuned_hybrid"),
        "lora_without_rag": ("base_none", "tuned_none"),
        "lora_with_rag": ("base_hybrid", "tuned_hybrid"),
    }
    summary["paired_changes"] = {}
    for name, (before, after) in checks.items():
        diffs = {row_id: int(answer_only(paired[after][row_id])) - int(answer_only(paired[before][row_id]))
                 for row_id in sorted(ids)}
        summary["paired_changes"][name] = {
            "improved": [k for k, v in diffs.items() if v == 1],
            "regressed": [k for k, v in diffs.items() if v == -1],
            "percentage_point_delta": 100 * sum(diffs.values()) / len(ids),
        }
    return summary


if __name__ == "__main__":
    assert answer_only({"answer": "C", "expected": "C"})
    assert answer_only({"answer": "D. explanation", "expected": "D"})
    assert not answer_only({"answer": "Contract asset", "expected": "C"})
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    print(json.dumps(summarize(parser.parse_args().work), indent=2))
