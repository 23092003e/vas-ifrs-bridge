"""Run the local VAS benchmark using public model checkpoints and frozen source PDFs."""

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
from pathlib import Path
from statistics import median, quantiles
from time import perf_counter

import httpx
import torch
from app.rag.chunker import chunk_document
from qdrant_client import QdrantClient, models
from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["149-2001-QD-BTC.pdf", "100-2005-QD-BTC.pdf", "99-2025-TT-BTC-part-01.pdf"]
GENERATOR = "Qwen/Qwen2.5-0.5B-Instruct"
GENERATOR_REV = "7ae557604adf67be50417f59c2c2f167def9a775"
EMBEDDER = "intfloat/multilingual-e5-small"
EMBEDDER_REV = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
CONTEXT_BUDGET = 512
OLLAMA_MODEL = "qwen2.5:14b-instruct"
BASE_SYSTEM = (
    "Trả lời câu hỏi kế toán bằng tiếng Việt, tối đa hai câu. Nêu rõ nếu thiếu dữ liệu."
)
EVIDENCE_SYSTEM = (
    "Trả lời câu hỏi kế toán bằng tiếng Việt, tối đa hai câu. "
    "Dựa vào tài liệu, nêu kết luận trước rồi nêu các điều kiện hoặc ngoại lệ liên quan. "
    "Nếu thiếu dữ liệu để tính, chỉ rõ cần thêm gì và không tự đặt số."
)


def normalized(text):
    return " ".join(text.casefold().split())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(model_id=GENERATOR, revision=GENERATOR_REV, max_new_tokens=80):
    tokenizer = AutoTokenizer.from_pretrained(
        model_id, revision=revision, local_files_only=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_id, revision=revision, local_files_only=True
    ).eval()

    @torch.inference_mode()
    def generate(question, context, system=BASE_SYSTEM):
        user = (
            question
            if not context
            else f"Tài liệu tham khảo:\n{context}\n\nCâu hỏi: {question}"
        )
        inputs = tokenizer.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        length = inputs["input_ids"].shape[1]
        start = perf_counter()
        output = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False
        )[0, length:]
        elapsed = perf_counter() - start
        return {
            "answer": tokenizer.decode(output, skip_special_tokens=True),
            "input_tokens": length,
            "output_tokens": len(output),
            "seconds": elapsed,
        }

    return tokenizer, generate


def load_ollama_generator(url, max_new_tokens=80):
    base_url = url.rstrip("/")
    with httpx.Client(base_url=base_url, timeout=30) as client:
        version = client.get("/api/version").raise_for_status().json()["version"]
        tags = client.get("/api/tags").raise_for_status().json()["models"]
    tag = next((item for item in tags if item["name"] == OLLAMA_MODEL), None)
    if tag is None:
        raise ValueError(f"Required Ollama model is missing: {OLLAMA_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(
        GENERATOR, revision=GENERATOR_REV, local_files_only=True
    )

    def generate(question, context, system=BASE_SYSTEM):
        user = (
            question
            if not context
            else f"Tài liệu tham khảo:\n{context}\n\nCâu hỏi: {question}"
        )
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": True,
            "options": {
                "temperature": 0,
                "num_ctx": 4096,
                "num_predict": max_new_tokens,
            },
        }
        answer = []
        first_token = None
        final = None
        start = perf_counter()
        with httpx.stream(
            "POST", f"{base_url}/api/chat", json=payload, timeout=180
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                event = json.loads(line)
                if "error" in event:
                    raise RuntimeError(event["error"])
                delta = event.get("message", {}).get("content", "")
                if delta:
                    if first_token is None:
                        first_token = perf_counter() - start
                    answer.append(delta)
                if event.get("done"):
                    final = event
        if final is None:
            raise RuntimeError("Ollama stream ended without final metrics")
        return {
            "answer": "".join(answer),
            "input_tokens": final["prompt_eval_count"],
            "output_tokens": final["eval_count"],
            "seconds": perf_counter() - start,
            "ttft_seconds": first_token,
            "done_reason": final.get("done_reason"),
        }

    return (
        tokenizer,
        generate,
        {
            "model": OLLAMA_MODEL,
            "digest": tag["digest"],
            "version": version,
            "details": tag["details"],
            "num_ctx": 4096,
            "temperature": 0,
        },
    )


def reciprocal_fusion(dense, sparse):
    scores = {}
    for ranking in (dense, sparse):
        for rank, key in enumerate(ranking, 1):
            scores[key] = scores.get(key, 0.0) + 1 / (rank + 60)
    return sorted(scores, key=lambda key: (-scores[key], key))


def search_pattern(question):
    terms = set(re.findall(r"[^\W_]+", question.casefold()))
    return " OR ".join(f'"{t}"' for t in sorted(terms) if len(t) >= 2)


def select_windows(chunks, question, tokenizer, budget=CONTEXT_BUDGET, width=70):
    """Rank overlapping word windows from the already retrieved chunks with BM25."""
    windows = []
    for chunk_id, text in enumerate(chunks):
        words = text.split()
        for start in range(0, len(words), 50):
            windows.append((chunk_id, start, " ".join(words[start : start + width])))
            if start + width >= len(words):
                break
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE VIRTUAL TABLE windows USING fts5(text)")
        db.executemany(
            "INSERT INTO windows(rowid, text) VALUES (?, ?)",
            ((i, w[2]) for i, w in enumerate(windows)),
        )
        ranked = db.execute(
            "SELECT rowid FROM windows WHERE windows MATCH ? ORDER BY rank, rowid",
            (search_pattern(question),),
        ).fetchall()
    db.close()
    selected = []
    for (window_id,) in ranked:
        chunk_id, start, text = windows[window_id]
        if any(c == chunk_id and abs(s - start) < width for c, s, _ in selected):
            continue
        candidate = "\n\n".join([w[2] for w in selected] + [text])
        if len(tokenizer.encode(candidate, add_special_tokens=False)) <= budget:
            selected.append(windows[window_id])
    return selected


def select_passages(chunks, question, tokenizer):
    return "\n\n".join(w[2] for w in select_windows(chunks, question, tokenizer))


@torch.inference_mode()
def run(args):
    torch.set_num_threads(args.threads)
    manifest = {
        r["file"]: r["sha256"]
        for r in json.loads((ROOT / "downloads.json").read_text())
        if "sha256" in r
    }
    data_file = ROOT / (
        "evaluation/pilot-v1.jsonl"
        if args.context_dev
        else "evaluation/vas-holdout-v1.jsonl"
    )
    holdout = [json.loads(line) for line in data_file.read_text().splitlines()]
    source_names = SOURCES
    if args.context_dev:
        labels_file = ROOT / "evaluation/vas-context-dev-labels.json"
        labels = json.loads(labels_file.read_text())
        lock = json.loads((ROOT / "evaluation/pilot-v1.lock.json").read_text())
        assert sha(data_file) == lock["sha256"]
        holdout = [
            r
            for r in holdout
            if all(e["source"].startswith("vas/") for e in r["evidence"])
        ]
        assert {r["id"] for r in holdout} == labels.keys()
        source_names = [*SOURCES, "12-2005-QD-BTC.doc"]
        for row in holdout:
            row["answer"] = row["ground_truth"]
            row["markers"] = labels[row["id"]]
            row["source"] = Path(row["evidence"][0]["source"]).name
    else:
        for row in holdout:
            row["markers"] = [row["needle"]]
            row["source"] = SOURCES[1]
    chunks, names = [], []
    for name in source_names:
        path = ROOT / "vas" / name
        assert sha(path) == manifest[f"vas/{name}"]
        command = (
            ["pdftotext", "-layout", path, "-"]
            if path.suffix == ".pdf"
            else ["textutil", "-convert", "txt", "-stdout", path]
        )
        text = subprocess.check_output(command, text=True)
        text = " ".join(text.split())
        for chunk in chunk_document(text):
            chunks.append(chunk.text)
            names.append(name)
    gold = {
        r["id"]: {
            i
            for i, chunk in enumerate(chunks)
            if names[i] == r["source"]
            and any(normalized(m) in normalized(chunk) for m in r["markers"])
        }
        for r in holdout
    }
    assert all(gold.values()), gold

    embed_tokenizer = AutoTokenizer.from_pretrained(
        EMBEDDER, revision=EMBEDDER_REV, local_files_only=True
    )
    embedder = AutoModel.from_pretrained(
        EMBEDDER, revision=EMBEDDER_REV, local_files_only=True
    ).eval()

    def embed(texts):
        batch = embed_tokenizer(
            texts, padding=True, max_length=512, truncation=True, return_tensors="pt"
        )
        hidden = embedder(**batch).last_hidden_state
        mask = batch["attention_mask"].unsqueeze(-1)
        return torch.nn.functional.normalize(
            (hidden * mask).sum(1) / mask.sum(1), dim=1
        ).tolist()

    index_start = perf_counter()
    db = sqlite3.connect(":memory:")
    db.execute("CREATE VIRTUAL TABLE chunks USING fts5(text)")
    db.executemany("INSERT INTO chunks(rowid, text) VALUES (?, ?)", enumerate(chunks))
    qdrant = QdrantClient(":memory:")
    qdrant.create_collection(
        "vas_eval",
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )
    for start in range(0, len(chunks), 8):
        vectors = embed([f"passage: {c}" for c in chunks[start : start + 8]])
        qdrant.upsert(
            "vas_eval",
            [models.PointStruct(id=start + i, vector=v) for i, v in enumerate(vectors)],
        )
    index_seconds = perf_counter() - index_start
    print(f"Indexed {len(chunks)} chunks in {index_seconds:.1f}s", flush=True)

    ollama = None
    if args.ollama_url:
        tokenizer, generate, ollama = load_ollama_generator(args.ollama_url)
    else:
        tokenizer, generate = load_generator()

    system = EVIDENCE_SYSTEM if args.evidence_prompt else BASE_SYSTEM
    generate("Hai cộng hai bằng bao nhiêu?", "", system)
    results = []
    for i, row in enumerate(holdout):
        start = perf_counter()
        dense = [
            p.id
            for p in qdrant.query_points(
                "vas_eval", embed([f"query: {row['question']}"])[0], limit=40
            ).points
        ]
        dense_ms = (perf_counter() - start) * 1000
        start = perf_counter()
        pattern = search_pattern(row["question"])
        sparse = [
            r[0]
            for r in db.execute(
                "SELECT rowid FROM chunks WHERE chunks MATCH ? ORDER BY rank, rowid LIMIT 40",
                (pattern,),
            )
        ]
        hybrid = reciprocal_fusion(dense, sparse)
        hybrid_ms = dense_ms + (perf_counter() - start) * 1000
        evidence = gold[row["id"]]
        ranks = {}
        for mode, ranked in (("dense", dense), ("sparse", sparse), ("hybrid", hybrid)):
            ranks[mode] = next(
                (j for j, key in enumerate(ranked[:5], 1) if key in evidence), None
            )
        preview = [chunks[key][:200] for key in hybrid[:5]]
        full = [chunks[key] for key in hybrid[:5]]
        contexts = {
            "base": "",
            "preview": "\n\n".join(preview),
            "full": "\n\n".join(full),
        }
        selection_seconds = 0.0
        if args.context_dev:
            contexts.pop("base")
        if args.context_dev or set(args.variants or ()) & {
            "prefix_512",
            "passages_512",
        }:
            prefix = tokenizer.encode(contexts["full"], add_special_tokens=False)[
                :CONTEXT_BUDGET
            ]
            contexts["prefix_512"] = tokenizer.decode(prefix)
            selection_start = perf_counter()
            contexts["passages_512"] = select_passages(full, row["question"], tokenizer)
            selection_seconds = perf_counter() - selection_start
            assert all(
                len(tokenizer.encode(contexts[m], add_special_tokens=False))
                <= CONTEXT_BUDGET
                for m in ("prefix_512", "passages_512")
            )
        if args.variants:
            contexts = {mode: contexts[mode] for mode in args.variants}
        variants = list(contexts)
        offset = i % len(variants)
        generations = {
            mode: generate(row["question"], contexts[mode], system)
            for mode in variants[offset:] + variants[:offset]
        }
        marker_counts = {
            mode: sum(
                normalized(marker) in normalized(context) for marker in row["markers"]
            )
            for mode, context in contexts.items()
        }
        results.append(
            {
                "id": row["id"],
                "question": row["question"],
                "reference": row["answer"],
                "gold": sorted(evidence),
                "first_gold_rank_at_5": ranks,
                "dense_ms": dense_ms,
                "hybrid_ms": hybrid_ms,
                "hybrid_top5": hybrid[:5],
                "selection_seconds": selection_seconds,
                "marker_total": len(row["markers"]),
                "markers_visible": marker_counts,
                "evidence_visible": {
                    m: count == len(row["markers"])
                    for m, count in marker_counts.items()
                },
                "generations": generations,
            }
        )
        print(f"Completed {row['id']}", flush=True)
    qdrant.close()
    n = len(results)
    ranking = {
        mode: {
            "hit_at_5": sum(
                r["first_gold_rank_at_5"][mode] is not None for r in results
            )
            / n,
            "mrr_at_5": sum(
                1 / (r["first_gold_rank_at_5"][mode] or float("inf")) for r in results
            )
            / n,
        }
        for mode in ("dense", "sparse", "hybrid")
    }
    generation = {}
    for mode in contexts:
        stats = [r["generations"][mode] for r in results]
        times = [
            r["seconds"]
            + (item["hybrid_ms"] / 1000 if mode != "base" else 0)
            + (item["selection_seconds"] if mode == "passages_512" else 0)
            for r, item in zip(stats, results, strict=True)
        ]
        generation[mode] = {
            "evidence_visible": sum(r["evidence_visible"][mode] for r in results),
            "markers_visible": sum(r["markers_visible"][mode] for r in results),
            "median_input_tokens": median(r["input_tokens"] for r in stats),
            "p50_total_seconds": median(times),
            "p95_total_seconds": quantiles(times, n=100, method="inclusive")[94],
        }
    return {
        "source_sha256": {f: manifest[f"vas/{f}"] for f in source_names},
        **(
            {
                "dev_sha256": sha(data_file),
                "labels_sha256": sha(labels_file),
                "context_budget": CONTEXT_BUDGET,
            }
            if args.context_dev
            else {"holdout_sha256": sha(data_file)}
        ),
        "generator": ollama["digest"] if ollama else GENERATOR_REV,
        **({"ollama": ollama} if ollama else {}),
        "system_prompt": system,
        "embedder": EMBEDDER_REV,
        "device": "cpu",
        "threads": args.threads,
        "chunk_count": len(chunks),
        "index_seconds": index_seconds,
        "ranking": ranking,
        "generation": generation,
        "results": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--context-dev", action="store_true")
    parser.add_argument("--ollama-url")
    parser.add_argument("--evidence-prompt", action="store_true")
    parser.add_argument(
        "--variants",
        nargs="+",
        choices=["base", "preview", "full", "prefix_512", "passages_512"],
    )
    args = parser.parse_args()
    if args.context_dev and args.variants and "base" in args.variants:
        parser.error("The dev context comparison does not include a model-only arm")
    args.out.write_text(json.dumps(run(args), ensure_ascii=False, indent=2) + "\n")
