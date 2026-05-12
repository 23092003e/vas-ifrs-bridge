-- 0001_init.sql: tenants and users tables

create extension if not exists "uuid-ossp";

create table tenants (
  id          uuid primary key default uuid_generate_v4(),
  name        text not null,
  plan        text not null default 'starter',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create table users (
  id          uuid primary key default uuid_generate_v4(),
  tenant_id   uuid not null references tenants(id) on delete cascade,
  email       text not null unique,
  role        text not null default 'viewer'
              check (role in ('owner','admin','accountant','auditor','viewer')),
  created_at  timestamptz not null default now()
);

create index idx_users_tenant_id on users(tenant_id);
