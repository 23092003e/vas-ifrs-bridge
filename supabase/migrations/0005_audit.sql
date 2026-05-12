-- 0005_audit.sql: query_logs, reports, and audit_logs

create table query_logs (
  id              uuid primary key default uuid_generate_v4(),
  tenant_id       uuid not null references tenants(id) on delete cascade,
  user_id         uuid not null references users(id) on delete cascade,
  conversation_id uuid,
  prompt_tokens   integer not null default 0,
  completion_tokens integer not null default 0,
  provider        text,
  latency_ms      integer,
  created_at      timestamptz not null default now()
);

alter table query_logs enable row level security;

create policy "query_logs: tenant isolation" on query_logs
  for all using (
    tenant_id = (select tenant_id from users where id = auth.uid())
  );

create table reports (
  id          uuid primary key default uuid_generate_v4(),
  tenant_id   uuid not null references tenants(id) on delete cascade,
  report_type text not null,
  period      text not null,
  status      text not null default 'pending'
              check (status in ('pending','generating','done','failed')),
  gcs_path    text,
  created_at  timestamptz not null default now()
);

alter table reports enable row level security;

create policy "reports: tenant isolation" on reports
  for all using (
    tenant_id = (select tenant_id from users where id = auth.uid())
  );

create table audit_logs (
  id          uuid primary key default uuid_generate_v4(),
  tenant_id   uuid not null references tenants(id) on delete cascade,
  user_id     uuid not null references users(id) on delete cascade,
  action      text not null,
  resource    text not null,
  payload     jsonb,
  created_at  timestamptz not null default now()
);

alter table audit_logs enable row level security;

create policy "audit_logs: admin read only" on audit_logs
  for select using (
    (select role from users where id = auth.uid()) in ('owner','admin','auditor')
    and tenant_id = (select tenant_id from users where id = auth.uid())
  );

create index idx_audit_logs_tenant_id on audit_logs(tenant_id, created_at desc);
