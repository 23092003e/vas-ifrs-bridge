-- 0003_kb_chunks.sql: documents and kb_chunks tables

create table documents (
  id            uuid primary key default uuid_generate_v4(),
  tenant_id     uuid references tenants(id) on delete cascade,
  filename      text not null,
  gcs_path      text not null,
  collection    text not null,
  chunk_count   integer not null default 0,
  status        text not null default 'pending'
                check (status in ('pending','processing','done','failed')),
  created_at    timestamptz not null default now()
);

alter table documents enable row level security;

create policy "documents: tenant isolation" on documents
  for all using (
    tenant_id = (select tenant_id from users where id = auth.uid())
    or tenant_id is null  -- shared collection
  );

create table kb_chunks (
  id            uuid primary key default uuid_generate_v4(),
  document_id   uuid not null references documents(id) on delete cascade,
  content       text not null,
  metadata      jsonb not null default '{}',
  qdrant_id     uuid,
  created_at    timestamptz not null default now()
);

create index idx_kb_chunks_document_id on kb_chunks(document_id);
