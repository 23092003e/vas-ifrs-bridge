# VAS-IFRS Knowledge Engine — Implementation Blueprint

---

# 1. PROJECT STRUCTURE

```
vas-ifrs-bridge/
├── apps/
│   ├── frontend/                          # Next.js 14 App Router
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── (auth)/
│   │   │   │   │   ├── login/page.tsx
│   │   │   │   │   ├── signup/page.tsx
│   │   │   │   │   └── callback/route.ts
│   │   │   │   ├── (app)/
│   │   │   │   │   ├── layout.tsx                # tenant context provider
│   │   │   │   │   ├── chat/
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   └── [conversationId]/page.tsx
│   │   │   │   │   ├── compare/page.tsx          # VAS↔IFRS side-by-side
│   │   │   │   │   ├── gl/
│   │   │   │   │   │   ├── upload/page.tsx
│   │   │   │   │   │   ├── mappings/page.tsx
│   │   │   │   │   │   └── adjustments/page.tsx
│   │   │   │   │   ├── documents/page.tsx
│   │   │   │   │   ├── reports/page.tsx
│   │   │   │   │   └── settings/
│   │   │   │   │       ├── tenant/page.tsx
│   │   │   │   │       ├── users/page.tsx
│   │   │   │   │       └── audit/page.tsx
│   │   │   │   ├── api/
│   │   │   │   │   ├── chat/stream/route.ts      # SSE proxy to FastAPI
│   │   │   │   │   └── upload/route.ts
│   │   │   │   ├── layout.tsx
│   │   │   │   └── globals.css
│   │   │   ├── components/
│   │   │   │   ├── chat/{ChatStream,MessageList,CitationCard,LangToggle}.tsx
│   │   │   │   ├── gl/{UploadDropzone,MappingTable,AdjustmentReview}.tsx
│   │   │   │   ├── compare/{StandardDiff,ParallelView}.tsx
│   │   │   │   └── ui/                           # shadcn primitives
│   │   │   ├── lib/
│   │   │   │   ├── supabase/{client,server,middleware}.ts
│   │   │   │   ├── api/client.ts                 # typed FastAPI SDK
│   │   │   │   ├── hooks/{useChat,useTenant,useStream}.ts
│   │   │   │   └── i18n/{vi,en}.ts
│   │   │   ├── middleware.ts                     # auth + tenant gate
│   │   │   └── types/{api,domain}.ts
│   │   ├── tailwind.config.ts
│   │   ├── next.config.mjs
│   │   ├── tsconfig.json
│   │   ├── package.json
│   │   ├── Dockerfile
│   │   └── .env.local.example
│   │
│   └── backend/                           # FastAPI Python 3.11
│       ├── app/
│       │   ├── main.py
│       │   ├── deps.py                           # DI: db, supabase, qdrant
│       │   ├── settings.py                       # pydantic-settings
│       │   ├── core/
│       │   │   ├── auth.py                       # JWT validation
│       │   │   ├── tenant.py                     # tenant resolver
│       │   │   ├── rbac.py
│       │   │   ├── tracing.py                    # OTel
│       │   │   ├── usage_limiter.py
│       │   │   ├── audit.py
│       │   │   └── errors.py
│       │   ├── api/v1/
│       │   │   ├── router.py
│       │   │   ├── chat.py                       # SSE stream
│       │   │   ├── kb.py
│       │   │   ├── gl.py
│       │   │   ├── mapping.py
│       │   │   ├── adjustments.py
│       │   │   ├── reports.py
│       │   │   ├── documents.py
│       │   │   └── admin.py
│       │   ├── agents/
│       │   │   ├── base.py                       # AgentBase, ToolBase
│       │   │   ├── retrieval_agent.py
│       │   │   ├── ifrs_compare_agent.py
│       │   │   ├── gl_mapping_agent.py
│       │   │   ├── adjustment_agent.py
│       │   │   ├── report_agent.py
│       │   │   ├── citation_validator.py
│       │   │   └── orchestrator.py               # router/dispatcher
│       │   ├── tools/
│       │   │   ├── search_shared_kb.py
│       │   │   ├── search_tenant_kb.py
│       │   │   ├── parse_gl_file.py
│       │   │   ├── map_account.py
│       │   │   ├── generate_adjustment.py
│       │   │   ├── export_report.py
│       │   │   └── registry.py
│       │   ├── llm/
│       │   │   ├── router.py                     # cost/latency routing
│       │   │   ├── providers/{ollama,openai,anthropic}.py
│       │   │   ├── streaming.py
│       │   │   └── token_meter.py
│       │   ├── rag/
│       │   │   ├── embedder.py                   # bge-m3
│       │   │   ├── reranker.py                   # bge-reranker-v2
│       │   │   ├── chunker.py
│       │   │   ├── retriever.py                  # hybrid
│       │   │   ├── citation.py
│       │   │   └── pipelines/{shared,tenant}.py
│       │   ├── ingestion/
│       │   │   ├── parsers/{pdf,docx,xlsx,html}.py
│       │   │   ├── normalizer.py
│       │   │   ├── enrichment.py                 # standard/section tagging
│       │   │   └── jobs.py
│       │   ├── gl/
│       │   │   ├── parser.py                     # PyMuPDF / openpyxl
│       │   │   ├── coa_loader.py
│       │   │   ├── mapping_engine.py
│       │   │   └── adjustments.py
│       │   ├── prompts/
│       │   │   ├── registry.py                   # load/version
│       │   │   ├── composer.py                   # Jinja2 assembly
│       │   │   ├── system/
│       │   │   │   ├── base.vi.j2
│       │   │   │   ├── base.en.j2
│       │   │   │   ├── retrieval_qa.j2
│       │   │   │   ├── ifrs_compare.j2
│       │   │   │   ├── gl_mapping.j2
│       │   │   │   ├── adjustment_entry.j2
│       │   │   │   └── report_synthesis.j2
│       │   │   └── fragments/{citation,tenant_ctx,safety}.j2
│       │   ├── db/
│       │   │   ├── session.py                    # asyncpg/SQLAlchemy
│       │   │   ├── models/                       # ORM
│       │   │   └── repos/
│       │   ├── schemas/                          # pydantic
│       │   │   └── {chat,gl,mapping,report,kb}.py
│       │   ├── workers/
│       │   │   ├── celery_app.py
│       │   │   ├── ingestion_tasks.py
│       │   │   ├── gl_tasks.py
│       │   │   └── report_tasks.py
│       │   ├── eval/
│       │   │   ├── retrieval_eval.py
│       │   │   ├── hallucination_eval.py
│       │   │   ├── mapping_eval.py
│       │   │   └── datasets/
│       │   └── observability/
│       │       ├── logging.py                    # structlog
│       │       ├── metrics.py                    # prometheus
│       │       └── llm_trace.py                  # langfuse adapter
│       ├── alembic/
│       │   ├── versions/
│       │   └── env.py
│       ├── tests/
│       │   ├── unit/
│       │   ├── integration/
│       │   └── e2e/
│       ├── pyproject.toml
│       ├── Dockerfile
│       └── .env.example
│
├── ingestion/                              # standalone heavy parsers
│   ├── pipelines/{vas_circulars,ifrs_standards,tenant_docs}.py
│   ├── unstructured_runner.py
│   ├── batch_embed.py
│   └── Dockerfile
│
├── orchestration/
│   ├── n8n/
│   │   ├── workflows/
│   │   │   ├── 01_doc_ingest_trigger.json
│   │   │   ├── 02_embedding_pipeline.json
│   │   │   ├── 03_gl_processing.json
│   │   │   ├── 04_retry_dlq.json
│   │   │   ├── 05_report_generation.json
│   │   │   └── 06_audit_export.json
│   │   ├── credentials.template.json
│   │   └── docker-compose.n8n.yml
│   └── README.md
│
├── infra/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── gke.tf
│   │   ├── gcs.tf
│   │   ├── vpc.tf
│   │   ├── iam.tf
│   │   ├── secrets.tf                            # Secret Manager
│   │   ├── gpu_node_pool.tf
│   │   └── envs/{staging,prod}.tfvars
│   ├── k8s/
│   │   ├── base/
│   │   │   ├── backend-deploy.yaml
│   │   │   ├── frontend-deploy.yaml
│   │   │   ├── qdrant-statefulset.yaml
│   │   │   ├── ollama-deploy.yaml                # GPU
│   │   │   ├── n8n-deploy.yaml
│   │   │   ├── celery-worker.yaml
│   │   │   ├── ingress.yaml
│   │   │   └── network-policies.yaml
│   │   └── overlays/{staging,prod}/
│   ├── docker/
│   │   ├── docker-compose.dev.yml
│   │   ├── docker-compose.qdrant.yml
│   │   └── docker-compose.ollama.yml
│   └── helm/
│       ├── qdrant/
│       └── ollama/
│
├── prompts/                                # versioned prompt registry
│   ├── registry.yaml                             # name→file→version
│   └── v1/
│       └── (mirrors backend/app/prompts/system)
│
├── supabase/
│   ├── migrations/
│   │   ├── 0001_init.sql
│   │   ├── 0002_rls_policies.sql
│   │   ├── 0003_kb_chunks.sql
│   │   ├── 0004_gl_tables.sql
│   │   └── 0005_audit.sql
│   ├── functions/                                # edge functions (Deno)
│   │   ├── on-document-upload/index.ts
│   │   ├── on-gl-upload/index.ts
│   │   └── tenant-provisioner/index.ts
│   └── config.toml
│
├── mcp/
│   ├── servers/
│   │   ├── qdrant_mcp/
│   │   ├── supabase_mcp/
│   │   ├── n8n_mcp/
│   │   └── filesystem_mcp/                       # reuse @modelcontextprotocol/server-filesystem
│   └── mcp_servers.json
│
├── tests/
│   ├── e2e_playwright/
│   ├── load/k6/
│   └── eval/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── RAG_DESIGN.md
│   ├── PROMPTS.md
│   └── RUNBOOK.md
│
├── .github/workflows/
│   ├── ci-backend.yml
│   ├── ci-frontend.yml
│   ├── eval-nightly.yml
│   └── deploy-prod.yml
├── Makefile
├── README.md
└── pnpm-workspace.yaml
```

---

# 2. PHASE ROADMAP

## Phase 1 — MVP RAG Core (8–10 weeks)

| Item | Detail |
|---|---|
| Goals | Auth, shared KB ingestion, RAG chat (VI/EN), VAS↔IFRS compare view |
| Deliverables | Supabase auth+RLS, ingestion of VAS circulars + IFRS standards into Qdrant, FastAPI `/v1/chat/stream`, Next.js chat UI w/ streaming, citation cards, compare page |
| Dependencies | GCP project, Supabase project, Qdrant cluster, Ollama+Qwen14B GPU node, OpenAI+Anthropic keys |
| Effort | 2 BE, 2 FE, 1 ML/RAG, 1 DevOps, 1 PM |
| Risks | bge-m3 latency on CPU; Qwen14B Vietnamese quality; IFRS copyright (see §16) |
| Acceptance | p95 chat <8s, ≥0.85 retrieval recall@10 on eval set, 100% citations resolvable, RLS verified by adversarial test |

## Phase 2 — GL Transformation (6–8 weeks)

| Item | Detail |
|---|---|
| Goals | Tenant KB, Excel/CSV GL upload, AI mapping, adjustment entries |
| Deliverables | `/v1/gl/upload`, mapping engine + review UI, adjustment generator, per-tenant Qdrant collection lifecycle, n8n GL workflow |
| Dependencies | Phase 1 prompts/registry, Celery/Redis, GCS bucket per env |
| Effort | 2 BE, 1 FE, 1 ML, 1 accounting SME (part-time) |
| Risks | GL schema variance across clients; mapping accuracy <90% blocks adoption |
| Acceptance | Parse 100k rows <60s, ≥0.92 mapping top-1 on benchmark CoA, adjustments traceable to source GL row |

## Phase 3 — Enterprise (6 weeks)

| Item | Detail |
|---|---|
| Goals | Reports, audit trail, exports (PDF/XLSX), admin dashboard, usage analytics |
| Deliverables | Report Generator Agent, audit log viewer, role admin, usage metering, billing hooks |
| Dependencies | Phases 1+2 stable, Langfuse instance, Stripe (optional) |
| Effort | 1 BE, 2 FE, 1 DevOps |
| Risks | Audit completeness gap = compliance fail; export PII leak |
| Acceptance | All mutating endpoints log audit row, exports redact secrets, admin can revoke user in <5s |

---

# 3. CLAUDE / LLM SETUP

## Prompt registry

`prompts/registry.yaml` — single source of truth. Loaded at boot by `prompts/registry.py`.

```yaml
prompts:
  base.system:
    versions:
      v1: system/base.{lang}.j2
    default: v1
  retrieval.qa:
    versions: { v1: system/retrieval_qa.j2, v2: system/retrieval_qa.j2 }
    default: v2
  ifrs.compare:
    default: v1
    versions: { v1: system/ifrs_compare.j2 }
  gl.mapping: { default: v1, versions: { v1: system/gl_mapping.j2 } }
  adjustment.entry: { default: v1, versions: { v1: system/adjustment_entry.j2 } }
  report.synthesis: { default: v1, versions: { v1: system/report_synthesis.j2 } }
fragments:
  citation: fragments/citation.j2
  tenant_ctx: fragments/tenant_ctx.j2
  safety: fragments/safety.j2
```

## Composer

`prompts/composer.py` — Jinja2 env, per-call assembly:

```python
class PromptComposer:
    def build(self, *, name: str, lang: str, tenant: TenantCtx,
              retrieval: list[Chunk], user_msg: str, version: str|None=None) -> Messages:
        sys = render(name, lang=lang, tenant=tenant, retrieval=retrieval, version=version)
        sys += "\n\n" + render("fragments/safety")
        return [{"role":"system","content":sys},
                {"role":"user","content":user_msg}]
```

Every prompt receives: `tenant_id`, `tenant_name`, `lang`, `retrieval[]`, `now_iso`, `policy_flags`.

## Routing policy (`llm/router.py`)

| Task | Primary | Escalation | Reason |
|---|---|---|---|
| Quick VI Q&A, summarization | Qwen 14B (Ollama) | GPT-4.5 if confidence<0.7 | Cost |
| IFRS compare reasoning | GPT-4.5 | Claude Sonnet 4.6 if tokens>32k | Reasoning |
| GL mapping (per row batch) | Qwen 14B | GPT-4.5 if ambiguous score | Volume |
| Long report synthesis | Claude Sonnet 4.6 | Claude Opus 4.7 if depth flag | Long ctx |
| Adjustment entry generation | GPT-4.5 | Claude Opus 4.7 on complex multi-period | Precision |
| Citation validation | Qwen 14B | — | Cheap structured task |

```python
class LLMRouter:
    def select(self, task: TaskKind, ctx: RouteCtx) -> ModelHandle:
        if task == TaskKind.QA_VI and ctx.expected_tokens < 4000:
            return self.ollama("qwen2.5:14b-instruct")
        if task == TaskKind.IFRS_COMPARE:
            return self.openai("gpt-4.5") if ctx.tokens < 32_000 \
                else self.anthropic("claude-sonnet-4-6")
        if task == TaskKind.REPORT_LONG:
            return self.anthropic("claude-opus-4-7" if ctx.depth=="deep"
                                  else "claude-sonnet-4-6")
        # ... see table
```

## Standard completion flow

`user → API → Orchestrator → Retrieval Agent → Composer → LLMRouter → provider (stream) → Citation Validator → SSE → client`

## Extended thinking flow

For Claude Opus/Sonnet on report+adjustment tasks set `thinking: {type:"enabled", budget_tokens: 8000}`. Trigger when:
- task == REPORT_LONG and ctx.tokens > 50k
- task == ADJUSTMENT and rule_count > 5
- explicit `?reasoning=deep` flag

## Reasoning escalation

```
attempt → check confidence (self-eval prompt small Qwen call)
       → if score<θ: escalate next tier
       → max 2 escalations, then mark "low_confidence" in response
```

## Context injection order

1. Base system (lang)
2. Tenant fragment (`tenant_ctx`)
3. Task-specific system
4. Retrieval block (top-k reranked, with `[doc_id:chunk_id]` markers)
5. Safety fragment (last)
6. User message

## Citation grounding

Every retrieved chunk wrapped: `<<C{n} src="{doc_id}#{chunk_id}">>...<</C{n}>>`. Model required to emit `[C{n}]` inline. Citation Validator rejects answers with unresolved markers.

---

# 4. AGENT ARCHITECTURE

All agents inherit `agents/base.py::AgentBase`. Output schemas = pydantic.

### 4.1 Retrieval Agent
- **Trigger**: every chat turn, every compare/mapping task
- **Input**: `{query, lang, tenant_id, scope: shared|tenant|both, k:int=20}`
- **Output**: `{chunks: List[Chunk], rerank_scores, latency_ms}`
- **LLM**: none (pure retrieval); optional Qwen14B for query rewrite
- **Tools**: `search_shared_kb`, `search_tenant_kb`
- **Failure**: empty result → fallback to BM25-only; vector store down → 503 + cached top docs
- **Retry**: 3× expo on Qdrant 5xx (backoff 0.5,1,2s)

### 4.2 IFRS Comparison Agent
- **Trigger**: `/v1/chat` with intent=compare, or `/v1/compare`
- **Input**: `{topic, vas_refs[], ifrs_refs[], lang}`
- **Output**: `{summary, differences:[{aspect, vas, ifrs, impact}], citations[]}`
- **LLM**: GPT-4.5 → Sonnet 4.6 escalate
- **Tools**: `search_shared_kb`
- **Failure**: missing standard ref → ask clarifying Q
- **Retry**: 2× on provider 429/5xx

### 4.3 GL Mapping Agent
- **Trigger**: post-parse of GL upload, batch of 200 rows
- **Input**: `{rows:[{account_code,account_name,balance,...}], coa_target:VAS|IFRS}`
- **Output**: `{mappings:[{src_account, target_account, confidence, rationale}]}`
- **LLM**: Qwen14B; escalate to GPT-4.5 if confidence<0.7 per row
- **Tools**: `map_account_to_standard`, `search_shared_kb`
- **Failure**: low-confidence row → mark `requires_review=true`, no auto-commit
- **Retry**: idempotent via `batch_id`

### 4.4 Adjustment Entry Agent
- **Trigger**: after mapping confirmed
- **Input**: `{tenant_id, mappings, period, rules:[ifrs_rule_id]}`
- **Output**: `{entries:[{date, dr_account, cr_account, amount, narration, rule_ref, citation}]}`
- **LLM**: GPT-4.5; Opus 4.7 with extended thinking when ≥3 interacting rules
- **Tools**: `generate_adjustment_entry`, `search_shared_kb`
- **Failure**: unbalanced JE → reject + log; arithmetic check enforced post-LLM
- **Retry**: 1×, then escalate model

### 4.5 Report Generator Agent
- **Trigger**: `/v1/reports/generate`
- **Input**: `{tenant_id, scope, period, sections[]}`
- **Output**: `{report_id, sections:[{title, markdown, citations[]}], export_uri}`
- **LLM**: Claude Sonnet 4.6 default, Opus 4.7 if `depth=deep`
- **Tools**: `search_shared_kb`, `search_tenant_kb`, `export_comparison_report`
- **Failure**: section fail → continue, mark partial
- **Retry**: per-section, 2×

### 4.6 Citation Validator
- **Trigger**: post-completion every agent emitting citations
- **Input**: `{answer_text, citation_map}`
- **Output**: `{valid:bool, unresolved:[], stripped_answer}`
- **LLM**: Qwen14B (structured) or rule-based regex
- **Failure**: unresolved >0 → re-prompt original agent w/ "fix citations" instruction (max 1 retry)

### Orchestrator
`agents/orchestrator.py` — intent classifier (Qwen14B prompt) → dispatch graph. Concurrency via `asyncio.TaskGroup`.

---

# 5. HOOKS AND WORKFLOWS

## 5.1 FastAPI middleware order (`app/main.py`)

```python
app.add_middleware(RequestIDMiddleware)        # uuid → context
app.add_middleware(TracingMiddleware)          # OTel span
app.add_middleware(AuthMiddleware)             # supabase JWT verify
app.add_middleware(TenantResolverMiddleware)   # x-tenant-id → context
app.add_middleware(RBACMiddleware)             # route → required_role
app.add_middleware(UsageLimiterMiddleware)     # token + req quota
app.add_middleware(AuditMiddleware)            # mutating ops → audit_logs
```

Key files:
- `core/auth.py` — verifies Supabase JWT (jwks cached), populates `request.state.user`
- `core/tenant.py` — resolves from JWT claim `tenant_id`; 403 if mismatch with header
- `core/rbac.py` — decorator `@require(Role.ADMIN)`; route table in `core/rbac_table.py`
- `core/usage_limiter.py` — Redis token-bucket per `(tenant_id, endpoint)`
- `core/audit.py` — async write to `audit_logs` w/ diff payload

## 5.2 n8n workflows

| ID | Trigger | Steps |
|---|---|---|
| 01_doc_ingest | Supabase webhook on `documents.insert` | Fetch from GCS → Unstructured.io → chunk → embed batch → Qdrant upsert → mark `ingested` |
| 02_embedding_pipeline | Manual / cron | Re-embed when model version bumps; reads `kb_chunks.embedding_model` |
| 03_gl_processing | `gl_uploads.insert` | Parse → CoA validate → enqueue mapping batches → notify FE via Supabase Realtime |
| 04_retry_dlq | Error branch all wfs | Push to `dlq` table; alert Slack after 3 fails |
| 05_report_generation | `/v1/reports/generate` queue | Sectioned LLM calls → assemble → render PDF (WeasyPrint) → GCS → signed URL |
| 06_audit_export | Cron daily | Snapshot `audit_logs` → GCS cold bucket |

## 5.3 Qdrant lifecycle (`rag/pipelines/tenant.py`)

- **Provision**: on tenant creation, create collection `tenant_{tenant_id}` with payload index on `doc_id`, `kind`, `lang`, `period`. Vector dim=1024 (bge-m3), distance=Cosine.
- **Optimize**: nightly `optimizers_config.indexing_threshold=20000`; HNSW `m=32, ef_construct=256`.
- **Delete**: on tenant offboarding, snapshot → GCS archive bucket (encrypted) → drop collection.
- **Quotas**: per-tenant max points enforced at upsert.

## 5.4 Supabase

- **Edge fn `on-document-upload`**: signed-URL → kicks n8n webhook
- **DB triggers**: `tenants_after_insert` → call `tenant-provisioner` (creates Qdrant collection, default roles, storage bucket prefix)
- **RLS**: every multi-tenant table has policy `tenant_id = auth.jwt() ->> 'tenant_id'`
- **Async dispatch**: `pg_net` extension to POST job to backend `/internal/jobs`

---

# 6. SKILLS / TOOLS

Registered in `tools/registry.py`. Each tool: pydantic input/output, JSON-schema export for LLM tool calling.

### `search_shared_kb`
- **Agent**: Retrieval, IFRS Compare, Report
- **Input**: `{query:str, lang:"vi"|"en"|"both", standards?:list[str], k:int=20, filters?:dict}`
- **Output**: `{chunks:[{id,doc_id,text,score,metadata,citation_key}]}`
- **Validation**: k∈[1,50]; query nonempty
- **Failures**: `QdrantUnavailable` (503), `EmbedderTimeout` (fallback BM25)

### `search_tenant_kb`
- **Agent**: Retrieval, GL Mapping, Report
- **Input**: `{tenant_id:UUID, query, scope:"gl"|"policy"|"all", k:int=10}`
- **Output**: same shape; results forced filtered `payload.tenant_id==tenant_id`
- **Validation**: caller `tenant_id` must equal request ctx; else `TenantMismatch`

### `parse_gl_file`
- **Agent**: GL Mapping (pre-step, called by ingestion worker)
- **Input**: `{gcs_uri, mime, expected_columns?:list[str]}`
- **Output**: `{rows:[{account_code,account_name,debit,credit,balance,period,raw}], schema_hash, row_count, errors[]}`
- **Validation**: ≤500MB, mime∈{xlsx,csv,xls}
- **Failures**: malformed → `errors[]` populated, partial OK

### `map_account_to_standard`
- **Agent**: GL Mapping
- **Input**: `{src_account:{code,name,desc?}, target:"VAS"|"IFRS", coa_ref?}`
- **Output**: `{candidates:[{target_code, target_name, confidence, rationale, citation}]}`
- **Validation**: ≥1 candidate or empty list w/ reason
- **Failures**: model timeout → retry 2× → mark `unmapped`

### `generate_adjustment_entry`
- **Agent**: Adjustment
- **Input**: `{mapping, period, rule_ids:list[str], gl_balance:Decimal}`
- **Output**: `{entries:[{dr,cr,amount,narration,rule_ref}], balanced:bool}`
- **Validation**: `sum(dr)==sum(cr)`; reject if false
- **Failures**: `UnbalancedJE`, `MissingRule`

### `export_comparison_report`
- **Agent**: Report
- **Input**: `{report_id, format:"pdf"|"xlsx"|"docx"}`
- **Output**: `{gcs_uri, signed_url, expires_at}`
- **Validation**: report status==`ready`
- **Failures**: render timeout → return partial w/ flag

---

# 7. MCP INTEGRATION

Reuse where exists, build where gap.

| Server | Build/Reuse | Purpose | Used by |
|---|---|---|---|
| filesystem | reuse `@modelcontextprotocol/server-filesystem` | Local prompt edit, eval set browse | Dev agents only |
| supabase-mcp | reuse `supabase-community/supabase-mcp` | Schema introspection, RLS audits, ticket→data lookup | Internal admin agents |
| qdrant-mcp | **build** (`mcp/servers/qdrant_mcp`) | Collection inspect, payload sample, similarity probe for QA agents | Eval + retrieval debug |
| n8n-mcp | **build** | Trigger workflow, get exec status, replay DLQ | Ops agents |

`mcp/mcp_servers.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./prompts", "./tests/eval"]
    },
    "supabase": {
      "command": "uvx",
      "args": ["supabase-mcp"],
      "env": { "SUPABASE_URL": "${SUPABASE_URL}", "SUPABASE_SERVICE_ROLE_KEY": "${SUPABASE_SERVICE_ROLE_KEY}" }
    },
    "qdrant": {
      "command": "python",
      "args": ["-m", "mcp.servers.qdrant_mcp"],
      "env": { "QDRANT_URL": "${QDRANT_URL}", "QDRANT_API_KEY": "${QDRANT_API_KEY}" }
    },
    "n8n": {
      "command": "node",
      "args": ["mcp/servers/n8n_mcp/dist/index.js"],
      "env": { "N8N_BASE_URL": "${N8N_URL}", "N8N_API_KEY": "${N8N_API_KEY}" }
    }
  }
}
```

**Auth**: short-lived service tokens via Secret Manager; rotated weekly. **Boundaries**: MCP for dev/ops only — production runtime never depends on MCP. No tenant data through MCP without explicit `tenant_id` header check in server wrapper.

---

# 8. DATA MODELS

## 8.1 Supabase Postgres

```sql
-- 0001_init.sql
create table tenants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,
  plan text not null default 'free',
  status text not null default 'active',
  qdrant_collection text not null,
  storage_prefix text not null,
  created_at timestamptz default now(),
  offboarded_at timestamptz
);

create table users (
  id uuid primary key references auth.users(id),
  tenant_id uuid not null references tenants(id) on delete cascade,
  email text not null,
  role text not null check (role in ('owner','admin','accountant','auditor','viewer')),
  created_at timestamptz default now()
);
create index on users(tenant_id);

create table documents (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,  -- null = shared KB
  scope text not null check (scope in ('shared','tenant')),
  source text not null,             -- 'vas_circular','ifrs_std','policy','audit_note'
  title text not null,
  lang text not null check (lang in ('vi','en','bi')),
  storage_uri text not null,
  checksum text not null,
  status text not null default 'pending',  -- pending|parsing|embedding|ready|failed
  metadata jsonb not null default '{}',
  created_at timestamptz default now(),
  ingested_at timestamptz
);
create index on documents(tenant_id, scope);
create index on documents using gin(metadata);

create table kb_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade,
  tenant_id uuid,
  scope text not null,
  chunk_index int not null,
  text text not null,
  token_count int,
  lang text,
  embedding_model text not null,    -- e.g. 'bge-m3@v1.5'
  qdrant_point_id uuid not null,
  metadata jsonb not null default '{}',
  created_at timestamptz default now()
);
create index on kb_chunks(document_id);
create index on kb_chunks(tenant_id, scope);

create table gl_uploads (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  uploaded_by uuid references users(id),
  storage_uri text not null,
  filename text,
  period_start date, period_end date,
  row_count int, schema_hash text,
  status text default 'pending',
  error jsonb,
  created_at timestamptz default now()
) partition by range (created_at);

create table mappings (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  gl_upload_id uuid references gl_uploads(id) on delete cascade,
  src_account_code text, src_account_name text,
  target_standard text check (target_standard in ('VAS','IFRS')),
  target_account_code text, target_account_name text,
  confidence numeric(4,3),
  rationale text,
  citation jsonb,
  status text default 'proposed',  -- proposed|confirmed|rejected
  reviewed_by uuid, reviewed_at timestamptz,
  created_at timestamptz default now()
);
create index on mappings(tenant_id, gl_upload_id, status);

create table adjustment_entries (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  gl_upload_id uuid references gl_uploads(id),
  period date not null,
  dr_account text not null, cr_account text not null,
  amount numeric(20,4) not null,
  narration text,
  rule_ref text, citation jsonb,
  status text default 'draft',
  created_at timestamptz default now()
);
create index on adjustment_entries(tenant_id, period);

create table query_logs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid, user_id uuid,
  request_id text, intent text, lang text,
  prompt_name text, prompt_version text,
  model text, tokens_in int, tokens_out int,
  latency_ms int, cost_usd numeric(10,6),
  retrieval_k int, rerank_top numeric(4,3),
  citations_resolved bool,
  created_at timestamptz default now()
) partition by range (created_at);

create table reports (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  kind text, period_start date, period_end date,
  status text default 'pending',
  storage_uri text, sections jsonb,
  created_by uuid, created_at timestamptz default now()
);

create table audit_logs (
  id bigserial primary key,
  tenant_id uuid, user_id uuid,
  action text not null, resource_type text, resource_id text,
  diff jsonb, request_id text, ip inet, ua text,
  created_at timestamptz default now()
) partition by range (created_at);
```

**Partitioning**: `query_logs`, `audit_logs`, `gl_uploads` — monthly via `pg_partman`.

**Indexes**: btree on FK + `(tenant_id, created_at desc)`; GIN on jsonb metadata.

**RLS** (`0002_rls_policies.sql`):

```sql
alter table documents enable row level security;
create policy doc_tenant_iso on documents
  using (scope='shared' or tenant_id = (auth.jwt()->>'tenant_id')::uuid)
  with check (tenant_id = (auth.jwt()->>'tenant_id')::uuid);
-- repeat per tenant table
```

## 8.2 Qdrant

**Collections**

| Name | Purpose | Vector dim | Distance |
|---|---|---|---|
| `kb_shared_vas` | VAS circulars | 1024 | Cosine |
| `kb_shared_ifrs` | IFRS standards | 1024 | Cosine |
| `kb_shared_guidance` | General accounting guidance | 1024 | Cosine |
| `tenant_{tenant_id}` | per-tenant private | 1024 | Cosine |

**Payload schema**

```json
{
  "doc_id": "uuid",
  "chunk_id": "uuid",
  "tenant_id": "uuid|null",
  "scope": "shared|tenant",
  "kind": "vas|ifrs|policy|gl_note|audit",
  "standard_code": "VAS-15|IFRS-15|...",
  "section": "1.2.3",
  "lang": "vi|en|bi",
  "period": "2026-Q1|null",
  "title": "...",
  "text_preview": "first 200 chars",
  "source_uri": "gs://...",
  "checksum": "sha256",
  "embedding_model": "bge-m3@v1.5",
  "ingested_at": "iso8601"
}
```

**Indexes**: payload index on `doc_id`, `tenant_id`, `kind`, `standard_code`, `lang`, `period`. Sparse vector field for hybrid (`text` BM25-like via Qdrant sparse).

**Filtering**: tenant retrieval always `must:[{key:"tenant_id", match:{value:tid}}]`. Shared retrieval `must_not:[{key:"tenant_id", match:{except:[null]}}]`.

---

# 9. API CONTRACTS

FastAPI router tree: `app/api/v1/router.py` mounts `chat, kb, gl, mapping, adjustments, reports, documents, admin`.

```
POST   /v1/chat/stream            SSE   body: ChatRequest
POST   /v1/chat/messages                body: {conv_id, content}
GET    /v1/chat/conversations           ?cursor=
GET    /v1/chat/conversations/{id}

GET    /v1/kb/search                    ?q=&scope=&lang=&k=
GET    /v1/kb/standards                 list available
GET    /v1/kb/standards/{code}

POST   /v1/documents                    multipart upload
GET    /v1/documents                    paginated
DELETE /v1/documents/{id}

POST   /v1/gl/uploads                   multipart (xlsx/csv)
GET    /v1/gl/uploads/{id}
GET    /v1/gl/uploads/{id}/rows         cursor pagination
POST   /v1/gl/uploads/{id}/process

GET    /v1/mappings                     ?gl_upload_id=&status=
PATCH  /v1/mappings/{id}                {status, target_account_code}
POST   /v1/mappings/bulk-confirm

POST   /v1/adjustments/generate         {gl_upload_id, period, rule_ids[]}
GET    /v1/adjustments                  ?period=&status=
PATCH  /v1/adjustments/{id}

POST   /v1/reports/generate             {kind, period, sections[]}
GET    /v1/reports/{id}
GET    /v1/reports/{id}/download

GET    /v1/admin/users
POST   /v1/admin/users/invite
GET    /v1/admin/audit                  cursor + filters
GET    /v1/admin/usage                  ?from=&to=

GET    /healthz   /readyz   /metrics
```

**Auth**: `Authorization: Bearer <supabase_jwt>` on all `/v1/*`. `X-Tenant-Id` optional (validated against JWT claim).

**Pagination**: cursor-based — `?cursor=<opaque>&limit=50`. Response `{items, next_cursor}`.

**Streaming**: SSE on `/v1/chat/stream`. Events: `token`, `citation`, `tool_call`, `final`, `error`.

**Sample schemas**

```python
# schemas/chat.py
class ChatRequest(BaseModel):
    conversation_id: UUID | None = None
    content: str
    lang: Literal["vi","en","auto"] = "auto"
    intent_hint: Literal["qa","compare","mapping","report"] | None = None
    reasoning: Literal["fast","balanced","deep"] = "balanced"
    scope: Literal["shared","tenant","both"] = "both"

class ChatTokenEvent(BaseModel):
    type: Literal["token"]
    delta: str

class ChatCitationEvent(BaseModel):
    type: Literal["citation"]
    key: str  # "C1"
    doc_id: UUID
    chunk_id: UUID
    snippet: str
    standard_code: str | None
```

OpenAPI auto-generated via FastAPI; published at `/openapi.json`.

---

# 10. RAG DESIGN

## Chunking
- `rag/chunker.py` — recursive splitter, target 800 tokens, overlap 120
- Section-aware: parser emits `{section_path, heading, lang}`; chunker preserves section boundaries
- Tables: serialize as Markdown, kept whole if ≤1500 tokens
- Bilingual VAS docs: emit `lang=bi` w/ aligned VI+EN spans for cross-lingual hit

## Embedding (`rag/embedder.py`)
- `bge-m3` (BAAI) — chosen because: (1) native multilingual incl. Vietnamese, (2) supports dense+sparse+ColBERT in one model, (3) 8k context fits long sections
- Served via TEI (`text-embeddings-inference`) on CPU/GPU node
- Batch=64, async via `httpx.AsyncClient`
- Outputs persisted dense (1024) + sparse (BM25-like) for hybrid

## Retrieval pipeline (`rag/retriever.py`)

```
query
 → (optional) query rewrite (Qwen14B, multilingual normalize)
 → embed(dense) + sparse_encode
 → Qdrant search dense (k=40) ∥ sparse (k=40)
 → RRF fusion → top 30
 → bge-reranker-v2-m3 (cross-encoder, k=30 → 8)
 → filter: score >= 0.35 (tunable)
 → return chunks + scores
```

## Hybrid filter logic

```python
must = [{"key":"lang","match":{"any":[lang,"bi"]}}]
if scope == "shared":
    must.append({"key":"scope","match":{"value":"shared"}})
elif scope == "tenant":
    must.append({"key":"tenant_id","match":{"value":str(tid)}})
else:
    should = [
      {"key":"scope","match":{"value":"shared"}},
      {"key":"tenant_id","match":{"value":str(tid)}}
    ]
```

## Reranker thresholds
- Default `min_score=0.35`
- If <3 chunks pass → relax to 0.20 + log `low_recall=true`
- If 0 chunks → fallback to BM25-only top-5, mark `degraded_retrieval=true`

## Citation generation
- Each surviving chunk gets `Cn` key
- System prompt instructs `[Cn]` inline w/ every factual claim
- Post-LLM: `agents/citation_validator.py` regex-extracts, verifies all keys exist in `citation_map`
- Unresolved → re-prompt once; still fail → strip claim and append warning

## Tenant-aware filtering
- Enforced server-side in `rag/retriever.py` — never trust LLM tool args
- `assert ctx.tenant_id == requested_tenant_id`
- Test: adversarial RLS suite in `tests/integration/test_tenant_isolation.py`

## Fallback strategy

| Failure | Fallback |
|---|---|
| Reranker timeout | Use dense scores only |
| Embedder down | Cached query embedding LRU; else BM25 sparse only |
| Qdrant down | Read-replica → if also down, return cached recent answers w/ stale flag |

---

# 11. FRONTEND ARCHITECTURE

## App Router structure

```
app/
  (auth)/              public, no tenant ctx
  (app)/               protected, layout injects tenant + nav
  api/                 thin proxies (auth cookie → Bearer to FastAPI)
```

## Server vs client

| Concern | Type |
|---|---|
| Layouts, page shells, KB lists, reports list | Server (RSC) |
| Chat stream, GL upload, mapping table, settings forms | Client |
| Auth callbacks, file upload, SSE proxy | Route handlers |

## Auth

- `lib/supabase/middleware.ts` — refresh session on every req
- `middleware.ts` — gate `(app)/*`; redirect to login if no session; inject `x-tenant-id` from JWT into rewrites

## Streaming chat UI (`components/chat/ChatStream.tsx`)

```tsx
const { messages, send, status } = useChatStream({ conversationId });
// Uses fetch + ReadableStream; appends tokens; collects citations into sidebar
```

`lib/hooks/useStream.ts` — typed SSE consumer w/ reconnect, EventSource polyfill via fetch.

## Upload UX
- `react-dropzone` + chunked PUT to Supabase Storage signed URL
- Progress via `XMLHttpRequest` + Realtime subscription on `gl_uploads.status`

## RBAC
- Server: route-level guard in `(app)/layout.tsx` reads role from session, blocks unauthorized routes
- Client: `<Can role="admin">…</Can>` component

## State management
- Server state: TanStack Query (`@tanstack/react-query`)
- Client state: Zustand for chat draft + upload progress
- No Redux

## Caching
- RSC: `revalidateTag('documents:'+tenantId)` after mutations
- React Query: `staleTime: 30s` defaults; longer for `kb/standards` (1h)
- SSE chat: optimistic user message append before server ack

## Key pages

| Path | Purpose |
|---|---|
| `/chat` | New conversation |
| `/chat/[id]` | Resume, streaming view, citation sidebar |
| `/compare` | VAS↔IFRS topic compare, diff view |
| `/gl/upload` | Dropzone + recent uploads |
| `/gl/mappings` | Review queue, bulk confirm |
| `/gl/adjustments` | JE viewer w/ citations |
| `/documents` | Tenant doc lib + ingest status |
| `/reports` | Generate + download |
| `/settings/audit` | Audit log viewer |

---

# 12. DEPLOYMENT ARCHITECTURE

## Topology (GCP `asia-southeast1`)

```
                    ┌──────────────────┐
                    │  Cloud Load Bal. │
                    └────────┬─────────┘
                             │
                ┌────────────┴───────────┐
                │  GKE Autopilot cluster │
                ├────────────────────────┤
   namespace=app│ frontend (Next.js)     │  HPA cpu/req
                │ backend (FastAPI)      │  HPA cpu+rps
                │ celery-worker          │  HPA queue depth
                │ n8n                    │
   namespace=ai │ ollama (qwen14b)       │  GPU node pool (L4 ×2)
                │ tei (bge-m3+reranker)  │  GPU node pool (L4 ×1)
   namespace=db │ qdrant (StatefulSet 3) │  pd-ssd 500GB ea
                │ redis (HA)             │
                └────────────────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
   Supabase             GCS (docs/exports)    Secret Manager
   (managed)            CMEK encryption
```

GPU nodes: `g2-standard-12` (L4, 24GB VRAM) — Qwen14B Q4_K_M fits w/ 8k ctx; second L4 for embed+rerank.

## Ollama deployment

- StatefulSet, pinned to GPU node pool (`nodeSelector: cloud.google.com/gke-accelerator=nvidia-l4`)
- Models pre-pulled via init container
- Single replica per GPU; concurrency via Ollama `OLLAMA_NUM_PARALLEL=4`
- Behind ClusterIP only

## Qdrant

- 3-node StatefulSet, replication factor 2, write consistency=majority
- `pd-ssd` 500GB, snapshot to GCS daily
- Helm chart `qdrant/qdrant`

## Networking / VPC

- Single VPC, 3 subnets: `app`, `data`, `gpu`
- Private GKE cluster, master authorized networks = office + CI/CD
- NAT for egress (OpenAI/Anthropic)
- VPC peering w/ Supabase IP allowlist
- NetworkPolicy: backend → qdrant/ollama only on internal ports

## Object storage

- Buckets: `vifb-docs-{env}`, `vifb-exports-{env}`, `vifb-archive-{env}` (cold)
- CMEK via Cloud KMS keyring `vifb-{env}`
- Signed URLs 15min

## CI/CD

- `.github/workflows/ci-backend.yml` — ruff, mypy, pytest, docker build, push to Artifact Registry
- `ci-frontend.yml` — biome, tsc, vitest, playwright smoke, build, push
- `deploy-prod.yml` — manual approval → `helmfile apply` → run alembic upgrade → smoke tests
- Image tag = git sha; promotion staging→prod via tag re-tag

## Environments
- `dev` (docker-compose local), `staging` (small GKE, no GPU — uses OpenAI for everything), `prod` (full)
- Per-env Supabase project + Qdrant cluster + GCS buckets

## Autoscaling
- Backend: HPA on RPS (target 50/pod) and CPU 70%
- Workers: KEDA on Redis queue length
- Ollama: not autoscaled (cost); vertical scale GPU type if needed
- Qdrant: vertical, manual

---

# 13. OBSERVABILITY

## Stack
- Logs: structlog → stdout → Cloud Logging
- Metrics: prometheus-client → Cloud Managed Prometheus → Grafana Cloud
- Traces: OpenTelemetry → Cloud Trace
- LLM traces: Langfuse (self-hosted) — captures prompts, completions, tokens, cost, eval scores

## Standard fields (every log)
`request_id, tenant_id, user_id, route, status, latency_ms, prompt_name, prompt_version, model, tokens_in, tokens_out, cost_usd, retrieval_k, rerank_top, citations_resolved, intent`

## Key metrics

| Metric | Type | Labels |
|---|---|---|
| `http_request_duration_seconds` | hist | route, status, tenant_plan |
| `llm_tokens_total` | counter | model, direction, tenant_id |
| `llm_cost_usd_total` | counter | model, tenant_id |
| `rag_retrieval_recall` | gauge | scope, lang |
| `rag_rerank_score_p50/p95` | gauge | scope |
| `citations_unresolved_total` | counter | agent |
| `qdrant_query_duration_seconds` | hist | collection |
| `gl_mapping_confidence` | hist | tenant_id |

## Hallucination monitoring
- Async job samples 5% of QA responses → re-runs Citation Validator + LLM-judge (Qwen) → flags `groundedness<0.7`
- Daily report to Slack `#ai-quality`

## Alerts
- p95 chat latency > 8s for 5 min
- LLM error rate > 5% (any provider)
- Qdrant 5xx > 1%
- Tenant cost > 2× 7-day avg
- Citation unresolved > 2% / hour
- DLQ depth > 20

## Dashboards
1. **Service Health** — RPS, error rate, p50/p95/p99 per route
2. **LLM Cost** — $/tenant/day, $/model, escalation rate
3. **RAG Quality** — recall@k, rerank score dist, citation success
4. **Ingestion** — docs queued/processed, embedding throughput, failures
5. **Tenant Usage** — top tenants by tokens/queries/uploads
6. **Audit** — mutating ops/min, RBAC denials, RLS violations attempted

---

# 14. SECURITY AND MULTI-TENANCY

## Isolation strategy
- **DB**: every tenant table has `tenant_id`, RLS enforced w/ JWT claim, app uses Postgres role w/o `BYPASSRLS`
- **Storage**: GCS prefixed `tenants/{tenant_id}/...`; signed URLs scoped to prefix
- **Vector**: separate Qdrant collection per tenant + payload filter belt-and-suspenders
- **Compute**: shared multi-tenant pods; tenant_id always in request context, validated at every layer

## RLS sample (mappings)

```sql
alter table mappings enable row level security;
create policy mappings_select on mappings for select
  using (tenant_id = (auth.jwt()->>'tenant_id')::uuid);
create policy mappings_mod on mappings for all
  using (tenant_id = (auth.jwt()->>'tenant_id')::uuid)
  with check (tenant_id = (auth.jwt()->>'tenant_id')::uuid);
```

## API-layer validation
- `TenantResolverMiddleware` rejects mismatch between JWT claim and `X-Tenant-Id`
- Every repo method requires `tenant_id`; lint rule blocks raw queries without it
- Pydantic models for tool inputs reject cross-tenant ids

## Qdrant filtering enforcement
- Wrapper `QdrantClient.search_tenant(tid, ...)` — only entrypoint; injects filter
- Test: monkeypatched call w/ wrong tid must return 0 results from real collection

## Encryption
- At rest: GCS CMEK, Postgres (Supabase managed), pd-ssd CMEK
- In transit: TLS 1.3 everywhere, mTLS between backend↔Qdrant↔Ollama
- App-level: PII columns (e.g., `users.email`) — pgcrypto for sensitive notes

## Secrets
- GCP Secret Manager; injected via Workload Identity (no static SA keys)
- LLM API keys rotated 90 days, alarm at 80 days
- `.env.example` only — never commit real

## Signup flow
1. Supabase email/password (or SSO future)
2. Edge fn `tenant-provisioner`: create `tenants` row, create Qdrant collection, create GCS prefix, seed default role
3. First user = `owner`
4. Welcome email w/ verification

## Tenant lifecycle

| Phase | Action |
|---|---|
| Provision | Supabase trigger → backend `/internal/tenants/provision` |
| Active | Quota tracking, usage metering |
| Suspend | Read-only flag in tenant; middleware blocks writes |
| Offboard | Export bundle to GCS archive (encrypted), 30-day retention, drop Qdrant collection, anonymize logs after 90d |

---

# 15. AI EVALUATION

## Datasets (`backend/app/eval/datasets/`)

| Set | Items | Purpose |
|---|---|---|
| `vas_qa_vi.jsonl` | 300 | VI Q→answer+citations |
| `ifrs_qa_en.jsonl` | 300 | EN Q→answer+citations |
| `vas_ifrs_compare.jsonl` | 100 | topic→difference structure |
| `gl_mapping_bench.csv` | 2000 rows | Vietnamese CoA → IFRS mapping gold |
| `adjustment_cases.jsonl` | 80 | Scenario→expected JE |
| `hallucination_probes.jsonl` | 150 | Adversarial OOD questions |

## Pipelines

| Eval | Method | Threshold |
|---|---|---|
| Retrieval recall@10 | Hit if gold doc_id in top-10 | ≥0.85 shared, ≥0.80 tenant |
| Rerank nDCG@5 | vs gold ranking | ≥0.75 |
| Answer faithfulness | RAGAS faithfulness w/ Claude judge | ≥0.85 |
| Citation resolvability | All `[Cn]` map to chunk | 100% |
| Hallucination rate | LLM judge + manual sample | ≤3% |
| Mapping top-1 accuracy | exact code match | ≥0.92 |
| Mapping top-3 accuracy | gold in top-3 candidates | ≥0.98 |
| JE balance check | sum(dr)==sum(cr) | 100% |
| Latency | p95 chat | ≤8s |

## Automated pipeline
- GH Action `eval-nightly.yml` runs full suite vs staging
- Outputs report → posts to Slack + appends to `eval_history.jsonl`
- Regression gate on PR: `eval-pr.yml` runs subset (50 items each) — blocks merge if recall drops >2pp

## Human review
- 5% sample of prod QA flagged `low_confidence` → admin queue UI
- SME (accountant) labels: `correct | partial | wrong | hallucination`
- Labels feed back as future eval set

## Regression
- Prompt version bump → must beat current on full eval before promote
- Model swap → A/B 5% traffic for 48h, compare faithfulness + cost

---

# 16. OPEN QUESTIONS

| # | Question | Owner | Blocker level |
|---|---|---|---|
| 1 | IFRS Foundation licensing — are full standard texts redistributable in our KB or must we use summaries/links only? | Legal | **HIGH** — affects shared KB scope |
| 2 | VAS circular versioning — do we snapshot circulars at upload or auto-track MoF amendments? | Product | MED |
| 3 | Data retention — how long for `query_logs`, `audit_logs`, `gl_uploads` raw files? Vietnam PDPL requirements? | Legal+Compliance | HIGH |
| 4 | Export controls — do PDF/XLSX exports need watermarking + tenant fingerprinting? | Product | MED |
| 5 | Enterprise SSO — SAML, OIDC, or Microsoft Entra priority for Phase 3 vs 4? | Sales | MED |
| 6 | Pricing model — per-seat, per-tenant, per-token, or hybrid? Affects metering granularity | Product | HIGH |
| 7 | Data residency — must tenant data stay in VN? `asia-southeast1` is Singapore. Need VN region fallback? | Compliance | HIGH |
| 8 | Auditor read-only access — separate role with cross-tenant view by invitation? | Product | MED |
| 9 | LLM provider redundancy — accept OpenAI-only outage tolerance or require Anthropic fallback for everything? | Eng leadership | MED |
| 10 | Qwen14B fine-tuning on VAS corpus — in scope Phase 2 or defer? GPU cost vs accuracy gain | ML lead | MED |
| 11 | GL file PII — payroll accounts may contain employee data; mask before LLM? | Compliance | HIGH |
| 12 | Adjustment entries — advisory only or auto-postable to client ERP (Misa, Fast)? Liability implications | Legal+Product | HIGH |
| 13 | Free tier limits — token/doc caps to prevent abuse | Product | LOW |
| 14 | Disaster recovery RPO/RTO targets | Eng leadership | MED |
| 15 | SOC2 / ISO27001 timeline — affects audit logging detail + access controls now | Compliance | MED |

---

*Generated: 2026-05-11. Resolve Open Questions #1, #3, #7, #11, #12 before Phase 1 sprint lock.*
