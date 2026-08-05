# How to Run — VAS-IFRS Bridge

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | ≥ 3.11 | `uv` recommended over pip |
| Node.js | ≥ 18 | pnpm required |
| pnpm | any | `npm i -g pnpm` |
| Docker + Compose | any | for full-stack mode |
| Qdrant | latest | vector DB, port 6333 |
| Redis | 7 | queue + cache, port 6379 |
| Supabase project | — | auth + Postgres |

---

## Option A — Full Stack via Docker (Recommended)

```bash
# 1. Copy env files
cp apps/backend/.env.example apps/backend/.env
# Edit apps/backend/.env — fill in SUPABASE_*, GEMINI_API_KEY, SECRET_KEY

# 2. Start everything (backend + frontend + qdrant + redis + ollama)
make dev
# or directly:
docker compose -f infra/docker/docker-compose.dev.yml up
```

Services after start:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Qdrant UI | http://localhost:6333/dashboard |
| Ollama | http://localhost:11434 |

---

## Option B — Local Dev (No Docker)

### Step 1 — Infrastructure

Run Qdrant and Redis manually or via partial compose:

```bash
# Qdrant only
docker compose -f infra/docker/docker-compose.qdrant.yml up -d

# Redis
docker run -d -p 6379:6379 redis:7-alpine

# Ollama (optional — only needed for fast/local LLM tier)
docker compose -f infra/docker/docker-compose.ollama.yml up -d
```

### Step 2 — Backend

```bash
cd apps/backend

# Install deps
uv pip install -e ".[dev]"
# or: pip install -e ".[dev]"

# Copy and configure env
cp .env.example .env
# Required: DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
#           QDRANT_URL, GEMINI_API_KEY, SECRET_KEY, REDIS_URL

# Run DB migrations
alembic upgrade head

# Start dev server (hot reload)
uvicorn app.main:app --reload --port 8000
```

### Step 3 — Frontend

```bash
cd apps/frontend

# Install deps
pnpm install

# .env.local already committed with dev Supabase keys
# Verify BACKEND_URL=http://localhost:8000

# Start dev server
pnpm dev
# -> http://localhost:3000
```

Or use make shortcuts from root:

```bash
make dev-backend   # backend only
make dev-frontend  # frontend only
```

---

## Environment Variables

### Backend (`apps/backend/.env`)

```env
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/vasifrs
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-32-chars-min
GEMINI_API_KEY=your-gemini-api-key

# Optional — LLM providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434

# Optional — Storage
GCS_BUCKET_DOCS=vifb-docs-dev
GCS_BUCKET_EXPORTS=vifb-exports-dev

# Dev convenience — skip JWT validation
DEV_AUTH_BYPASS=true
```

### Frontend (`apps/frontend/.env.local`)

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
BACKEND_URL=http://localhost:8000
```

---

## Ingest Documents

Place raw documents in `ingestion/raw/`:

```
ingestion/raw/shared/ifrs/standards/   <- IFRS PDFs
ingestion/raw/shared/vas/standards/    <- VAS PDFs
ingestion/raw/tenant/<tenant-id>/      <- tenant docs
```

Then run ingestion (PowerShell / Windows):

```powershell
# All shared collections (also the default)
./ingest.ps1 -Scope shared

# VAS only
./ingest.ps1 -Scope vas

# IFRS only
./ingest.ps1 -Scope ifrs

# Tenant
./ingest.ps1 -Scope tenant -TenantId <tenant-uuid>

# Shared and tenant collections
./ingest.ps1 -Scope all -TenantId <tenant-uuid>

# Preview without writing
./ingest.ps1 -DryRun
```

Or directly via Python (Linux/macOS):

```bash
# From repo root
make embed-shared
# or:
PYTHONPATH=apps/backend:ingestion \
  apps/backend/.venv/bin/python ingestion/pipelines/embedders/batch_embed.py \
  --docs ingestion/raw/shared/vas --collection kb_shared_vas --scope shared \
  --ollama-url http://localhost:11434 --qdrant-url http://localhost:6333
```

---

## Build Knowledge Graph

```bash
PYTHONPATH=apps/backend:. apps/backend/.venv/bin/python \
  ingestion/pipelines/graph_builder.py \
  --docs ingestion/raw/shared \
  --output ingestion/metadata/paragraph_graph/cross_reference_graph.json
```

---

## Lint & Test

```bash
# All (from root)
make lint
make test

# Backend only
cd apps/backend
ruff check .
pytest                        # all tests
pytest tests/unit/            # unit only

# Frontend only
cd apps/frontend
pnpm lint
pnpm vitest run
```

---

## Ports Summary

| Port | Service |
|------|---------|
| 3000 | Next.js frontend |
| 8000 | FastAPI backend |
| 5432 | PostgreSQL (Supabase managed or local) |
| 6333 | Qdrant REST |
| 6334 | Qdrant gRPC |
| 6379 | Redis |
| 11434 | Ollama |

---

## Common Issues

**Backend won't start — `alembic upgrade head` fails**
Check `DATABASE_URL` in `.env`. Postgres must be running.

**Qdrant collection not found**
Run ingestion first (`make embed-shared`). Collections are created on first ingest.

**Auth 401 on all API calls**
Set `DEV_AUTH_BYPASS=true` in `apps/backend/.env` for local dev.

**Ollama model not loaded**
`docker exec -it <ollama-container> ollama pull qwen2.5:14b`

**Frontend shows blank / 404**
Confirm `BACKEND_URL=http://localhost:8000` in `apps/frontend/.env.local`.
