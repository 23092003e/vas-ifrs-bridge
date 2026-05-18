# Document Ingestion Guide

## Prerequisites

1. **Qdrant** — vector database (required)
2. **Documents** — PDF/DOCX/XLSX/TXT in the folders below
3. **TEI** (optional) — bge-m3 embedding server. If absent, falls back to Gemini `text-embedding-004`

---

## Step 1 — Put Documents in the Right Folders

```
ingestion/documents/
├── shared/
│   ├── vas/         ← VAS circulars (Thông tư Bộ Tài chính)
│   │                   e.g. TT200-2014-BTC.pdf, VAS15.pdf
│   └── ifrs/        ← IFRS standards
│                        e.g. IFRS15-Revenue.pdf, IAS1.pdf
└── tenant/
    └── dev-tenant/  ← Company-specific docs (GL policies, audit notes)
```

Supported file types: `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls`, `.txt`, `.md`

---

## Step 2 — Start Qdrant

```powershell
docker-compose -f infra/docker/docker-compose.qdrant.yml up -d
```

Verify: http://localhost:6333/dashboard

---

## Step 3 — Run Ingestion

### Option A — PowerShell script (easiest)

From repo root:

```powershell
# Ingest all folders
.\ingest.ps1

# Ingest only VAS documents
.\ingest.ps1 -Scope vas

# Ingest only IFRS documents
.\ingest.ps1 -Scope ifrs

# Dry run (chunk only, no embedding/upsert) — check output first
.\ingest.ps1 -DryRun

# Force recreate collections (clean slate)
.\ingest.ps1 -Recreate
```

### Option B — Python directly

```powershell
cd apps/backend

# VAS shared KB
python ../../ingestion/batch_embed.py `
  --docs ../../ingestion/documents/shared/vas `
  --collection kb_shared_vas `
  --scope shared

# IFRS shared KB
python ../../ingestion/batch_embed.py `
  --docs ../../ingestion/documents/shared/ifrs `
  --collection kb_shared_ifrs `
  --scope shared

# Tenant private KB
python ../../ingestion/batch_embed.py `
  --docs ../../ingestion/documents/tenant/dev-tenant `
  --collection tenant_dev-tenant `
  --scope tenant `
  --tenant-id dev-tenant
```

---

## Embedding Backend

| Backend | When used | Dim | Speed |
|---|---|---|---|
| **bge-m3 via TEI** | TEI running at localhost:8080 | 1024 | Fast (local GPU/CPU) |
| **Gemini text-embedding-004** | TEI unavailable (auto fallback) | 768 | Slower (API call) |

**Note:** Use the same backend for ingestion and query. If you ingest with Gemini (dim=768), the Qdrant collection will have dim=768. Queries will also use Gemini automatically.

To run TEI locally (requires Docker + ~4GB RAM):
```powershell
docker run -p 8080:80 ghcr.io/huggingface/text-embeddings-inference:cpu-latest `
  --model-id BAAI/bge-m3 `
  --port 80
```

---

## Verify Ingestion

After ingestion, check Qdrant dashboard: http://localhost:6333/dashboard

Or via API:
```powershell
# Count chunks in VAS collection
Invoke-RestMethod "http://localhost:6333/collections/kb_shared_vas"

# Count chunks in IFRS collection
Invoke-RestMethod "http://localhost:6333/collections/kb_shared_ifrs"
```

---

## Test a Query

With the backend running (`uvicorn app.main:app --reload` from `apps/backend`):

```powershell
# Test retrieval via chat API
$body = @{content = "VAS 15 quy định về ghi nhận doanh thu như thế nào?"; scope = "shared"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/v1/chat/stream" -Method POST -Body $body -ContentType "application/json"
```

Or open Swagger UI: http://localhost:8000/docs

---

## Eval Dataset Format

After ingestion, create eval datasets in `apps/backend/app/eval/datasets/`:

**retrieval eval** (`vas_qa_vi.jsonl`):
```jsonl
{"question": "VAS 15 ghi nhận doanh thu khi nào?", "ground_truth_doc_ids": ["<uuid-from-qdrant>"]}
{"question": "IFRS 15 khác VAS 15 như thế nào?", "ground_truth_doc_ids": ["<uuid>"]}
```

**hallucination eval** (`hallucination_test.jsonl`):
```jsonl
{"question": "VAS 15 ghi nhận doanh thu khi nào?", "answer": "<llm answer>", "contexts": ["<chunk text>"], "ground_truth": "Doanh thu được ghi nhận khi..."}
```

Run eval:
```powershell
cd apps/backend
python -m app.eval.retrieval_eval --dataset app/eval/datasets/vas_qa_vi.jsonl --k 10
python -m app.eval.hallucination_eval --dataset app/eval/datasets/hallucination_test.jsonl
```
