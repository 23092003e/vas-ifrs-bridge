"""Local 2x2 pilot with a pinned Qwen base, a trained LoRA and dense/BM25 retrieval."""
import argparse
import hashlib
import json
import random
import re
import sqlite3
from collections import Counter
from pathlib import Path
from time import perf_counter

import torch
from safetensors.torch import load_file, save_file
from torch import nn
from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer
from transformers.generation.streamers import BaseStreamer

HERE = Path(__file__).resolve().parent
BASE = "Qwen/Qwen2.5-1.5B-Instruct"
BASE_REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
EMBEDDER = "intfloat/multilingual-e5-small"
EMBEDDER_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
SYSTEM = (
    "You answer a bilingual multiple-choice accounting or evidence task. Choose one option. "
    "When evidence notes are present, list only note IDs that support the choice. "
    "When there is no supporting note, use NONE. Reply in one line exactly: A | S01,S02 "
    "(or B | NONE). Use the actual option and IDs. Do not add prose."
)
OUTPUT = re.compile(r"\s*([ABCD])\s*\|\s*(NONE|S\d{2}(?:\s*,\s*S\d{2})*)\s*")
SEED = 401
TOP_K = 4
MAX_OUTPUT = 32
RANK = 8
ALPHA = 16
LAYERS = 8
EPOCHS = 2
BATCH = 4
LEARNING_RATE = 0.001


def sha(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def read(name):
    return [json.loads(line) for line in (HERE / f"{name}.jsonl").read_text().splitlines()]


def verify():
    locked = json.loads((HERE / "lock.json").read_text())
    for item, expected in locked["sha256"].items():
        if sha(HERE / item) != expected:
            raise ValueError(f"Frozen input changed: {item}")
    splits = [read(name) for name in ("train", "dev", "test")]
    for key in ("family", "id", "question"):
        sets = [{row[key] for row in rows} for rows in splits]
        if any(sets[i] & sets[j] for i in range(3) for j in range(i)):
            raise ValueError(f"Dataset splits overlap on {key}")
    corpus = {row["id"] for row in read("corpus")}
    if any(not set(row["evidence"]) <= corpus for row in splits[2]):
        raise ValueError("A test label points to a missing evidence card")


def messages(row, notes):
    prompt = ("Evidence notes:\n" + "\n".join(f"[{k}] {v}" for k, v in notes)
              if notes else "Evidence notes: none")
    options = "\n".join(f"{letter}. {text}" for letter, text in zip("ABCD", row["options"]))
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"{prompt}\n\n{row['question']}\n{options}"},
    ]


class Retrieval:
    def __init__(self, corpus):
        self.corpus = corpus
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE VIRTUAL TABLE cards USING fts5(doc, tokenize = 'unicode61')")
        self.texts = [f"{d['standard']} — {d['text']}" for d in corpus]
        self.db.executemany("INSERT INTO cards(doc) VALUES (?)", [(t,) for t in self.texts])
        self.tokenizer = AutoTokenizer.from_pretrained(
            EMBEDDER, revision=EMBEDDER_REVISION, local_files_only=True
        )
        self.model = AutoModel.from_pretrained(
            EMBEDDER, revision=EMBEDDER_REVISION, local_files_only=True
        ).eval()
        self.vectors = self.embed("passage: ", self.texts)

    @torch.inference_mode()
    def embed(self, prefix, texts):
        inputs = self.tokenizer(
            [prefix + text for text in texts], padding=True, truncation=True, return_tensors="pt"
        )
        hidden = self.model(**inputs).last_hidden_state
        mask = inputs.attention_mask.unsqueeze(-1)
        return nn.functional.normalize((hidden * mask).sum(1) / mask.sum(1), dim=1)

    def search(self, question):
        dense = (self.vectors @ self.embed("query: ", [question])[0]).argsort(descending=True)
        words = sorted(set(re.findall(r"[^\W_]+", question.casefold())))
        expression = " OR ".join(f'"{w}"' for w in words if len(w) > 1)
        sparse = [i - 1 for (i,) in self.db.execute(
            "SELECT rowid FROM cards WHERE cards MATCH ? ORDER BY bm25(cards), rowid", (expression,)
        )] if expression else []
        scores = Counter()
        for ranking in (dense.tolist(), sparse):
            for rank, index in enumerate(ranking, 1):
                scores[index] += 1 / (60 + rank)
        order = sorted(scores, key=lambda i: (-scores[i], i))[:TOP_K]
        return [(self.corpus[i]["id"], self.texts[i]) for i in order]


class Adapter(nn.Module):
    def __init__(self, linear):
        super().__init__()
        self.linear = linear
        self.a = nn.Linear(linear.in_features, RANK, bias=False)
        self.b = nn.Linear(RANK, linear.out_features, bias=False)
        nn.init.zeros_(self.b.weight)
        self.a.to(linear.weight.device)
        self.b.to(linear.weight.device)

    def forward(self, x):
        return self.linear(x) + (self.b(self.a(x.float())) * (ALPHA / RANK)).to(x.dtype)


def add_adapters(model):
    model.requires_grad_(False)
    parameters = {}
    for index, layer in list(enumerate(model.model.layers))[-LAYERS:]:
        for name in ("q_proj", "v_proj"):
            adapter = Adapter(getattr(layer.self_attn, name))
            setattr(layer.self_attn, name, adapter)
            parameters[f"{index}.{name}.a"] = adapter.a.weight
            parameters[f"{index}.{name}.b"] = adapter.b.weight
    return parameters


class Timer(BaseStreamer):
    def __init__(self, start):
        self.start = start
        self.seen_prompt = False
        self.ttft = None

    def put(self, value):
        if self.seen_prompt and self.ttft is None:
            self.ttft = perf_counter() - self.start
        self.seen_prompt = True

    def end(self):
        pass


@torch.inference_mode()
def generate(model, tokenizer, row, notes, device):
    batch = tokenizer.apply_chat_template(
        messages(row, notes), add_generation_prompt=True, return_dict=True, return_tensors="pt"
    ).to(device)
    length = batch.input_ids.shape[1]
    start = perf_counter()
    timer = Timer(start)
    generated = model.generate(
        **batch, max_new_tokens=MAX_OUTPUT, do_sample=False, streamer=timer,
        return_dict_in_generate=True, output_scores=True,
    )
    output = generated.sequences[0, length:]
    if device == "mps":
        torch.mps.synchronize()
    seconds = perf_counter() - start
    if any(torch.isnan(scores).any().item() or not torch.isfinite(scores).any().item()
           for scores in generated.scores):
        raise RuntimeError(f"Non-finite generation scores for {row['id']}")
    raw = tokenizer.decode(output, skip_special_tokens=True)
    match = OUTPUT.fullmatch(raw)
    choice = match[1] if match else None
    citations = (
        re.findall(r"S\d{2}", match[2]) if match else []
    )
    visible_ids = {k for k, _ in notes}
    gold = set(row["evidence"])
    return {
        "id": row["id"], "group": row["group"], "lang": row["lang"], "answer": raw,
        "expected": row["answer"], "choice": choice, "correct": choice == row["answer"],
        "format_valid": match is not None, "citations": citations,
        "retrieved": [k for k, _ in notes], "gold_citations": sorted(gold),
        "valid_citations": sorted(set(citations) & visible_ids & gold),
        "all_evidence_retrieved": gold <= visible_ids,
        "grounded_correct": bool(gold) and choice == row["answer"] and set(citations) == gold
        and gold <= visible_ids,
        "input_tokens": length, "output_tokens": len(output),
        "ttft_seconds": timer.ttft, "generation_seconds": seconds,
    }


def train(model, tokenizer, parameters, device):
    data = read("train")
    eos = tokenizer.eos_token_id
    pad = tokenizer.pad_token_id
    optimizer = torch.optim.AdamW(parameters.values(), lr=LEARNING_RATE)
    rng = random.Random(SEED)
    encoded = []
    for row in data:
        notes = row["context"]
        prefix = tokenizer.apply_chat_template(
            messages(row, notes), add_generation_prompt=True, return_dict=False
        )
        target = tokenizer.encode(
            row["answer"] + " | " + (",".join(row["evidence"]) or "NONE"), add_special_tokens=False
        ) + [eos]
        encoded.append((prefix + target, [-100] * len(prefix) + target))
    history = []
    model.train()
    for epoch in range(EPOCHS):
        rng.shuffle(encoded)
        for offset in range(0, len(encoded), BATCH):
            batch = encoded[offset:offset + BATCH]
            width = max(len(ids) for ids, labels in batch)
            ids = torch.tensor([i + [pad] * (width-len(i)) for i, _ in batch], device=device)
            labels = torch.tensor(
                [y + [-100] * (width-len(y)) for _, y in batch], device=device
            )
            mask = torch.tensor(
                [[1] * len(i) + [0] * (width-len(i)) for i, _ in batch], device=device
            )
            optimizer.zero_grad(set_to_none=True)
            hidden = model.model(input_ids=ids, attention_mask=mask, use_cache=False).last_hidden_state
            target = labels[:, 1:]
            train_tokens = target != -100
            logits = model.lm_head(hidden[:, :-1][train_tokens])
            loss = nn.functional.cross_entropy(logits.float(), target[train_tokens])
            if not torch.isfinite(loss).item():
                raise RuntimeError(f"Training loss is non-finite at step {len(history) + 1}")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(parameters.values(), 1.0, error_if_nonfinite=True)
            optimizer.step()
            history.append(loss.item())
        print(f"epoch {epoch+1}: mean loss {sum(history[-len(encoded)//BATCH:])/(len(encoded)//BATCH):.4f}", flush=True)
    return history


def evaluate(model, tokenizer, retrieval, device):
    warmup = read("dev")[0]
    generate(model, tokenizer, warmup, warmup["context"], device)
    dev = [generate(model, tokenizer, row, row["context"], device) for row in read("dev")]
    questions = read("test")
    trials = [(question, mode) for question in questions for mode in ("none", "hybrid")]
    random.Random(SEED).shuffle(trials)
    results = {"dev": dev, "none": [], "hybrid": []}
    for question, mode in trials:
        start = perf_counter()
        notes = retrieval.search(question["question"]) if mode == "hybrid" else []
        retrieval_time = perf_counter() - start
        row = generate(model, tokenizer, question, notes, device)
        row["retrieval_seconds"] = retrieval_time
        row["total_seconds"] = perf_counter() - start
        results[mode].append(row)
        print(f"{mode} {row['id']} {row['total_seconds']:.2f}s", flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["base", "train", "tuned"])
    parser.add_argument("--device", default="mps", choices=["mps", "cpu"])
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    verify()
    args.work.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(SEED)
    dtype = torch.float32
    tokenizer = AutoTokenizer.from_pretrained(BASE, revision=BASE_REVISION, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        BASE, revision=BASE_REVISION, local_files_only=True, dtype=dtype, attn_implementation="eager"
    ).to(args.device)
    adapter_path = args.work / "adapter.safetensors"
    result = {"base": BASE, "revision": BASE_REVISION, "device": args.device,
              "dtype": str(dtype), "torch": str(torch.__version__), "stage": args.stage}
    if args.stage == "train":
        if not (args.work / "base.json").exists():
            raise RuntimeError("Finish baseline before training")
        parameters = add_adapters(model)
        start = perf_counter()
        loss = train(model, tokenizer, parameters, args.device)
        save_file({k: p.detach().cpu().contiguous() for k, p in parameters.items()}, adapter_path)
        result.update({
            "loss": loss, "seconds": perf_counter() - start, "adapter_sha256": sha(adapter_path),
            "parameter_count": sum(p.numel() for p in parameters.values()), "seed": SEED,
            "epochs": EPOCHS, "batch": BATCH, "lr": LEARNING_RATE, "rank": RANK, "alpha": ALPHA,
        })
    else:
        if args.stage == "tuned":
            parameters = add_adapters(model)
            weights = load_file(adapter_path)
            if weights.keys() != parameters.keys():
                raise ValueError("Adapter parameters differ from the locked configuration")
            with torch.no_grad():
                for key, dest in parameters.items():
                    dest.copy_(weights[key])
            result["adapter_sha256"] = sha(adapter_path)
        result["results"] = evaluate(model.eval(), tokenizer, Retrieval(read("corpus")), args.device)
    (args.work / f"{args.stage}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
