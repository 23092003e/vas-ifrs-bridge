"""Compare-agent replay with E5/BM25 cards and a fixed local Qwen checkpoint."""

import argparse
import asyncio
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

import torch
from app.agents import ifrs_compare_agent as compare
from app.rag import retriever
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "matrix-v1"))
from run_matrix import BASE, BASE_REVISION, Retrieval, read


async def run(output, device, questions_file=None):
    model = (
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
    tokenizer = AutoTokenizer.from_pretrained(
        BASE, revision=BASE_REVISION, local_files_only=True
    )
    lookup = Retrieval(read("corpus"))
    captured = {}

    async def embed(query):
        return lookup.embed("query: ", [query])[0]

    async def search(client, collection, vec, query, flt):
        side = {"kb_shared_vas": "vas", "kb_shared_ifrs": "ifrs"}.get(collection)
        if side is None:
            return []
        standards = (
            next(
                (c.match.any for c in (flt.must or []) if c.key == "standard_code"), []
            )
            if flt
            else []
        )
        allowed = {
            i
            for i, card in enumerate(lookup.corpus)
            if ("vas" if card["standard"].startswith("VAS") else "ifrs") == side
            and (not standards or card["standard"] in standards)
        }
        dense = (lookup.vectors @ vec).argsort(descending=True).tolist()
        terms = " OR ".join(
            f'"{t}"'
            for t in sorted(set(re.findall(r"[^\W_]+", query.casefold())))
            if len(t) > 1
        )
        sparse = (
            [
                i - 1
                for (i,) in lookup.db.execute(
                    "SELECT rowid FROM cards WHERE cards MATCH ? ORDER BY bm25(cards), rowid",
                    (terms,),
                )
            ]
            if terms
            else []
        )
        scores = Counter()
        for ranking in (dense, sparse):
            for rank, index in enumerate((i for i in ranking if i in allowed), 1):
                scores[index] += 1 / (60 + rank)
        hits = []
        for i in sorted(scores, key=lambda i: (-scores[i], i)):
            card = lookup.corpus[i]
            hits.append(
                SimpleNamespace(
                    id=card["id"],
                    score=scores[i],
                    payload={
                        "doc_id": card["id"],
                        "standard_code": card["standard"],
                        "text": card["text"],
                    },
                )
            )
        return hits

    class LocalClient:
        async def close(self):
            pass

    async def rerank(query, chunks, top_k):
        return sorted(chunks, key=lambda chunk: chunk["score"], reverse=True)[:top_k]

    async def generate(user, system, model_hint, messages=None):
        captured["docs"] = dict(re.findall(r'<<(C\d+) src="([^#]+)#', system))
        batch = tokenizer.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        ).to(device)
        with torch.inference_mode():
            result = model.generate(**batch, max_new_tokens=170, do_sample=False)
        raw = tokenizer.decode(
            result[0, batch.input_ids.shape[1] :], skip_special_tokens=True
        )
        captured["raw"] = raw
        yield raw

    retriever._qdrant_client = LocalClient
    retriever._hybrid_search = search
    retriever.embed_query = embed
    retriever.rerank = rerank
    compare._call_llm = generate
    questions = [
        json.loads(line)
        for line in (questions_file or HERE / "questions.jsonl")
        .read_text()
        .splitlines()
    ]
    pilots = (
        []
        if questions_file
        else [
            dict(row, gold=row["evidence"])
            for row in read("test")
            if row["group"] == "compare"
        ]
    )
    rows = []
    for group, cases in (("freeform", questions), ("pilot", pilots)):
        for row in cases:
            captured.clear()
            start = perf_counter()
            events = [
                json.loads(event.removeprefix("data: "))
                async for event in compare.IFRSCompareAgent().arun(
                    query=row["question"], scope="shared", lang=row["lang"]
                )
            ]
            data = {
                "id": row["id"],
                "group": group,
                "seconds": perf_counter() - start,
                "expected": row.get("expected"),
                "gold": row["gold"],
                "docs": captured.get("docs", {}),
                "raw": captured.get("raw"),
                "evidence_present": set(row["gold"])
                <= set(captured.get("docs", {}).values()),
                "final": next(
                    event["content"] for event in events if event["type"] == "final"
                ),
                "citations": [event for event in events if event["type"] == "citation"],
            }
            rows.append(data)
            output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
            print(
                data["id"],
                f"{data['seconds']:.2f}s",
                data["evidence_present"],
                flush=True,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--device", default="mps")
    parser.add_argument("--questions", type=Path)
    parser.add_argument("--agent-file", type=Path)
    args = parser.parse_args()
    if args.agent_file:
        spec = importlib.util.spec_from_file_location(
            "archived_compare_agent", args.agent_file
        )
        if spec is None or spec.loader is None:
            raise ValueError(f"Invalid agent path {args.agent_file}")
        compare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compare)
    asyncio.run(run(args.output, args.device, args.questions))
