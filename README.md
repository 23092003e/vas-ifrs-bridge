# VAS-IFRS Bridge

[![Backend CI](https://github.com/23092003e/vas-ifrs-bridge/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/23092003e/vas-ifrs-bridge/actions/workflows/ci-backend.yml)
[![Frontend CI](https://github.com/23092003e/vas-ifrs-bridge/actions/workflows/ci-frontend.yml/badge.svg)](https://github.com/23092003e/vas-ifrs-bridge/actions/workflows/ci-frontend.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg)](apps/backend/)
[![Next.js](https://img.shields.io/badge/Next.js-15.5-black.svg)](apps/frontend/)

VAS-IFRS Bridge is a multi-tenant knowledge application for Vietnamese Accounting Standards (VAS), IFRS comparison, and assisted GL transformation. It is a monorepo with a FastAPI backend, Next.js frontend, PostgreSQL, Qdrant, Redis, and Ollama.

## What is implemented

- Streaming chat through the Next.js SSE proxy and FastAPI orchestrator.
- Keyword-based intent routing to retrieval, comparison, GL mapping, and adjustment agents.
- Hybrid dense/sparse retrieval from Qdrant, optional TEI reranking, and citation validation.
- Local 1024-dimensional `bge-m3` embeddings through Ollama.
- PDF, DOCX, XLSX, HTML, Markdown, and text ingestion with normalization and chunking.
- Supabase JWT authentication, tenant resolution, RBAC, audit middleware, and database RLS migrations.
- Reproducible backend/frontend containers, local Compose, Kustomize overlays, and Terraform for GCP/GKE.

The specialized agents can generate mapping and adjustment drafts in chat. The standalone KB, GL, mapping, adjustment, report, and admin REST workflows still return HTTP 501 where persistence and approval contracts have not been implemented. They must not be treated as production-complete accounting automation.

## Request flow

```text
Browser
  -> Next.js 15 App Router
  -> /api/chat/stream SSE proxy
  -> FastAPI /v1/chat/stream
  -> tracing/auth/tenant/RBAC/usage/audit middleware
  -> keyword intent router
  -> one specialized agent
  -> Ollama bge-m3 -> Qdrant dense + sparse retrieval
  -> optional TEI reranker -> top 8 chunks
  -> LLM provider -> citation validation -> SSE response
```

## Ingestion flow

```text
Raw documents
  -> format parser
  -> text normalizer
  -> heading-aware chunks (800 target tokens, 120 overlap)
  -> Ollama bge-m3 embeddings
  -> kb_shared_vas, kb_shared_ifrs, or tenant_<tenant_id> in Qdrant
```

## Quick start

Requirements: Docker Desktop with Compose. For host development, also install Python 3.11+, `uv`, Node.js 22+, and pnpm 11.

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.local.example apps/frontend/.env.local

# Set DEV_AUTH_BYPASS=true for local-only development, then:
docker compose -f infra/docker/docker-compose.dev.yml up --build
docker compose -f infra/docker/docker-compose.dev.yml exec backend alembic upgrade head
docker compose -f infra/docker/docker-compose.dev.yml exec ollama ollama pull bge-m3
docker compose -f infra/docker/docker-compose.dev.yml exec ollama ollama pull qwen2.5:14b-instruct
```

Open:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/healthz
- API docs: http://localhost:8000/docs
- Qdrant dashboard: http://localhost:6333/dashboard

The local Compose stack includes PostgreSQL, Redis, Qdrant, Ollama, backend, and frontend. See [HOW_TO_RUN.md](HOW_TO_RUN.md) for host development and troubleshooting.

## Development

```bash
# Backend
cd apps/backend
uv sync --frozen --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000

# Frontend
cd apps/frontend
pnpm install --frozen-lockfile
pnpm dev

# Repository checks
make lint
make test
```

Ingest shared VAS/IFRS documents after Ollama has the `bge-m3` model:

```bash
make embed-shared
```

## Repository layout

```text
apps/backend/       FastAPI, agents, RAG, database, workers
apps/frontend/      Next.js 15 application
ingestion/          document parsers, metadata, and batch embedding
infra/docker/       local Compose configurations
infra/k8s/          Kustomize base and staging/production overlays
infra/terraform/    GCP networking, GKE, storage, IAM, WIF, secrets
supabase/           PostgreSQL migrations and Edge Functions
orchestration/n8n/  workflow definitions and webhook boundary
docs/               architecture, RAG design, prompts, and operations
```

## Deployment and evaluation

Production delivery uses GitHub Workload Identity Federation, Artifact Registry, a migration Job, and Kustomize. Terraform creates the GCP/GKE foundation; it intentionally requires a trusted GKE control-plane CIDR before apply. Runtime secrets are provisioned outside Git.

The nightly RAG evaluation workflow requires versioned external dataset URLs and service credentials. Evaluation datasets are not bundled with the repository.

Read [docs/RUNBOOK.md](docs/RUNBOOK.md) before provisioning or deploying production. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) describes the current implementation; [VAS_IFRS_ARCHITECTURE.md](VAS_IFRS_ARCHITECTURE.md) is the broader target blueprint.

## License

[MIT](LICENSE)
