"""Offline entailment and paired output filtering for the Compare experiment."""

import argparse
import json
import re
import sys
from pathlib import Path
from time import perf_counter

import torch
from app.rag.citation import extract_used_keys
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "matrix-v1"))
from run_matrix import BASE, BASE_REVISION, read

CLAIM_PREFIX = re.compile(r"^\*\*(?:VAS|IFRS|Comparison|Đối chiếu)\*\* — ")
STATUSES = ("supported", "contradicted", "insufficient")
SYSTEM = """Check whether the cited evidence supports the entire candidate accounting claim.
Use only the cited evidence and the case facts stated in the question. The question is not evidence for an accounting rule.
A: All material parts are supported. A calculation directly implied by the facts and rule counts as support.
B: At least one material part contradicts the evidence.
C: No direct contradiction, but at least one material part is missing evidence or the candidate only restates the case without answering.
Preserve qualifiers and distinguish related concepts. Do not fill gaps from your own knowledge.
Example: Evidence: A permit expires after 12 months. Claim: The permit expires after 6 months. Answer: B.
Example: Evidence: Routine servicing is expensed. Claim: Routine servicing is expensed and attracts a 5% penalty. Answer: C.
Example: Question: Two equal payments of 5. Evidence: Add both payments. Claim: Total is 10. Answer: A.
Reply with exactly A, B, or C."""


def load_cases(path):
    return {row["id"]: row for row in map(json.loads, path.read_text().splitlines())}


class Verifier:
    def __init__(self, device):
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(
            BASE, revision=BASE_REVISION, local_files_only=True
        )
        self.model = (
            AutoModelForCausalLM.from_pretrained(
                BASE,
                revision=BASE_REVISION,
                local_files_only=True,
                dtype=torch.float32,
                attn_implementation="eager",
            )
            .to(device)
            .eval()
        )
        letters = [
            self.tokenizer.encode(label, add_special_tokens=False) for label in "ABC"
        ]
        if not all(len(ids) == 1 for ids in letters):
            raise ValueError("Verdict labels must tokenize to one token each")
        self.label_ids = [ids[0] for ids in letters]

    @torch.inference_mode()
    def check(self, question, claim, evidence):
        if not evidence:
            return "insufficient", None
        payload = json.dumps(
            {"question": question, "candidate": claim, "cited_evidence": evidence},
            ensure_ascii=False,
        )
        batch = self.tokenizer.apply_chat_template(
            [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": payload},
            ],
            return_dict=True,
            return_tensors="pt",
            add_generation_prompt=True,
        ).to(self.device)
        logits = self.model(**batch, use_cache=False, logits_to_keep=1).logits
        scores = logits[0, -1, self.label_ids].float().cpu()
        if not scores.isfinite().all():
            raise ValueError("Non-finite verifier scores")
        return STATUSES[scores.argmax().item()], scores.tolist()


def check_claim(verifier, row, case, claim, cards):
    keys = extract_used_keys(claim)
    sources = [row["docs"][key] for key in sorted(keys) if key in row["docs"]]
    evidence = [
        {"standard": cards[doc]["standard"], "text": cards[doc]["text"]}
        for doc in sources
    ]
    verdict, scores = verifier.check(case["question"], claim, evidence)
    return {"claim": claim, "sources": sources, "verdict": verdict, "logits": scores}


def replay(verifier, row, case, cards):
    started = perf_counter()
    checks = []
    kept = []
    for block in row["final"].split("\n\n"):
        if CLAIM_PREFIX.match(block):
            verdict = check_claim(verifier, row, case, block, cards)
            checks.append(verdict)
            if verdict["verdict"] != "supported":
                continue
        kept.append(block)
    if not kept:
        kept.append(
            "No cited claim could be verified."
            if case["lang"] == "en"
            else "Chưa xác minh được nhận định nào từ các đoạn được dẫn."
        )
    final = "\n\n".join(kept)
    elapsed = perf_counter() - started
    used = extract_used_keys(final)
    return {
        "id": row["id"],
        "checks": checks,
        "final": final,
        "citations": [cite for cite in row["citations"] if cite["key"] in used],
        "seconds_verifier": elapsed,
        "seconds_paired_sum": row["seconds"] + elapsed,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("controls", "holdout"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--device", default="mps")
    args = parser.parse_args()
    cards = {card["id"]: card for card in read("corpus")}
    verifier = Verifier(args.device)
    verifier.check(
        "When was the form signed?",
        "It was signed on Tuesday.",
        [{"standard": "fixture", "text": "The form was signed on Tuesday."}],
    )
    if args.stage == "controls":
        prior = HERE.parent / "compare-v3"
        cases = load_cases(prior / "holdout.jsonl")
        rows = {
            row["id"]: row for row in json.loads((prior / "results.json").read_text())
        }
        output = []
        for case_id, index, expected in json.loads(
            (HERE / "controls.json").read_text()
        ):
            row = rows[case_id]
            claim = row["final"].split("\n\n")[index - 1]
            if not CLAIM_PREFIX.match(claim):
                raise ValueError(f"Control {case_id}.{index} is not a published claim")
            output.append(
                {
                    "id": case_id,
                    "index": index,
                    "expected": expected,
                    **check_claim(verifier, row, cases[case_id], claim, cards),
                }
            )
    else:
        cases = load_cases(HERE / "holdout.jsonl")
        rows = json.loads((HERE / "baseline.json").read_text())
        if list(cases) != [row["id"] for row in rows]:
            raise ValueError("Baseline is missing locked holdout rows")
        output = [replay(verifier, row, cases[row["id"]], cards) for row in rows]
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
