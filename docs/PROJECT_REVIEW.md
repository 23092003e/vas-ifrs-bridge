# Project review — 2026-11-19

## Pass 1: baseline and application startup

No application code changed in this pass.

### Verified

- Backend Ruff: passed.
- Backend mypy (`app/`): passed, 101 source files.
- Backend unit tests: 116 passed, 5 dependency deprecation warnings.
- Frontend Biome: passed, 64 files.
- Frontend Vitest: 31 passed across 7 files.
- Frontend TypeScript (`tsc --noEmit`): passed.

Backend checks used `apps/backend/.venv/bin/python`: `uv run --no-sync`
selected an environment without pytest or mypy. Initial test collection also
required downloading the tiktoken encoding; tests passed after network access.

### Confirmed finding

**P2 — CORS preflight is rejected before reaching CORSMiddleware.**

Location: `apps/backend/app/main.py:49-67`.

CORSMiddleware is registered before AuthMiddleware, putting it inside auth
under Starlette's reverse registration order. With `APP_ENV=test` and
`DEV_AUTH_BYPASS=false`, TestClient sends `OPTIONS /v1/chat/stream` with:

- `Origin: http://localhost:3000`
- `Access-Control-Request-Method: POST`
- `Access-Control-Request-Headers: authorization,content-type`

Actual: HTTP 401, `Missing Bearer token`, no Access-Control-Allow-Origin.
Browser preflights do not carry the bearer token, so direct browser calls
from an allowed origin to the backend cannot proceed. Middleware-generated
auth errors also miss CORS headers. Same-origin Next.js proxy requests are
outside this specific failure path.

Recommended fix: register CORS outside auth/tenant middleware and add a
regression test for allowed-origin preflight and unauthenticated responses.

### Remaining review scope

- API authorization and tenant isolation across every route.
- RAG retrieval, citations, LLM failures and streaming cancellation.
- Document ingestion, GL mapping and adjustment correctness.
- Database migrations and live RLS/integration checks.
- Production frontend build and browser flows.
- Deployment manifests, workers and operational recovery.

Passing baseline checks does not establish correctness of these remaining areas.

## Pass 2: flows, pipelines and business logic

Reviewed chat persistence/SSE, orchestration, retrieval/reranking/citations,
document ingestion and GL parsing/mapping/adjustment generation. No application
code was changed. Six failure scenarios were reproduced with mocked external
services using `/private/tmp/vas_pipeline_review.py` (assertions passed).

### Current flows

1. Chat: Next.js authenticated proxy → backend saves user message → orchestrator
   classifies intent and loads history → agent retrieves context → LLM streams
   tokens → citation processing → backend saves assistant message → enriched
   final event → frontend replaces streamed text with final content.
2. Documents: upload validates filename/size → writes local file → inserts DB
   record → FastAPI BackgroundTasks runs parse/chunk/dense+sparse embedding →
   Qdrant upsert → document marked ready or failed.
3. GL: frontend displays explicitly labeled sample-data sandbox. Backend upload,
   status, mapping persistence, adjustment approval and report APIs remain
   incomplete. Standalone parser/mapping/adjustment modules exist; they do not
   constitute a connected end-to-end transformation workflow.

### Confirmed findings, ordered by impact

**P1 — Retrieval discards full chunk text before reranking and prompting.**

- `apps/backend/app/rag/retriever.py:193` prefers `text_preview` over `text`.
- Shared ingestion stores 200-character previews; tenant ingestion stores
  300-character previews alongside the complete chunk. Graph expansion repeats
  the same preference at `agents/retrieval_agent.py:206` and `:247`.
- Reproduction: a chunk with a critical exception after character 300 loses that
  exception in `retrieve()` output, despite the full text being in its payload.
- Impact: semantic search finds a full chunk but reranker and LLM see only its
  beginning, potentially omitting conditions/exceptions from an accounting answer.
- Fix: prefer full text, retaining preview only as a fallback/display snippet.

**P1 — GL parser confuses opening, movement and closing amounts.**

- `apps/backend/app/gl/parser.py:33-78` selects the first column containing a
  keyword. Generic `dư` matches opening balances as well as closing balances.
- Reproduction using the frontend's downloaded template headers: opening debit
  1250, movements 8450/8100, closing debit 1600 → parsed balance is 1250.
- Separate reproduction: headers `Tên tài khoản,Số hiệu,Nợ,Có` cause the account
  name column to be used as account code because it contains `tài khoản`.
- Impact: wrong balances/account identity enter mapping silently when this module
  is used. Public GL upload currently returns 501, limiting current exposure.
- Fix: distinguish the supported balance columns explicitly, prioritize exact
  account header matches and reject ambiguous layouts.

**P1 — Adjustment normalization accepts invalid journal entries.**

- `apps/backend/app/gl/adjustments.py:103-129` defaults absent debit/credit to the
  same amount and absent accounts to empty strings; equality is the only check.
- Reproduction: LLM output `[{"amount": -100}]` becomes an accepted entry with
  debit/credit amounts -100 and both accounts empty.
- Nested multi-line journals also join account names and sum amounts, losing
  individual account allocations (`:74-93`). This was confirmed by source review,
  rather than the six-case reproducer.
- Fix: validate required accounts and finite permitted amounts at the LLM boundary;
  preserve individual debit/credit lines for multi-account entries.
- Exposure: standalone generation module; approval/storage API is still 501.

**P2 — Citation repair output bypasses the validator.**

- `apps/backend/app/agents/retrieval_agent.py:315-326` validates the first answer,
  retries once, then directly assigns retry text to final content.
- Reproduction: both generations return `Unsupported claim [C999]` with an empty
  citation map; final content still contains `[C999]` and no corresponding citation.
- Fix: validate/clean the retry before emitting the final event.

**P2 — Complete retrieval outage is treated as an empty successful search.**

- `apps/backend/app/rag/retriever.py:268-285` and
  `apps/backend/app/agents/retrieval_agent.py:115-122` skip every failed collection.
- Reproduction: all four shared collections raise `Qdrant offline`;
  `retrieve_multi()` returns `[]` instead of signaling dependency failure.
- Impact: downstream agents still invoke the LLM with no retrieved evidence. The
  caller cannot distinguish an outage from a legitimate search with no matches.
- Fix: allow partial success, but fail explicitly if every attempted source failed.

### Operational limits found by source review

- Document upload uses in-process BackgroundTasks, bypassing the existing Celery
  task and its retries. Process restart can strand pending/processing records;
  local files are not shared storage for workers/replicas. No crash recovery was
  exercised in this pass (`api/v1/documents.py:97`).
- `.xls` is accepted by document and GL dispatch but passed to openpyxl's XLSX
  reader. Supporting legacy XLS requires a reader for that format or rejecting
  it at upload validation.
- Citation validation establishes that a key exists, not that the cited source
  supports the statement. This pass did not evaluate accounting factual accuracy.

### Verification limits

Reproductions use the actual pipeline functions with mocked network/LLM clients.
They establish control-flow and data-shape failures, not live retrieval quality.
No live Ollama, Qdrant, TEI, production database or browser session was used.

Suggested repair order: full chunk text → explicit GL column parsing → journal
entry validation → citation retry validation → total retrieval failure handling →
durable ingestion and end-to-end GL implementation.
