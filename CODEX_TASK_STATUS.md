# Codex Task Status Report

> Generated: 2026-08-05 18:30 | Branch: `main` (ahead of origin by 32 commits)

## Summary

Codex completed **21 commits** (from `ee8f733` to `bc9da9a`) roughly 2–4 hours ago, covering frontend, backend, ingestion, infra, auth hardening, and docs rewriting. There are also **23 unstaged file changes** that were never committed. The task is **incomplete** — there is a critical runtime bug in the retriever.

---

## 1. Completed Commits (21 most recent by Codex)

```
bc9da9a fix(ingestion): normalize extracted document text
2e17143 feat(infra): make production deployment executable
6de3486 build(backend): lock production dependencies
1cf2085 fix(frontend): upgrade patched Next runtime
be0bd13 fix(auth): enforce tenant isolation
c2d8b63 fix(mcp): secure service boundaries
c584f37 fix(ingestion): preserve live ontology
9e0f741 fix(ingestion): route host service endpoints
f6cd276 fix(ingestion): stabilize metadata builders
925ac37 fix(ingestion): harden pipeline entrypoints
a405fd4 fix(ingestion): fail on corrupt source files
0ee8a63 fix(ingestion): make batch writes deterministic
90ee991 chore(frontend): ignore build artifacts
8d5f1a8 fix(frontend): remove dead-end UI
f590287 fix(frontend): remove placeholder records
384d575 fix(frontend): remove misleading controls
1a27c02 fix(frontend): stabilize chat data flow
991a200 fix(frontend): harden backend proxies
28d1428 fix(frontend): secure auth session flow
3348d81 fix(backend): harden request processing
ee8f733 prompt: update RetrievalAgent system prompt
```

---

## 2. Uncommitted Changes (Unstaged)

### Modified (23 files)

| File | Change Type |
|------|-------------|
| `.github/workflows/ci-frontend.yml` | Minor CI fix |
| `.github/workflows/deploy-prod.yml` | Deploy pipeline update |
| `CLAUDE.md` | Doc update |
| `HOW_TO_RUN.md` | **Near-total rewrite** (263 lines → 128 lines) |
| `Makefile` | Updated targets |
| `README.md` | **Heavily trimmed** (572 lines removed) |
| `VAS_IFRS_ARCHITECTURE.md` | Minor fix |
| `apps/backend/.env.example` | Added new env vars |
| `apps/backend/tests/unit/ingestion/test_batch_embed_pipeline.py` | **+23 lines**: 2 new tests for HTML parser & text normalizer |
| `apps/backend/tests/unit/ingestion/test_ingestion_scripts.py` | **+31 lines**: new test for HTML document discovery |
| `apps/frontend/src/app/layout.tsx` | +1 line |
| `docs/ARCHITECTURE.md` | Rewritten (247 lines changed) |
| `docs/RAG_DESIGN.md` | **Heavily trimmed** (534 lines removed) |
| `docs/RUNBOOK.md` | **+130 lines**: added incident triage section |
| `infra/docker/docker-compose.dev.yml` | Qdrant uncommented, versions pinned, redis volume added |
| `infra/docker/docker-compose.ollama.yml` | Removed `version: '3.8'`, pinned ollama tag |
| `infra/docker/docker-compose.qdrant.yml` | Pinned `qdrant:v1.18.2`, added gRPC port 6334 |
| `infra/k8s/base/frontend-deploy.yaml` | Removed frontend secretRef |
| `infra/k8s/base/network-policies.yaml` | Added port 5432 egress |
| `ingestion/pipelines/parsers/unstructured_runner.py` | **+32 lines**: HTML parser + normalize pipeline |
| `skills/.../run_ingest.sh` | Added `.html`/`.htm` to file discovery |

### Deleted (2 files)

- `ingestion/raw/shared/ifrs/standards/IFRS_01_First_time_Adoption_of_IFRS.pdf`
- `ingestion/raw/shared/ifrs/standards/IFRS_02_Share_based_Payment.pdf`

### Untracked / New (12+ items)

- `.github/workflows/security.yml` — new CI workflow
- `apps/backend/storage/` — new directory
- 8 new IFRS PDF files (kebab-case naming convention)
- 1 new VAS PDF file
- `scratch/` — ad-hoc test scripts

---

## 3. 🚨 Critical Bug: `retriever.py` is broken

### Problem

File `apps/backend/app/rag/retriever.py` (line 109) calls an API that **does not exist** in `qdrant-client` v1.19.0:

```python
# Line 109 — BROKEN
result = await client.http.search_api.search_points(
    collection_name=collection,
    search_request=http_models.SearchRequest(
        vector=vec,
        filter=flt,
        limit=DENSE_K,
        with_payload=True,
    ),
)
```

### Runtime Error

```
AttributeError: 'AsyncSearchApi' object has no attribute 'search_points'
```

### Root Cause

Commit `9f2be10` (7 weeks ago) switched from `query_points` to `search_points` for Qdrant server compatibility. However, in `qdrant-client` v1.19.0 the `search_points` method no longer exists on `client.http.search_api`. The correct API is the high-level `client.query_points()` method.

### Suggested Fix

Use the high-level `AsyncQdrantClient.query_points()` method (confirmed available in v1.19.0):

```python
# FIX: use high-level API
result = await client.query_points(
    collection_name=collection,
    query=vec,
    query_filter=flt,
    limit=DENSE_K,
    with_payload=True,
)
hits = result.points
```

**Note**: `query_points` returns a `QueryResponse` with `.points` (not `.result`). Each point still has `.payload` and `.score` as before.

---

## 4. Overall Assessment

| Area | Status | Notes |
|------|--------|-------|
| Frontend hardening | ✅ Committed | 7 related commits |
| Backend hardening | ✅ Committed | 1 commit |
| Auth / tenant isolation | ✅ Committed | 1 commit |
| Ingestion pipeline | ✅ Committed + ⚠️ Unstaged | Normalize/harden committed; HTML parser unstaged |
| Infra (Docker/K8s) | ⚠️ Unstaged | Version pinning, qdrant uncomment, redis volume |
| Docs rewrite | ⚠️ Unstaged | HOW_TO_RUN, README, ARCHITECTURE, RAG_DESIGN, RUNBOOK |
| New tests | ⚠️ Unstaged | 3 new tests for HTML/normalize |
| **Retriever (Qdrant search)** | **🔴 BROKEN** | `search_points` does not exist in qdrant-client v1.19 |
| File rename (IFRS PDFs) | ⚠️ Unstaged | 2 old PDFs deleted, 8 new PDFs added |

---

## 5. Recommended Actions

1. **Fix `retriever.py`** — Replace `client.http.search_api.search_points()` with `client.query_points()` (see section 3)
2. **Review unstaged changes** — Decide whether to commit or revert each group
3. **Run tests** — `cd apps/backend && uv run pytest tests/unit/`
4. **Verify retrieval** — `cd apps/backend && uv run python ../../scratch/test_retrieval_chunks.py`
5. **Git push** — After verification, push 32 commits to origin

---

## 6. Technical Details

- **qdrant-client version**: `1.19.0`
- **Python**: `3.13.13` (via uv)
- **Branch**: `main` (ahead of origin by 32 commits)
- **Stash**: empty
- **Qdrant server target**: `v1.18.2` (docker-compose)
