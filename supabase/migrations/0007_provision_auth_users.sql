-- 0007_provision_auth_users.sql: create tenant context for every auth user

create or replace function public.prepare_auth_user_tenant()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  requested_tenant_id uuid;
  resolved_tenant_id uuid;
  resolved_tenant_name text;
  resolved_plan text;
  resolved_role text;
begin
  if nullif(new.email, '') is null then
    raise exception 'An email address is required to provision a user';
  end if;

  begin
    requested_tenant_id := nullif(new.raw_app_meta_data ->> 'tenant_id', '')::uuid;
  exception
    when invalid_text_representation then
      raise exception 'Invalid tenant_id in app metadata';
  end;

  if requested_tenant_id is null then
    resolved_tenant_id := public.uuid_generate_v4();
    resolved_tenant_name := coalesce(
      nullif(btrim(new.raw_user_meta_data ->> 'workspace'), ''),
      'Default Workspace'
    );
    resolved_plan := 'starter';
    resolved_role := 'owner';

    insert into public.tenants (id, name, plan)
    values (resolved_tenant_id, resolved_tenant_name, resolved_plan);
  else
    select name, plan
      into resolved_tenant_name, resolved_plan
      from public.tenants
      where id = requested_tenant_id;

    if not found then
      raise exception 'Tenant % in app metadata does not exist', requested_tenant_id;
    end if;

    resolved_tenant_id := requested_tenant_id;
    resolved_role := coalesce(
      nullif(new.raw_app_meta_data ->> 'role', ''),
      'viewer'
    );

    if resolved_role not in ('owner', 'admin', 'accountant', 'auditor', 'viewer') then
      raise exception 'Invalid role in app metadata';
    end if;
  end if;

  new.raw_app_meta_data := coalesce(new.raw_app_meta_data, '{}'::jsonb)
    || jsonb_build_object(
      'tenant_id', resolved_tenant_id::text,
      'tenant_name', resolved_tenant_name,
      'plan', resolved_plan,
      'role', resolved_role
    );

  return new;
end
$$;

create or replace function public.create_auth_user_profile()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.users (id, tenant_id, email, role)
  values (
    new.id,
    (new.raw_app_meta_data ->> 'tenant_id')::uuid,
    new.email,
    new.raw_app_meta_data ->> 'role'
  );

  return new;
end
$$;

revoke all on function public.prepare_auth_user_tenant() from public;
revoke all on function public.create_auth_user_profile() from public;

drop trigger if exists prepare_auth_user_tenant on auth.users;
create trigger prepare_auth_user_tenant
  before insert on auth.users
  for each row execute function public.prepare_auth_user_tenant();

drop trigger if exists create_auth_user_profile on auth.users;
create trigger create_auth_user_profile
  after insert on auth.users
  for each row execute function public.create_auth_user_profile();
