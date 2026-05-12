-- 0002_rls_policies.sql: Row Level Security policies

alter table tenants enable row level security;
alter table users enable row level security;

-- Users can only see their own tenant
create policy "tenants: read own" on tenants
  for select using (
    id = (select tenant_id from users where id = auth.uid())
  );

-- Users can only see users in their own tenant
create policy "users: read same tenant" on users
  for select using (
    tenant_id = (select tenant_id from users where id = auth.uid())
  );

-- Only owners/admins can insert users
create policy "users: insert by admin" on users
  for insert with check (
    (select role from users where id = auth.uid()) in ('owner', 'admin')
    and tenant_id = (select tenant_id from users where id = auth.uid())
  );
