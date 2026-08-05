create schema auth;

create table auth.users (
  id uuid primary key,
  email text not null,
  raw_user_meta_data jsonb not null default '{}',
  raw_app_meta_data jsonb not null default '{}'
);

create function auth.uid() returns uuid
language sql stable
as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin;
  end if;
end
$$;
