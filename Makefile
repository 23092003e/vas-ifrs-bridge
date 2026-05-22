.PHONY: dev dev-backend dev-frontend lint test deploy-staging

dev:
	docker compose -f infra/docker/docker-compose.dev.yml up

dev-backend:
	cd apps/backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd apps/frontend && pnpm dev

lint:
	cd apps/backend && ruff check . && mypy .
	cd apps/frontend && pnpm biome check .

test:
	cd apps/backend && pytest
	cd apps/frontend && pnpm vitest run

migrate:
	cd apps/backend && alembic upgrade head

embed-shared:
	PYTHONPATH=apps/backend:ingestion apps/backend/.venv/bin/python ingestion/pipelines/embedders/batch_embed.py --scope shared
