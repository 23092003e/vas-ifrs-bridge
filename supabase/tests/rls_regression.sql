insert into auth.users (id, email, raw_user_meta_data) values
  (
    '00000000-0000-4000-8000-000000000001',
    'a@example.test',
    '{"workspace":"Tenant A","role":"admin","tenant_id":"ffffffff-ffff-4fff-8fff-ffffffffffff"}'
  ),
  (
    '00000000-0000-4000-8000-000000000002',
    'b@example.test',
    '{"workspace":"Tenant B"}'
  );

insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
values (
  '00000000-0000-4000-8000-000000000003',
  'accountant@example.test',
  '{}',
  jsonb_build_object(
    'tenant_id', (select tenant_id::text from users where id = '00000000-0000-4000-8000-000000000001'),
    'role', 'accountant'
  )
);

do $$
begin
  if (select count(*) from users) <> 3 then
    raise exception 'auth signup did not create three user profiles';
  end if;
  if (select count(*) from tenants) <> 2 then
    raise exception 'auth signup did not create two tenants';
  end if;
  if exists (
    select 1
    from auth.users au
    join users u on u.id = au.id
    where au.raw_app_meta_data ->> 'tenant_id' is distinct from u.tenant_id::text
       or au.raw_app_meta_data ->> 'role' is distinct from u.role
  ) then
    raise exception 'trusted auth metadata does not match the user profile';
  end if;
  if (select role from users where id = '00000000-0000-4000-8000-000000000001') <> 'owner' then
    raise exception 'untrusted user metadata changed the signup role';
  end if;
  if (select role from users where id = '00000000-0000-4000-8000-000000000003') <> 'accountant' then
    raise exception 'trusted invitation role was not applied';
  end if;
end
$$;

insert into documents (id, tenant_id, filename, gcs_path, collection) values
  (
    '20000000-0000-4000-8000-000000000001',
    (select tenant_id from users where id = '00000000-0000-4000-8000-000000000001'),
    'a.pdf',
    'a.pdf',
    'tenant_a'
  ),
  (
    '20000000-0000-4000-8000-000000000002',
    (select tenant_id from users where id = '00000000-0000-4000-8000-000000000002'),
    'b.pdf',
    'b.pdf',
    'tenant_b'
  ),
  (
    '20000000-0000-4000-8000-000000000003',
    null,
    'shared.pdf',
    'shared.pdf',
    'kb_shared_vas'
  );

insert into kb_chunks (id, document_id, content) values
  (
    '30000000-0000-4000-8000-000000000001',
    '20000000-0000-4000-8000-000000000001',
    'tenant a'
  ),
  (
    '30000000-0000-4000-8000-000000000002',
    '20000000-0000-4000-8000-000000000002',
    'tenant b'
  ),
  (
    '30000000-0000-4000-8000-000000000003',
    '20000000-0000-4000-8000-000000000003',
    'shared'
  );

grant usage on schema public to authenticated;
grant select, insert, update, delete on all tables in schema public to authenticated;
grant execute on all functions in schema public to authenticated;

set role authenticated;
select set_config(
  'request.jwt.claim.sub',
  '00000000-0000-4000-8000-000000000001',
  false
);

do $$
declare
  visible_documents integer;
  visible_chunks integer;
  deleted_shared integer;
begin
  select count(*) into visible_documents from documents;
  if visible_documents <> 2 then
    raise exception 'expected 2 visible documents, got %', visible_documents;
  end if;

  select count(*) into visible_chunks from kb_chunks;
  if visible_chunks <> 2 then
    raise exception 'expected 2 visible chunks, got %', visible_chunks;
  end if;

  with deleted as (
    delete from documents
    where id = '20000000-0000-4000-8000-000000000003'
    returning id
  )
  select count(*) into deleted_shared from deleted;
  if deleted_shared <> 0 then
    raise exception 'tenant user deleted a shared document';
  end if;
end
$$;

do $$
begin
  begin
    insert into documents (tenant_id, filename, gcs_path, collection)
    values (null, 'forged.pdf', 'forged.pdf', 'kb_shared_vas');
    raise exception 'tenant user inserted a shared document';
  exception
    when insufficient_privilege then null;
  end;
end
$$;

reset role;
