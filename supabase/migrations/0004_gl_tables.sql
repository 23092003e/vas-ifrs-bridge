-- 0004_gl_tables.sql: GL uploads, mappings, and adjustment entries

create table gl_uploads (
  id          uuid primary key default uuid_generate_v4(),
  tenant_id   uuid not null references tenants(id) on delete cascade,
  filename    text not null,
  gcs_path    text not null,
  status      text not null default 'pending'
              check (status in ('pending','processing','done','failed')),
  created_at  timestamptz not null default now()
);

alter table gl_uploads enable row level security;

create policy "gl_uploads: tenant isolation" on gl_uploads
  for all using (
    tenant_id = (select tenant_id from users where id = auth.uid())
  );

create table mappings (
  id          uuid primary key default uuid_generate_v4(),
  tenant_id   uuid not null references tenants(id) on delete cascade,
  upload_id   uuid references gl_uploads(id) on delete set null,
  vas_code    text not null,
  ifrs_code   text not null,
  confidence  numeric(5,4) not null default 1.0,
  source      text not null default 'manual',
  created_at  timestamptz not null default now()
);

alter table mappings enable row level security;

create policy "mappings: tenant isolation" on mappings
  for all using (
    tenant_id = (select tenant_id from users where id = auth.uid())
  );

create table adjustment_entries (
  id          uuid primary key default uuid_generate_v4(),
  tenant_id   uuid not null references tenants(id) on delete cascade,
  mapping_id  uuid not null references mappings(id) on delete cascade,
  debit_acc   text not null,
  credit_acc  text not null,
  amount      numeric(18,2) not null,
  currency    text not null default 'VND',
  status      text not null default 'draft'
              check (status in ('draft','approved','rejected')),
  created_at  timestamptz not null default now()
);

alter table adjustment_entries enable row level security;

create policy "adjustment_entries: tenant isolation" on adjustment_entries
  for all using (
    tenant_id = (select tenant_id from users where id = auth.uid())
  );
