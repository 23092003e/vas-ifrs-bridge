# RAG System Architecture — VAS-IFRS Knowledge Engine

## Overview

Hệ thống RAG (Retrieval-Augmented Generation) của VAS-IFRS gồm 2 pipeline song song:
- **Ingestion pipeline** — xử lý tài liệu offline, tạo embeddings, lưu vào Qdrant
- **Query pipeline** — xử lý câu hỏi realtime: retrieve → rerank → generate → stream

---

## 1. Ingestion Pipeline

```
Tài liệu (PDF/DOCX/XLSX)
        │
        ▼
┌───────────────────┐
│  Parser           │  PyMuPDF (PDF), python-docx (DOCX), openpyxl (XLSX)
│  + Normalizer     │  → plain text + metadata (title, lang, source, section)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Chunker          │  app/rag/chunker.py
│                   │  • Target: 800 tokens/chunk, overlap 120 tokens
│                   │  • Split tại markdown headings → giữ section context
│                   │  • Bảng (tables) giữ nguyên nếu ≤ 1500 tokens
│                   │  • Sentence boundary detection (. ! ? \n)
└────────┬──────────┘
         │  List[Chunk]
         ▼
┌───────────────────┐
│  Embedder         │  app/rag/embedder.py
│  bge-m3 via TEI   │  • Model: BAAI/bge-m3 (dim=1024, multilingual VI+EN)
│                   │  • Served via text-embeddings-inference (localhost:8080)
│                   │  • Batch size: 64, timeout: 30s
│                   │  • Output: dense vector float[1024]
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Qdrant Upsert    │  Vector DB
│                   │  • Shared KB: kb_shared_vas, kb_shared_ifrs
│                   │  • Tenant KB: tenant_{tenant_id}
│                   │  • Distance: Cosine
│                   │  • Payload: doc_id, chunk_id, text, lang, scope,
│                   │    standard_code, section, tenant_id, source_uri
└───────────────────┘
```

### Chunk payload schema

```json
{
  "doc_id": "uuid",
  "chunk_id": "uuid",
  "chunk_index": 0,
  "text": "nội dung chunk...",
  "text_preview": "200 chars đầu",
  "section_path": "Chương 1/Mục 1.2",
  "heading": "Ghi nhận doanh thu",
  "lang": "vi | en | bi",
  "scope": "shared | tenant",
  "tenant_id": "uuid | null",
  "standard_code": "VAS-15 | IFRS-15 | null",
  "source_uri": "gs://vifb-docs-dev/...",
  "embedding_model": "bge-m3@v1.5",
  "token_count": 750,
  "ingested_at": "2026-05-18T00:00:00Z"
}
```

---

## 2. Query Pipeline (Runtime)

```
User query: "IFRS 15 khác VAS 15 như thế nào?"
        │
        ▼
┌─────────────────────────────────────────────┐
│  Orchestrator  app/agents/orchestrator.py    │
│  • Classify intent: qa | compare | report    │
│  • Select model hint: fast | balanced | deep │
└──────────────────┬──────────────────────────┘
                   │ intent=compare → IFRSCompareAgent
                   │ intent=qa      → RetrievalAgent
                   ▼
┌─────────────────────────────────────────────┐
│  RetrievalAgent  app/agents/retrieval_agent  │
│                                             │
│  retrieve_multi():                           │
│    ├── retrieve(shared KB) ─────────────┐   │
│    └── retrieve(tenant KB) ─────────────┤   │
│                          asyncio.gather()│   │
│    └── merge → rerank final top-8        │   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Retriever  app/rag/retriever.py             │
│                                             │
│  1. embed_query(query)                       │
│     └── bge-m3 via TEI → float[1024]         │
│                                             │
│  2. Qdrant.search(limit=40)                  │
│     Filter: lang, scope, tenant_id           │
│     → 40 candidate chunks                   │
│                                             │
│  3. rerank(query, chunks, top_k=8)           │
│     └── bge-reranker-v2-m3 cross-encoder     │
│         min_score=0.35 (relax → 0.20)        │
│         fallback: dense score nếu TEI off    │
│                                             │
│  → List[RetrievedChunk] max 8 chunks         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Citation Wrapper  app/rag/citation.py       │
│                                             │
│  Mỗi chunk được wrap:                        │
│                                             │
│  <<C1 src="doc_id#chunk_id">>               │
│  [nội dung chunk 1...]                       │
│  <</C1>>                                    │
│                                             │
│  → context_block (inject vào system prompt) │
│  → citation_map {"C1": Citation(...)}        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  System Prompt                               │
│                                             │
│  "Answer ONLY using context below.           │
│   Cite every claim with [Cn].               │
│   Respond in {lang}."                        │
│                                             │
│  + context_block                             │
│  + user query                               │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Gemini 2.5 Flash  app/llm/providers/gemini  │
│                                             │
│  Model routing:                              │
│    fast    → gemini-2.5-flash               │
│    balanced→ gemini-2.5-flash               │
│    deep    → gemini-2.5-flash               │
│                                             │
│  Stream tokens via google-genai SDK          │
│  system_instruction + user message           │
└──────────────────┬──────────────────────────┘
                   │ stream tokens
                   ▼
┌─────────────────────────────────────────────┐
│  Citation Validator                          │
│  app/agents/citation_validator.py            │
│                                             │
│  1. Extract [Cn] keys từ answer             │
│  2. Validate key tồn tại trong citation_map  │
│  3. Unresolved → re-prompt 1 lần            │
│  4. Strip keys còn lỗi                      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  SSE Stream  app/api/v1/chat.py              │
│                                             │
│  data: {"type":"intent","intent":"qa"}       │
│  data: {"type":"token","delta":"IFRS 15 "}   │
│  data: {"type":"token","delta":"là..."}      │
│  data: {"type":"citation","key":"C1",...}    │
│  data: {"type":"final","content":"..."}      │
└─────────────────────────────────────────────┘
                   │
                   ▼
            Client (browser / curl)
```

---

## 3. Qdrant Collections

| Collection | Scope | Nội dung |
|---|---|---|
| `kb_shared_vas` | Public | VAS circulars, thông tư Bộ Tài chính |
| `kb_shared_ifrs` | Public | IFRS standards (IFRS 1–17, IAS 1–41) |
| `kb_shared_guidance` | Public | Hướng dẫn kế toán tổng hợp |
| `tenant_{tenant_id}` | Private | GL data, policy, audit notes của từng doanh nghiệp |

### Tenant isolation enforcement

```python
# Shared query
Filter(must=[FieldCondition("scope", MatchValue("shared"))])

# Tenant query — enforced server-side, không trust LLM args
Filter(must=[FieldCondition("tenant_id", MatchValue(tenant_id))])
```

---

## 4. Embedding Model — bge-m3

**Lý do chọn bge-m3:**

| Tiêu chí | bge-m3 |
|---|---|
| Multilingual | Native VI + EN trong 1 model |
| Dimension | 1024 — đủ precision cho thuật ngữ kế toán |
| Context | 8192 tokens |
| Output | Dense + Sparse + ColBERT |
| Deployment | Self-hosted, không phụ thuộc API ngoài |

**Serving stack:**
```
text-embeddings-inference (TEI)
  POST /embed  → dense vectors float[1024]
  POST /rerank → cross-encoder scores [0,1]
```

---

## 5. Reranker — bge-reranker-v2-m3

Cross-encoder nhận `(query, chunk_text)` → relevance score [0,1].

```
Threshold:
  score >= 0.35  → pass  (default MIN_SCORE)
  score >= 0.20  → pass  (LOW_RECALL_SCORE, áp dụng nếu <3 chunks pass)
  score <  0.20  → drop

TEI không available:
  → Fallback: sort by Qdrant dense score
  → Log warning: "reranker unavailable"
```

---

## 6. Citation System

### Injection (vào prompt)

```
<<C1 src="doc_uuid#chunk_uuid">>
Điều 5. Doanh thu được ghi nhận khi rủi ro và lợi ích...
<</C1>>

<<C2 src="doc_uuid#chunk_uuid">>
IFRS 15 paragraph 31. An entity shall recognise revenue...
<</C2>>
```

### Model output (expected)

```
"Theo VAS 15 [C1], doanh thu ghi nhận khi chuyển giao
rủi ro. IFRS 15 [C2] dùng mô hình 5 bước khác biệt..."
```

### Post-generation validation

```
extract [Cn] keys từ answer
    ↓
validate key ∈ citation_map
    ↓
unresolved? → re-prompt 1 lần với instruction "fix citations"
    ↓
vẫn còn? → strip [Cn] khỏi answer
    ↓
emit citation SSE events cho từng key hợp lệ
```

---

## 7. Fallback Strategy

| Failure | Behavior |
|---|---|
| TEI embedder timeout | Raise `EmbedderTimeout` → 503 |
| TEI unavailable (ingestion) | Auto-fallback Gemini `text-embedding-004` (dim=768) |
| TEI unavailable (query) | Auto-fallback Gemini embedding, log `warning` |
| Qdrant unavailable | Raise `QdrantUnavailable` → 503 |
| Reranker timeout | Dùng dense score, log `reranker unavailable` |
| 0 chunks retrieved | Empty context → model từ chối trả lời |
| <3 chunks pass threshold | Relax từ 0.35 → 0.20, log `low_recall` |
| Citation unresolved | Re-prompt 1 lần → strip markers còn lại |
| Gemini API error | Emit `{"type":"error","message":"..."}` SSE |
| Tenant KB unavailable | Tiếp tục với shared KB only |

---

## 8. Key Parameters

| Parameter | Value | Location |
|---|---|---|
| Chunk target size | 800 tokens | `chunker.py::TARGET_TOKENS` |
| Chunk overlap | 120 tokens | `chunker.py::OVERLAP_TOKENS` |
| Max table size | 1500 tokens | `chunker.py::MAX_TABLE_TOKENS` |
| Embed batch size | 64 | `embedder.py::BATCH_SIZE` |
| Embed dim (bge-m3 / TEI) | 1024 | `embedder.py::EMBED_DIM` |
| Embed dim (Gemini fallback) | 768 | `embedder.py::EMBED_DIM_GEMINI` |
| Query LRU cache | 512 entries | `embedder.py` |
| Dense search k | 40 | `retriever.py::DENSE_K` |
| Final rerank k | 8 | `retriever.py::RERANK_K` |
| Rerank threshold | 0.35 | `reranker.py::MIN_SCORE` |
| Rerank relax threshold | 0.20 | `reranker.py::LOW_RECALL_SCORE` |
| Reranker timeout | 15s | `reranker.py::TIMEOUT_S` |
| Embedder timeout | 30s | `embedder.py::TIMEOUT_S` |

---

## 9. File Map

```
apps/backend/app/
├── rag/
│   ├── chunker.py            Section-aware text splitter
│   ├── embedder.py           bge-m3 via TEI (dim=1024), Gemini fallback (dim=768), LRU cache
│   ├── reranker.py           bge-reranker-v2-m3 via TEI, threshold logic
│   ├── retriever.py          Dense Qdrant search + multi-collection merge
│   ├── citation.py           Wrap chunks, validate/resolve [Cn] keys
│   └── pipelines/
│       ├── shared.py         Ingest VAS + IFRS shared KB
│       └── tenant.py         Ingest + lifecycle tenant private KB
├── agents/
│   ├── base.py               AgentBase ABC
│   ├── retrieval_agent.py    Q&A: retrieve → prompt → stream + cite
│   ├── ifrs_compare_agent.py VAS↔IFRS structured comparison
│   ├── citation_validator.py Post-gen [Cn] validation + cleanup
│   └── orchestrator.py       Intent classify → agent dispatch
└── llm/
    └── providers/
        └── gemini.py         Gemini 2.5 Flash (primary LLM)

ingestion/
├── documents/
│   ├── shared/
│   │   ├── vas/              ← Bỏ VAS circulars vào đây
│   │   └── ifrs/             ← Bỏ IFRS standards vào đây
│   └── tenant/
│       └── dev-tenant/       ← Tài liệu riêng tenant
├── batch_embed.py            Chunk → embed (TEI/Gemini) → upsert Qdrant
├── unstructured_runner.py    PDF/DOCX/XLSX/TXT → JSON (lang detect, std_code extract)
└── parsed/                   ← Auto-created: intermediate JSON per document

ingest.ps1                    One-command ingest runner (PowerShell, repo root)
```

---

## 10. Sequence Diagram — Chat Q&A

```
Client          API           Orchestrator    Retriever      Gemini
  │               │                │               │            │
  │─POST /stream──▶               │               │            │
  │               │─classify───────▶               │            │
  │               │◀─intent=qa─────               │            │
  │               │─arun()─────────▶               │            │
  │               │                │─embed_query───▶            │
  │               │                │◀──vector───────            │
  │               │                │─qdrant.search──▶           │
  │               │                │◀──40 hits───────           │
  │               │                │─rerank(top 8)──▶           │
  │               │                │◀──scored chunks─           │
  │               │                │─wrap citations──           │
  │               │─SSE intent──────────────────────────────────│
  │◀─intent event─│                │─stream_chat()──────────────▶
  │               │                │◀──token stream──────────────
  │◀─token events─│                │                │            │
  │               │                │─validate cites─            │
  │◀─cite events──│                │                │            │
  │◀─final event──│                │                │            │
```

---

---

## 11. Ingestion Pipeline (Offline)

```
PDF / DOCX / XLSX / TXT
        │
        ▼
┌───────────────────────────┐
│  unstructured_runner.py   │  PyMuPDF, python-docx, openpyxl
│                           │  → lang detect (VI/EN by Unicode)
│                           │  → standard_code extract (VAS-15, IFRS-15)
│                           │  → JSON: {text, sections, lang, standard_code}
└────────────┬──────────────┘
             │
             ▼
┌───────────────────────────┐
│  batch_embed.py           │
│  chunk_document()         │  800 token target, 120 overlap
│  → List[Chunk]            │  section-aware, table-aware
└────────────┬──────────────┘
             │
             ▼
┌───────────────────────────┐
│  embed_texts()            │  TEI bge-m3 (dim=1024)  ← preferred
│                           │  Gemini text-embedding-004 (dim=768) ← fallback
└────────────┬──────────────┘
             │
             ▼
┌───────────────────────────┐
│  Qdrant upsert            │
│  kb_shared_vas            │  VAS circulars
│  kb_shared_ifrs           │  IFRS standards
│  tenant_{id}              │  Private per-tenant
└───────────────────────────┘
```

### Embedding backend selection

| Backend | Condition | Dim | Collection must use |
|---|---|---|---|
| bge-m3 (TEI) | TEI running at `TEI_URL` | 1024 | 1024 |
| Gemini text-embedding-004 | TEI unavailable (auto-fallback) | 768 | 768 |

**Ingest and query must use same backend** — dim mismatch causes Qdrant search to fail.

### Run ingestion

```powershell
# Start Qdrant
docker-compose -f infra/docker/docker-compose.qdrant.yml up -d

# Ingest all documents (from repo root)
.\ingest.ps1

# Dry run (parse + chunk only, no embed/upsert)
.\ingest.ps1 -DryRun

# Clean slate
.\ingest.ps1 -Recreate
```

See `INGEST_GUIDE.md` for full details.

---

## 12. Evaluation

```
apps/backend/app/eval/
├── retrieval_eval.py     Recall@K, MRR, Precision@K  (threshold: recall@10 ≥ 0.85)
├── hallucination_eval.py Faithfulness, AnswerRelevancy, ContextRecall, ContextPrecision
│                         (Gemini LLM-as-judge, threshold: faith ≥ 0.85, halluc ≤ 0.03)
└── datasets/             JSONL eval datasets (create after ingestion)
```

```powershell
cd apps/backend
python -m app.eval.retrieval_eval --dataset app/eval/datasets/vas_qa_vi.jsonl --k 10
python -m app.eval.hallucination_eval --dataset app/eval/datasets/hallucination_test.jsonl
```

---

*Last updated: 2026-05-18*
