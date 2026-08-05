-- 0006_harden_rls.sql: remove recursive policies and close tenant isolation gaps

alter table users
  add constraint users_auth_user_fk
  foreign key (id) references auth.users(id) on delete cascade
  not valid;

create or replace function public.current_user_tenant_id()
returns uuid
language sql
stable
security definer
set search_path = ''
as $$
  select tenant_id from public.users where id = auth.uid()
$$;

create or replace function public.current_user_role()
returns text
language sql
stable
security definer
set search_path = ''
as $$
  select role from public.users where id = auth.uid()
$$;

revoke all on function public.current_user_tenant_id() from public;
revoke all on function public.current_user_role() from public;
grant execute on function public.current_user_tenant_id() to authenticated;
grant execute on function public.current_user_role() to authenticated;

drop policy if exists "tenants: read own" on tenants;
create policy "tenants: read own" on tenants
  for select using (id = public.current_user_tenant_id());

drop policy if exists "users: read same tenant" on users;
drop policy if exists "users: insert by admin" on users;
create policy "users: read same tenant" on users
  for select using (tenant_id = public.current_user_tenant_id());
create policy "users: insert by admin" on users
  for insert with check (
    public.current_user_role() in ('owner', 'admin')
    and tenant_id = public.current_user_tenant_id()
  );

drop policy if exists "documents: tenant isolation" on documents;
create policy "documents: read tenant or shared" on documents
  for select using (
    tenant_id = public.current_user_tenant_id()
    or tenant_id is null
  );
create policy "documents: insert own tenant" on documents
  for insert with check (tenant_id = public.current_user_tenant_id());
create policy "documents: update own tenant" on documents
  for update
  using (tenant_id = public.current_user_tenant_id())
  with check (tenant_id = public.current_user_tenant_id());
create policy "documents: delete own tenant" on documents
  for delete using (tenant_id = public.current_user_tenant_id());

alter table kb_chunks enable row level security;
create policy "kb_chunks: read tenant or shared" on kb_chunks
  for select using (
    exists (
      select 1 from documents
      where documents.id = kb_chunks.document_id
        and (
          documents.tenant_id = public.current_user_tenant_id()
          or documents.tenant_id is null
        )
    )
  );
create policy "kb_chunks: insert own tenant" on kb_chunks
  for insert with check (
    exists (
      select 1 from documents
      where documents.id = kb_chunks.document_id
        and documents.tenant_id = public.current_user_tenant_id()
    )
  );
create policy "kb_chunks: update own tenant" on kb_chunks
  for update
  using (
    exists (
      select 1 from documents
      where documents.id = kb_chunks.document_id
        and documents.tenant_id = public.current_user_tenant_id()
    )
  )
  with check (
    exists (
      select 1 from documents
      where documents.id = kb_chunks.document_id
        and documents.tenant_id = public.current_user_tenant_id()
    )
  );
create policy "kb_chunks: delete own tenant" on kb_chunks
  for delete using (
    exists (
      select 1 from documents
      where documents.id = kb_chunks.document_id
        and documents.tenant_id = public.current_user_tenant_id()
    )
  );

drop policy if exists "gl_uploads: tenant isolation" on gl_uploads;
create policy "gl_uploads: tenant isolation" on gl_uploads
  for all
  using (tenant_id = public.current_user_tenant_id())
  with check (tenant_id = public.current_user_tenant_id());

drop policy if exists "mappings: tenant isolation" on mappings;
create policy "mappings: tenant isolation" on mappings
  for all
  using (tenant_id = public.current_user_tenant_id())
  with check (tenant_id = public.current_user_tenant_id());

drop policy if exists "adjustment_entries: tenant isolation" on adjustment_entries;
create policy "adjustment_entries: tenant isolation" on adjustment_entries
  for all
  using (tenant_id = public.current_user_tenant_id())
  with check (tenant_id = public.current_user_tenant_id());

drop policy if exists "query_logs: tenant isolation" on query_logs;
create policy "query_logs: read own or tenant admin" on query_logs
  for select using (
    tenant_id = public.current_user_tenant_id()
    and (
      user_id = auth.uid()
      or public.current_user_role() in ('owner', 'admin', 'auditor')
    )
  );
create policy "query_logs: insert own" on query_logs
  for insert with check (
    tenant_id = public.current_user_tenant_id()
    and user_id = auth.uid()
  );

drop policy if exists "reports: tenant isolation" on reports;
create policy "reports: tenant isolation" on reports
  for all
  using (tenant_id = public.current_user_tenant_id())
  with check (tenant_id = public.current_user_tenant_id());

drop policy if exists "audit_logs: admin read only" on audit_logs;
create policy "audit_logs: admin read only" on audit_logs
  for select using (
    tenant_id = public.current_user_tenant_id()
    and public.current_user_role() in ('owner', 'admin', 'auditor')
  );
