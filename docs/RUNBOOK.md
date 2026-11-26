# Operations runbook

## Local stack

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.local.example apps/frontend/.env.local
docker compose -f infra/docker/docker-compose.dev.yml up --build
docker compose -f infra/docker/docker-compose.dev.yml exec ollama ollama pull bge-m3
docker compose -f infra/docker/docker-compose.dev.yml exec ollama ollama pull qwen2.5:14b-instruct
```

Health checks:

```bash
docker compose -f infra/docker/docker-compose.dev.yml ps
curl --fail http://localhost:8000/healthz
curl --fail http://localhost:8000/readyz
```

Stop without deleting data:

```bash
docker compose -f infra/docker/docker-compose.dev.yml down
```

Do not use `down -v` unless PostgreSQL, Qdrant, Redis, and Ollama volumes are intentionally disposable.

The development Compose backend applies Alembic migrations after PostgreSQL becomes healthy and before starting Uvicorn.

TEI runs only when the `reranker` profile is enabled. The backend still supports the existing retrieval-score fallback when TEI is unavailable.

```bash
docker compose -f infra/docker/docker-compose.dev.yml --profile reranker up -d tei
```

## GL smoke test

Use the FastAPI PostgreSQL database for GL workflow records. Apply the Alembic schema there. The Supabase migrations provision the separate Auth and PostgREST schema used for sign-in and tenant claims.

On a disposable test database, run the migration forward, back to the previous revision, and forward again. The downgrade deletes the GL workflow data introduced by revision `0003`, so only run this sequence on a test database.

```bash
cd apps/backend
uv sync --frozen --no-default-groups --extra dev
export DATABASE_URL=postgresql+asyncpg://gl_test:gl_test@127.0.0.1:5432/gl_test
export APP_ENV=test DEV_AUTH_BYPASS=false
uv run --no-sync alembic upgrade head
uv run --no-sync alembic downgrade 0002
uv run --no-sync alembic upgrade head
GL_INTEGRATION_TEST=1 uv run --no-sync pytest tests/integration/test_gl_workflow.py -q
```

For a browser smoke test, sign in as an accountant, upload a CSV or XLSX, complete any unmapped accounts, enter a balanced journal with a rationale, approve it, and export the adjusted trial balance. Confirm the source and adjustment totals against the fixture. Journals and reports are stored in Postgres, so they survive backend restarts. Reuse the same upload `Idempotency-Key` or draft/report request ID when retrying a lost response. Reuse the ID with the original payload.

The GL export is a signed debit-minus-credit reconciliation grouped by mapped account. It lists the approved journal IDs and reports the source imbalance. Statutory statements and estimates for leases, ECL and deferred tax require additional source data and accounting review.

## Database migrations

Apply migrations before starting traffic for a new backend release:

```bash
cd apps/backend
uv sync --frozen
uv run alembic upgrade head
```

The production workflow runs the same migration as a one-off Kubernetes Job and stops deployment if it fails. Back up production data and test downgrade/restore procedures before any destructive schema migration.

## Production prerequisites

1. Create the Terraform state bucket named by `infra/terraform/main.tf` before `terraform init`.
2. Copy `infra/terraform/envs/prod.tfvars` to a protected local values file if customization is required.
3. Replace the reserved `192.0.2.1/32` control-plane CIDR with the trusted egress CIDR of the deployment runner. Terraform intentionally must not be applied with the example CIDR.
4. Authenticate Terraform to the intended GCP project and review the plan.

```bash
cd infra/terraform
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan -var-file=envs/prod.tfvars
```

Terraform provisions networking/NAT, regional GKE and GPU pool, Artifact Registry, GCS buckets, Secret Manager containers, IAM, and GitHub Workload Identity Federation. It does not insert secret payloads.

## GitHub production configuration

Configure these repository/environment variables:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GAR_REPOSITORY`
- `GKE_CLUSTER`
- `PRODUCTION_HOST`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_DEPLOY_SERVICE_ACCOUNT`
- `NEXT_PUBLIC_SUPABASE_URL`

Configure `NEXT_PUBLIC_SUPABASE_ANON_KEY` as a GitHub environment secret. Although it is a public browser key, keeping build configuration centralized avoids accidental cross-environment builds.

Provision these Kubernetes secrets in namespace `vas-ifrs-prod` before deployment:

- `vas-ifrs-secrets`: at minimum `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SECRET_KEY`; add optional provider/storage keys used by the deployment.
- `n8n-secrets`: at minimum a stable `N8N_ENCRYPTION_KEY`, plus external database settings if n8n is not using its persistent local volume.
- `vas-ifrs-tls`: TLS certificate and key for the production hostname, normally managed by the platform certificate controller.

Never commit secret values or create them in command history on shared machines. Use the organization's secret delivery mechanism (for example External Secrets backed by Secret Manager).

## Deploy

Run the `Deploy Prod` workflow with an immutable image tag such as a Git commit SHA. The workflow:

1. authenticates through Workload Identity Federation;
2. builds and pushes backend/frontend images;
3. checks required runtime secrets;
4. runs Alembic in a migration Job;
5. applies the production Kustomize overlay;
6. pulls the pinned embedding and local chat models into the persistent Ollama volume;
7. waits for all deployments/stateful sets to roll out.

Post-deploy checks:

```bash
kubectl -n vas-ifrs-prod get pods,svc,ingress
kubectl -n vas-ifrs-prod rollout status deployment/backend
curl --fail https://<production-host>/healthz
```

Rollback application workloads:

```bash
kubectl -n vas-ifrs-prod rollout undo deployment/backend
kubectl -n vas-ifrs-prod rollout undo deployment/frontend
kubectl -n vas-ifrs-prod rollout undo deployment/celery-worker
```

Database rollback is migration-specific. Do not run an Alembic downgrade automatically unless the migration's data-loss behavior has been reviewed and a restore point exists.

## Nightly RAG evaluation

Configure GitHub variables `RETRIEVAL_EVAL_DATASET_URL` and `HALLUCINATION_EVAL_DATASET_URL`, plus secrets `EVAL_QDRANT_URL`, `EVAL_QDRANT_API_KEY` when required, `EVAL_OLLAMA_BASE_URL`, and `GEMINI_API_KEY`. URLs should point to immutable/versioned JSONL datasets. Results are retained as workflow artifacts for 30 days.

## Incident triage

```bash
kubectl -n vas-ifrs-prod get events --sort-by=.lastTimestamp
kubectl -n vas-ifrs-prod logs deployment/backend --tail=200
kubectl -n vas-ifrs-prod logs deployment/frontend --tail=200
kubectl -n vas-ifrs-prod logs statefulset/qdrant --tail=200
kubectl -n vas-ifrs-prod logs deployment/ollama --tail=200
```

- `/healthz` proves the backend process is alive; `/readyz` verifies runtime dependencies.
- A TEI failure degrades reranking, but an Ollama embedding or Qdrant failure blocks retrieval.
- HTTP 501 on standalone KB/GL/mapping/adjustment/report/admin workflows is an implementation boundary, not a transient outage.
- If tenant isolation is suspected, stop affected writes, preserve audit logs, and verify JWT claims, tenant context, RLS policies, and Qdrant collection routing before resuming traffic.
