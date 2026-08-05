#!/usr/bin/env bash
set -euo pipefail

test_database_url="${SUPABASE_TEST_DATABASE_URL:?SUPABASE_TEST_DATABASE_URL is required}"
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

psql "$test_database_url" -v ON_ERROR_STOP=1 -f "$repo_root/supabase/tests/setup_auth.sql"
for migration in "$repo_root"/supabase/migrations/*.sql; do
    psql "$test_database_url" -v ON_ERROR_STOP=1 -f "$migration"
done
psql "$test_database_url" -v ON_ERROR_STOP=1 -f "$repo_root/supabase/tests/rls_regression.sql"
