# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

VAS-IFRS Bridge — hybrid RAG knowledge engine for Vietnamese Accounting Standards (VAS) ↔ IFRS comparison, GL-to-IFRS transformation, and financial reporting. Monorepo: Next.js 14 frontend + FastAPI backend + Qdrant vector DB.

## Commands

### Backend (`apps/backend/`)

```bash
# Install (uv)
pip install -e ".[dev]"

# Run dev server
uvicorn app.main:app --reload --port 8000

# Lint + type-check
ruff check . && mypy app/

# Tests
pytest                                      # all
pytest tests/unit/                          # unit only
pytest tests/integration/                   # integration (needs DB + Qdrant)
pytest -k "test_name"                       # single test

# Migrations
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
make dev-backend   # backend only
make dev-frontend  # frontend only
make lint          # both
make test          # both
make embed-shared  # ingest VAS + IFRS docs into Qdrant
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
  → /api/chat/stream  ← SSE proxy
  → FastAPI /v1/...
      Middleware stack: Auth → TenantResolver → RBAC → Audit → UsageLimiter → Tracing
      → Orchestrator (classifies intent)
      → Agent (RetrievalAgent | IFRSCompareAgent | GLMappingAgent | ReportAgent)
          → RAG: Qdrant dense + BM25 sparse → reranker → citation validator
          → LLM Router → provider (fast=Ollama, balanced=GPT-4o, deep=Claude Sonnet)
          → stream JSON events via SSE
```

### Backend structure (`apps/backend/app/`)

| Directory | Purpose |
|-----------|---------|
| `api/v1/` | REST routers: chat, kb, gl, mappings, adjustments, reports, documents, admin |
| `agents/` | Orchestrator + specialized agents (retrieval, ifrs_compare, gl_mapping, adjustment, report, citation_validator) |
| `core/` | Middleware: auth, tenant resolver, rbac, audit, usage_limiter, tracing |
| `rag/` | Retriever (hybrid), embedder, chunker, reranker, citation, pipelines |
| `llm/` | Provider abstraction + router, streaming, token meter |
| `prompts/` | Jinja2 templates, composer, registry |
| `db/` | SQLAlchemy async ORM, repos, session factory |
| `tools/` | Agent tool registry (search_kb, parse_gl_file, map_account, generate_adjustment, export_report) |
| `eval/` | JSONL datasets + retrieval/hallucination eval runners |
| `gl/` | GL analysis modules |
| `workers/` | Background tasks |

Key files: `main.py` (app init), `settings.py` (Pydantic env config), `deps.py` (DI: DB session, tenant ctx, auth).

### Qdrant collections

| Collection | Contents |
|-----------|---------|
| `kb_shared_vas` | VAS 01–30, circulars, decisions |
| `kb_shared_ifrs` | IFRS 1–17, IAS, IFRIC, SIC, conceptual framework |
| `tenant_{tenant_id}` | Per-tenant docs (financial statements, audit, contracts) |

### Ingestion pipeline (`ingestion/`)

Raw docs (`ingestion/raw/`) → Parser → Chunker (800 tokens, 120 overlap, markdown headings) → Embedder (bge-m3 via TEI or Gemini) → Qdrant upsert. Output artifacts land in `ingestion/processed/`. Metadata (VAS↔IFRS mapping tables, citation index, taxonomy) in `ingestion/metadata/`.

### Frontend structure (`apps/frontend/src/`)

- `app/(auth)/` — login, signup, OAuth callback
- `app/(app)/` — protected: chat, compare, gl/upload+mappings+adjustments, documents, reports, settings
- `app/api/` — SSE proxy routes to FastAPI
- `components/` — ChatStream, MappingTable, UploadDropzone, StandardDiff, shadcn UI
- `lib/` — `supabase/client.ts`, `supabase/server.ts`, `api/client.ts` (typed FastAPI SDK), `i18n/{vi,en}.ts`, hooks
- `types/` — shared TypeScript types

Key hooks: `useChat` (chat state + SSE), `useTenant` (tenant context), `useStream` (SSE event handling).

### Auth & multi-tenancy

Supabase JWT in cookies → `AuthMiddleware` validates → `TenantResolverMiddleware` extracts `tenant_id` → RBAC enforced per route via `rbac_table.py`. All mutations logged by `AuditMiddleware`.

### LLM routing

`llm/router.py` selects provider based on reasoning tier: `fast` → Ollama, `balanced` → OpenAI GPT-4o, `deep` → Anthropic Claude 3.5 Sonnet. Providers implement a common async streaming interface.

## Environment

Backend `.env` (see `.env.example`): `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `QDRANT_URL`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OLLAMA_BASE_URL`, `TEI_URL`, `REDIS_URL`, `GCS_BUCKET_DOCS`, `GCS_BUCKET_EXPORTS`, `SECRET_KEY`, `DEV_AUTH_BYPASS`.

Frontend `.env.local`: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `BACKEND_URL`.

Set `DEV_AUTH_BYPASS=true` locally to skip JWT validation during development.

## Key docs

- `docs/RAG_DESIGN.md` — detailed RAG pipeline architecture
- `docs/PROMPTS.md` — prompt strategy
- `docs/RUNBOOK.md` — operations
- `INGEST_GUIDE.md` — ingestion walkthrough
- `VAS_IFRS_ARCHITECTURE.md` — full system blueprint
