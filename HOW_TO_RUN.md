# How to run VAS-IFRS Bridge

## Full stack with Docker

Requirements: Docker Desktop and Docker Compose.

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.local.example apps/frontend/.env.local
```

For local-only access, set `DEV_AUTH_BYPASS=true` in `apps/backend/.env`. Replace placeholder secrets; do not reuse development values in production.

```bash
docker compose -f infra/docker/docker-compose.dev.yml up --build
docker compose -f infra/docker/docker-compose.dev.yml exec backend alembic upgrade head
docker compose -f infra/docker/docker-compose.dev.yml exec ollama ollama pull bge-m3
docker compose -f infra/docker/docker-compose.dev.yml exec ollama ollama pull qwen2.5:14b-instruct
```

| Service | Address |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Qdrant | http://localhost:6333/dashboard |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| Ollama | http://localhost:11434 |

Verify the stack:

```bash
docker compose -f infra/docker/docker-compose.dev.yml ps
curl --fail http://localhost:8000/healthz
curl --fail http://localhost:8000/readyz
```

Stop it without deleting persistent volumes:

```bash
docker compose -f infra/docker/docker-compose.dev.yml down
```

## Host development

Requirements: Python 3.11+, `uv`, Node.js 22+, pnpm 11, plus PostgreSQL/Qdrant/Redis/Ollama endpoints.

Backend:

```bash
cd apps/backend
cp .env.example .env
uv sync --frozen --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

Frontend, in another terminal:

```bash
cd apps/frontend
cp .env.local.example .env.local
pnpm install --frozen-lockfile
pnpm dev
```

The main backend variables are `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SECRET_KEY`, `QDRANT_URL`, `REDIS_URL`, and `OLLAMA_BASE_URL`. `TEI_URL` enables cross-encoder reranking. OpenAI, Anthropic, Gemini, GCS, and Langfuse settings are optional for the features that use them.

## Ingest documents

Put source files under:

```text
ingestion/raw/shared/vas/
ingestion/raw/shared/ifrs/
ingestion/raw/tenant/<tenant-id>/
```

Then pull the embedding model and run the checked-in ingestion wrapper:

```bash
docker compose -f infra/docker/docker-compose.dev.yml exec ollama ollama pull bge-m3
make embed-shared
```

PowerShell users can run `./ingest.ps1 -Scope vas`, `ifrs`, `shared`, `tenant`, or `all`; use `-DryRun` to preview.

## Checks

```bash
make lint
make test

cd apps/frontend && pnpm build
docker compose -f infra/docker/docker-compose.dev.yml config --quiet
```

Backend integration tests need their documented external services; unit tests do not.

## Troubleshooting

Port 3000 already in use:

```bash
lsof -nP -iTCP:3000 -sTCP:LISTEN
```

Stop the process/container you recognize, or change the frontend host mapping in the Compose file. Do not terminate an unknown process blindly.

Orphan container warning:

```bash
docker compose -f infra/docker/docker-compose.dev.yml ps -a
docker compose -f infra/docker/docker-compose.dev.yml up --remove-orphans
```

Use `--remove-orphans` only after confirming those containers belong to this Compose project. The current development stack includes Qdrant, so a Qdrant container created by this file is no longer an orphan.

Other checks:

- Migration fails: verify PostgreSQL is healthy and `DATABASE_URL` targets the correct host (`db` inside Compose, `localhost` from the host).
- Qdrant collection missing: run ingestion after pulling `bge-m3`.
- API returns 401: use a valid Supabase JWT, or enable `DEV_AUTH_BYPASS` only in local development.
- Local answers fail: check `docker compose ... logs ollama backend` and confirm the required Ollama chat model is available.
- HTTP 501 from KB/GL/mapping/adjustment/report/admin routes: those standalone workflow contracts remain explicit implementation boundaries; streaming chat is the supported end-to-end path today.

For production provisioning, secrets, deployment, rollback, and nightly evaluation, see [docs/RUNBOOK.md](docs/RUNBOOK.md).
