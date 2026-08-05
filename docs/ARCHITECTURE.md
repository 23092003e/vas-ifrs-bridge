# Kiến trúc hiện tại — VAS-IFRS Bridge

Tài liệu này mô tả code đang chạy. Bản thiết kế đích dài hạn nằm ở [VAS_IFRS_ARCHITECTURE.md](../VAS_IFRS_ARCHITECTURE.md).

## Các tầng từ ingestion

Tính từ dữ liệu đầu vào đến giao diện, hệ thống có 8 tầng logic:

1. **Ingestion** — parser và normalizer cho PDF, DOCX, XLSX, HTML, Markdown, TXT.
2. **Chunking và metadata** — chia đoạn theo heading, giữ source, language, standard code và tenant scope.
3. **Embedding/indexing** — `bge-m3` qua Ollama, vector 1024 chiều, upsert Qdrant.
4. **Retrieval/reranking** — dense + sparse retrieval; TEI reranker là tùy chọn, khi thiếu sẽ giữ thứ tự dense score.
5. **Agent/orchestration** — classifier từ khóa chọn đúng một agent cho mỗi request.
6. **LLM/prompt/citation** — provider router, prompt composition, streaming và citation validation.
7. **API/security/data** — FastAPI routers, middleware, SQLAlchemy/PostgreSQL, RLS và audit.
8. **Presentation** — Next.js 15, Supabase session gate và SSE proxy.

Các thư mục `infra/`, `supabase/`, `orchestration/` và `mcp/` là tầng vận hành/tích hợp cắt ngang, không nằm tuần tự trong request flow.

## Request flow

```text
Browser
  -> Next.js /api/chat/stream
  -> FastAPI /v1/chat/stream
  -> Tracing -> Auth -> Tenant -> RBAC -> Usage limiter -> Audit
  -> Orchestrator keyword classifier
  -> RetrievalAgent | IFRSCompareAgent | GLMappingAgent | AdjustmentAgent
  -> HybridRetriever
  -> Ollama embedding + Qdrant dense/sparse search
  -> optional TEI reranker
  -> LLM provider
  -> citation validator
  -> JSON events over SSE
```

`intent_hint` can override the keyword classifier. `reasoning` selects an LLM tier, `scope` controls shared/tenant retrieval, and `lang` controls the response language.

## Ingestion flow

```text
ingestion/raw/**
  -> parser selected by extension
  -> normalize_document_text
  -> chunk_document (target 800 tokens, overlap 120)
  -> Ollama bge-m3 embedding
  -> Qdrant collection
```

Collections:

| Collection | Purpose |
|---|---|
| `kb_shared_vas` | Shared VAS sources |
| `kb_shared_ifrs` | Shared IFRS sources |
| `tenant_<tenant_id>` | Private tenant documents |

Tenant requests may query shared, tenant, or both scopes. Tenant identity is resolved by middleware and reinforced by PostgreSQL row-level security for relational data.

## Runtime components

| Component | Current implementation |
|---|---|
| Frontend | Next.js 15.5, React 18, Supabase SSR client |
| Backend | FastAPI, async SQLAlchemy, Alembic |
| Auth | Supabase JWKS JWT validation; local-only bypass flag |
| Vector database | Qdrant 1.18.x |
| Embedding | Ollama `bge-m3`, dimension 1024 |
| Reranking | Optional TEI `bge-reranker-v2-m3`; deterministic score fallback |
| Local LLM | Ollama; external provider adapters are optional |
| Queue/cache | Redis and Celery |
| Deployment | Docker Compose locally; Terraform + GKE + Kustomize in production |

## Implementation boundary

| Area | Status |
|---|---|
| Health/readiness | Implemented |
| Streaming RAG chat | Implemented and tested |
| Parser/normalizer/chunker/embedding ingestion | Implemented |
| Auth, tenant resolution, RBAC, audit, RLS migrations | Implemented |
| Mapping and adjustment drafts through chat agents | Implemented |
| KB/document CRUD REST workflow | Explicit HTTP 501 boundary |
| GL upload/persisted mapping/approval workflow | Explicit HTTP 501 boundary |
| Persisted adjustments and report export | Explicit HTTP 501 boundary |
| Admin workflow and production n8n automation | Explicit HTTP 501/stub boundary |

The 501 routes are intentional: accounting persistence, approvals, storage lifecycle, and report formats need product contracts before implementation. Returning a clear unsupported response is safer than simulating success.

## Security model

- Supabase JWT is verified against JWKS; legacy HS256 is separately configured.
- Tenant context is derived server-side, not trusted from arbitrary client headers.
- RBAC uses ordered roles: viewer, auditor, accountant, admin, owner.
- Relational tenant tables are protected by RLS migrations.
- Qdrant tenant data uses tenant-specific collections.
- Mutation audit runs in middleware.
- Production workloads run as non-root with dropped Linux capabilities and network policies.

## Important source locations

```text
apps/backend/app/main.py                 application and middleware wiring
apps/backend/app/agents/orchestrator.py  intent classification and dispatch
apps/backend/app/rag/                    retrieval, embedding, reranking, citations
apps/backend/app/core/                   auth, tenant, RBAC, audit, rate limits
apps/backend/app/api/v1/                 HTTP and SSE contracts
apps/frontend/src/app/                   Next.js routes and proxies
ingestion/pipelines/                     offline parsing and indexing
infra/                                   local and production deployment
supabase/migrations/                     schema and RLS policy history
```
