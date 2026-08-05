# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project

VAS-IFRS Bridge — hybrid RAG knowledge engine for Vietnamese Accounting Standards (VAS) ↔ IFRS comparison, GL-to-IFRS transformation, and financial reporting. Monorepo: Next.js 14 frontend + FastAPI backend + Qdrant vector DB.

## Commands

### Backend (`apps/backend/`)

```bash
# Install (uv recommended, pip also works)
uv pip install -e ".[dev]"

# Run dev server
uvicorn app.main:app --reload --port 8000

# Lint + type-check
ruff check . && mypy app/

# Tests
pytest                                      # all
pytest tests/unit/                          # unit only
pytest tests/integration/                   # integration (needs DB + Qdrant)
pytest -k "test_name"                       # single test

# Migrations (run from apps/backend/)
alembic upgrade head
alembic revision --autogenerate -m "msg"

# RAG evaluation
python -m app.eval.retrieval_eval --dataset app/eval/datasets/vas_qa_vi.jsonl --k 10
python -m app.eval.hallucination_eval --dataset app/eval/datasets/hallucination_test.jsonl
```

### Frontend (`apps/frontend/`)

```bash
pnpm install
pnpm dev           # :3000
pnpm build
pnpm lint          # Biome
pnpm vitest run    # unit tests
pnpm vitest        # watch
```

### Full stack

```bash
make dev           # docker compose -f infra/docker/docker-compose.dev.yml up
make dev-backend   # backend only (cd apps/backend && uvicorn ...)
make dev-frontend  # frontend only
make lint          # both
make test          # both
make embed-shared  # ./skills/vas-ifrs-document-ingestion/scripts/run_ingest.sh --scope shared
```

### Ingestion (PowerShell)

```powershell
./ingest.ps1 -Scope all             # all collections
./ingest.ps1 -Scope vas             # VAS only
./ingest.ps1 -Scope ifrs            # IFRS only
./ingest.ps1 -Scope tenant -TenantId <id>
./ingest.ps1 -Recreate              # drop + recreate collections
./ingest.ps1 -DryRun                # preview without writing
```

## Architecture

### Request Flow

```
Browser → Next.js (App Router)
  → /api/chat/stream  ← SSE proxy (src/app/api/chat/stream/route.ts)
  → FastAPI /v1/...
      Middleware stack (applied bottom-up in main.py):
        TracingMiddleware → AuthMiddleware → TenantResolverMiddleware
        → RBACMiddleware → UsageLimiterMiddleware → AuditMiddleware
      → Orchestrator (keyword-based intent classifier, Phase 1)
      → Agent (RetrievalAgent | IFRSCompareAgent | GLMappingAgent | AdjustmentAgent)
          → RAG: Qdrant dense + BM25 sparse → reranker (top-8) → citation validator
          → LLM Router → provider (fast=Ollama, balanced=OpenAI, deep=Anthropic)
          → stream JSON events via SSE
```

### Intent classification (Phase 1 → Phase 2)

`_classify_intent_keywords()` in `orchestrator.py` uses keyword matching for five intents:

| Intent | Agent | Notes |
|--------|-------|-------|
| `compare` | `IFRSCompareAgent` | VAS↔IFRS diff questions |
| `mapping` | `GLMappingAgent` | GL account mapping |
| `adjustment` | `AdjustmentAgent` | Journal entry generation |
| `report` | `RetrievalAgent` (fallback) | Not yet dedicated |
| `qa` | `RetrievalAgent` | Default |

Phase 2 will replace keyword matching with a Qwen14B classifier.

`ChatRequest` fields that drive routing:
- `intent_hint` — override classification (`qa` | `compare` | `mapping` | `adjustment` | `report`)
- `reasoning` — LLM tier (`fast` | `balanced` | `deep`)
- `scope` — Qdrant search scope (`shared` | `tenant` | `both`)
- `lang` — `vi` | `en` | `auto`

### Backend structure (`apps/backend/app/`)

| Directory | Purpose |
|-----------|---------|
| `api/v1/` | REST routers: chat, kb, gl, mappings, adjustments, reports, documents, admin |
| `agents/` | Orchestrator + specialized agents (retrieval, ifrs_compare, gl_mapping, adjustment, report, citation_validator) |
| `core/` | Middleware: auth, tenant resolver, rbac, audit, usage_limiter, tracing |
| `rag/` | Retriever (hybrid dense+BM25), embedder, chunker, reranker, citation, pipelines |
| `llm/` | Provider abstraction + router (tier→provider), streaming, token meter |
| `prompts/` | Jinja2 templates, composer, registry |
| `schemas/` | Pydantic request/response models (chat, gl, kb, mapping, report) |
| `db/` | SQLAlchemy async ORM, repos, session factory |
| `tools/` | Agent tool registry (search_kb, parse_gl_file, map_account, generate_adjustment, export_report) |
| `observability/` | Structured logging, OpenTelemetry tracing, Prometheus metrics, LLM trace |
| `eval/` | JSONL datasets + retrieval/hallucination eval runners |
| `gl/` | GL analysis modules |
| `workers/` | Background tasks (Celery + Redis) |

Key files: `main.py` (app init, middleware order), `settings.py` (Pydantic env config), `deps.py` (DI: DB session, tenant ctx, auth).

### Qdrant collections

| Collection | Contents |
|-----------|---------|
| `kb_shared_vas` | VAS 01–30, circulars, decisions |
| `kb_shared_ifrs` | IFRS 1–17, IAS, IFRIC, SIC, conceptual framework |
| `tenant_{tenant_id}` | Per-tenant docs (financial statements, audit, contracts) |

Retriever constants: `DENSE_K=40`, `SPARSE_K=40`, `RERANK_K=8` (top-8 after fusion).

### Ingestion pipeline (`ingestion/`)

Raw docs (`ingestion/raw/`) → Parser → Chunker (800 tokens, 120 overlap, markdown headings) → Embedder (bge-m3 via Ollama) → Qdrant upsert. Output artifacts land in `ingestion/processed/`. Metadata (VAS↔IFRS mapping tables, citation index, taxonomy) in `ingestion/metadata/`.

### Frontend structure (`apps/frontend/src/`)

- `app/(auth)/` — login, signup, OAuth callback
- `app/(app)/` — protected routes: chat, compare, gl (upload/mappings/adjustments), documents, reports, settings
- `app/api/` — SSE proxy routes to FastAPI (stub in route.ts, returns 501 until implemented)
- `components/` — ChatStream, MappingTable, UploadDropzone, StandardDiff, shadcn UI
- `types/` — shared TypeScript types
- `middleware.ts` — Supabase auth gate (Next.js middleware, runs on all non-static routes)

### Auth & multi-tenancy

Supabase JWT in cookies → `AuthMiddleware` validates via Supabase JWKS (`/auth/v1/jwks`) → `TenantResolverMiddleware` extracts `tenant_id` → RBAC enforced per route via `rbac_table.py`. Roles (ascending): `viewer` → `auditor` → `accountant` → `admin` → `owner`. All mutations logged by `AuditMiddleware`.

### LLM routing

`llm/router.py` maps reasoning tier to provider: `fast` → Ollama, `balanced` → OpenAI, `deep` → Anthropic. Providers implement a common async streaming interface. Langfuse tracing optional (configure `LANGFUSE_*` env vars).

## Environment

Backend `.env` (see `.env.example`): `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `QDRANT_URL`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OLLAMA_BASE_URL`, `TEI_URL`, `REDIS_URL`, `GCS_BUCKET_DOCS`, `GCS_BUCKET_EXPORTS`, `SECRET_KEY`, `DEV_AUTH_BYPASS`.

Frontend `.env.local`: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `BACKEND_URL`.

Set `DEV_AUTH_BYPASS=true` locally to skip JWT validation. `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` are optional for Phase 1 (Ollama/Gemini-only dev setup).

## Key docs

- `docs/RAG_DESIGN.md` — detailed RAG pipeline architecture
- `docs/PROMPTS.md` — prompt strategy
- `docs/RUNBOOK.md` — operations
- `INGEST_GUIDE.md` — ingestion walkthrough
- `VAS_IFRS_ARCHITECTURE.md` — full system blueprint
