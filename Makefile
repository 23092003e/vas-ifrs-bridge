.PHONY: dev dev-backend dev-frontend lint test deploy-staging

dev:
	docker compose -f infra/docker/docker-compose.dev.yml up

dev-backend:
	cd apps/backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd apps/frontend && pnpm dev

lint:
	cd apps/backend && uv run ruff check . && uv run mypy app/
	pnpm --dir apps/frontend lint

test:
	cd apps/backend && uv run pytest
	pnpm --dir apps/frontend test

migrate:
	cd apps/backend && uv run alembic upgrade head

embed-shared:
	./skills/vas-ifrs-document-ingestion/scripts/run_ingest.sh --scope shared
