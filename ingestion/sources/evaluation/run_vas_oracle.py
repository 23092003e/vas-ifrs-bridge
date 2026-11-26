"""Run a gold-context diagnostic on the existing seven VAS dev questions."""

import argparse
import json
import subprocess
from pathlib import Path
from statistics import median

import torch
from run_vas_benchmark import (
    BASE_SYSTEM,
    EVIDENCE_SYSTEM,
    GENERATOR,
    GENERATOR_REV,
    ROOT,
    load_generator,
    load_ollama_generator,
    normalized,
    sha,
)

# Inclusive line ranges in the output from pdftotext -layout or textutil.
SPANS = {
    "vas-inventory-01": [(71, 72)],
    "vas-inventory-02": [(153, 158)],
    "vas-revenue-01": [(1002, 1009)],
    "vas-events-01": [(417, 418)],
    "vas-events-02": [(428, 429), (458, 461)],
    "vas-regime-01": [(1108, 1127)],
    "abstain-inventory-01": [(65, 67), (71, 72), (153, 156)],
}


def prepare():
    directory = ROOT / "evaluation"
    dataset = directory / "pilot-v1.jsonl"
    labels_file = directory / "vas-context-dev-labels.json"
    baseline_file = directory / "vas-context-dev-v1.json"
    lock = json.loads((directory / "pilot-v1.lock.json").read_text())
    baseline = json.loads(baseline_file.read_text())
    assert sha(dataset) == lock["sha256"] == baseline["dev_sha256"]
    assert sha(labels_file) == baseline["labels_sha256"]
    assert baseline["generator"] == GENERATOR_REV
    labels = json.loads(labels_file.read_text())
    locked_sources = {item["file"]: item["sha256"] for item in lock["sources"]}
    rows = [json.loads(line) for line in dataset.read_text().splitlines()]
    rows = [row for row in rows if row["id"] in SPANS]
    assert {row["id"] for row in rows} == SPANS.keys() == labels.keys()
    sources = {}
    cases = []
    for row in rows:
        source = row["evidence"][0]["source"]
        if source not in sources:
            path = ROOT / source
            assert (
                sha(path)
                == locked_sources[source]
                == baseline["source_sha256"][path.name]
            )
            command = (
                ["pdftotext", "-layout", path, "-"]
                if path.suffix == ".pdf"
                else ["textutil", "-convert", "txt", "-stdout", path]
            )
            sources[source] = subprocess.check_output(command, text=True).split("\n")
        ranges = SPANS[row["id"]]
        context = "\n\n".join(
            " ".join(" ".join(sources[source][a - 1 : b]).split()) for a, b in ranges
        )
        markers = labels[row["id"]]
        assert all(normalized(marker) in normalized(context) for marker in markers), (
            row["id"]
        )
        cases.append(
            {
                "id": row["id"],
                "question": row["question"],
                "reference": row["ground_truth"],
                "required_points": row["required_points"],
                "source": source,
                "locator": row["evidence"][0]["locator"],
                "lines": ranges,
                "context": context,
                "markers_visible": len(markers),
            }
        )
    return cases, dataset, labels_file, baseline_file, baseline, locked_sources


def run(args):
    cases, dataset, labels, baseline_path, baseline, locked_sources = prepare()
    print(
        f"Verified {len(cases)} contexts and {sum(r['markers_visible'] for r in cases)} markers",
        flush=True,
    )
    if args.verify_only:
        return
    torch.set_num_threads(baseline["threads"])
    ollama = None
    if args.ollama_url:
        _, generate, ollama = load_ollama_generator(
            args.ollama_url, args.max_new_tokens
        )
    else:
        _, generate = load_generator(args.model, args.revision, args.max_new_tokens)
    generate("Hai cộng hai bằng bao nhiêu?", "")
    prompts = {"oracle_base": BASE_SYSTEM}
    if not args.base_only:
        prompts["oracle_evidence_prompt"] = EVIDENCE_SYSTEM
    for i, case in enumerate(cases):
        modes = list(prompts)
        if i % 2:
            modes.reverse()
        case["generations"] = {
            mode: generate(case["question"], case["context"], prompts[mode])
            for mode in modes
        }
        print(f"Completed {case['id']}", flush=True)
    report = {
        "dev_sha256": sha(dataset),
        "labels_sha256": sha(labels),
        "baseline_sha256": sha(baseline_path),
        "source_sha256": {
            name: locked_sources[name] for name in sorted({r["source"] for r in cases})
        },
        "generator_model": ollama["model"] if ollama else args.model,
        "generator": ollama["digest"] if ollama else args.revision,
        **({"ollama": ollama} if ollama else {}),
        "max_new_tokens": args.max_new_tokens,
        "device": "ollama" if ollama else baseline["device"],
        **({} if ollama else {"threads": baseline["threads"]}),
        "prompts": prompts,
        "generation": {
            mode: {
                "median_input_tokens": median(
                    r["generations"][mode]["input_tokens"] for r in cases
                ),
                "p50_generation_seconds": median(
                    r["generations"][mode]["seconds"] for r in cases
                ),
            }
            for mode in prompts
        },
        "results": cases,
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--model", default=GENERATOR)
    parser.add_argument("--revision", default=GENERATOR_REV)
    parser.add_argument("--base-only", action="store_true")
    parser.add_argument("--max-new-tokens", type=int, default=80)
    parser.add_argument("--ollama-url")
    args = parser.parse_args()
    if args.max_new_tokens < 1:
        parser.error("--max-new-tokens must be positive")
    if args.out is None:
        if (
            args.model != GENERATOR
            or args.revision != GENERATOR_REV
            or args.base_only
            or args.max_new_tokens != 80
            or args.ollama_url
        ):
            parser.error("--out is required for an alternate configuration")
        args.out = ROOT / "evaluation/vas-oracle-dev-v1.json"
    run(args)
