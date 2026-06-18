# Document Ingestion Guide

## Folder Layout

```
ingestion/
├── raw/                          ← DROP DOCUMENTS HERE
│   ├── shared/
│   │   ├── ifrs/
│   │   │   ├── standards/        IFRS 1–17 (PDF/DOCX)
│   │   │   ├── ias/              IAS 1–41
│   │   │   ├── ifric/            IFRIC interpretations
│   │   │   ├── sic/              SIC interpretations
│   │   │   ├── framework/        Conceptual Framework
│   │   │   └── taxonomy/         IFRS taxonomy XBRL
│   │   └── vas/
│   │       ├── standards/        VAS 01–30 (PDF/DOCX)
│   │       ├── circulars/        Thông tư Bộ Tài chính (TT200, TT133...)
│   │       ├── decisions/        Quyết định ban hành VAS
│   │       └── adoption/         Hướng dẫn áp dụng
│   └── tenant/
│       └── dev-tenant/
│           ├── fs/               Financial statements
│           ├── audit/            Audit reports, notes
│           ├── contracts/        Contracts, agreements
│           └── internal/         Internal policies
│
├── processed/                    ← AUTO-GENERATED (do not edit)
│   ├── markdown/                 Converted markdown
│   ├── cleaned/                  Normalized text
│   ├── chunks/                   Chunked JSON
│   └── embeddings/               Cached embedding vectors
│
├── metadata/
│   ├── standards_map/            VAS↔IFRS mapping tables
│   ├── paragraph_graph/          Cross-reference graph
│   ├── citations/                Citation index
│   └── taxonomy/                 Account taxonomy
│
└── pipelines/
    ├── parsers/
    │   ├── unstructured_runner.py    PDF/DOCX/XLSX → JSON
    │   ├── vas_circulars.py
    │   ├── ifrs_standards.py
    │   └── tenant_docs.py
    ├── chunkers/
    ├── embedders/
    │   └── batch_embed.py            Chunk → Embed → Upsert Qdrant
    └── retrievers/
```

---

## Prerequisites

1. **Qdrant** — vector DB (required)
2. **Ollama** — running locally (required) with `bge-m3` model downloaded (`ollama pull bge-m3`)

---

## Step 1 — Start Qdrant

```powershell
docker-compose -f infra/docker/docker-compose.qdrant.yml up -d
```

Dashboard: http://localhost:6333/dashboard

---

## Step 2 — Put Documents in `ingestion/raw/`

Examples:
- `ingestion/raw/shared/vas/circulars/TT200-2014-BTC.pdf`
- `ingestion/raw/shared/ifrs/standards/IFRS15-Revenue.pdf`
- `ingestion/raw/tenant/dev-tenant/fs/BCTC-2024.xlsx`

Supported: `.pdf` `.docx` `.doc` `.xlsx` `.xls` `.txt` `.md`

---

## Step 3 — Run Ingestion

### PowerShell (easiest, from repo root)

```powershell
.\ingest.ps1                          # all collections
.\ingest.ps1 -Scope vas               # VAS only
.\ingest.ps1 -Scope ifrs              # IFRS only
.\ingest.ps1 -Scope tenant            # dev-tenant only
.\ingest.ps1 -DryRun                  # parse+chunk only, no embed/upsert
.\ingest.ps1 -Recreate                # drop + recreate collections first
.\ingest.ps1 -Scope vas -Recreate     # clean VAS re-ingest
```

### Python directly (from repo root)

When running the ingestion pipeline, the generated chunks for each document are automatically cached under `ingestion/processed/chunks/<collection_name>/<doc_name>_chunks.json`. This provides an audit trail for chunk verification and debugging.

You can also run the ingestion directly using these pre-saved chunks (skipping the heavy PDF parsing/chunking phases):

```powershell
$env:PYTHONPATH = "apps\backend;ingestion"

# Ingest from raw docs (parses PDFs, chunks, caches JSONs, embeds, and upserts)
python ingestion/pipelines/embedders/batch_embed.py `
  --docs ingestion/raw/shared/vas `
  --collection kb_shared_vas --scope shared

# Ingest from pre-parsed JSON chunks (skips parsing/chunking, directly embeds & upserts)
python ingestion/pipelines/embedders/batch_embed.py `
  --parsed ingestion/processed/chunks/kb_shared_vas `
  --collection kb_shared_vas --scope shared
```

#### Detailed command examples:

```powershell
# VAS
python ingestion/pipelines/embedders/batch_embed.py `
  --docs ingestion/raw/shared/vas `
  --collection kb_shared_vas --scope shared

# IFRS
python ingestion/pipelines/embedders/batch_embed.py `
  --docs ingestion/raw/shared/ifrs `
  --collection kb_shared_ifrs --scope shared

# Tenant
python ingestion/pipelines/embedders/batch_embed.py `
  --docs ingestion/raw/tenant/dev-tenant `
  --collection tenant_dev-tenant --scope tenant --tenant-id dev-tenant
```

---

## Embedding Backend

| Backend | When used | Dim |
|---|---|---|
| **bge-m3 (Ollama)** | Ollama at `OLLAMA_BASE_URL` (localhost:11434) | 1024 |

All text embedding tasks now strictly use Ollama with `bge-m3`. Gemini and TEI embedding fallbacks have been removed.

Run Ollama and pull the `bge-m3` model:
```powershell
ollama pull bge-m3
```

---

## Verify

```powershell
# Check collections
Invoke-RestMethod "http://localhost:6333/collections/kb_shared_vas"
Invoke-RestMethod "http://localhost:6333/collections/kb_shared_ifrs"
```

---

## Eval Datasets

After ingestion, create JSONL files in `apps/backend/app/eval/datasets/`:

**retrieval** (`vas_qa_vi.jsonl`):
```jsonl
{"question": "VAS 15 ghi nhận doanh thu khi nào?", "ground_truth_doc_ids": ["<uuid>"]}
```

**hallucination** (`hallucination_test.jsonl`):
```jsonl
{"question": "...", "answer": "<llm answer>", "contexts": ["<chunk>"], "ground_truth": "..."}
```

Run eval:
```powershell
cd apps/backend
python -m app.eval.retrieval_eval --dataset app/eval/datasets/vas_qa_vi.jsonl --k 10
python -m app.eval.hallucination_eval --dataset app/eval/datasets/hallucination_test.jsonl
```
