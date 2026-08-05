#!/usr/bin/env python3
import sys
from typing import Any

import httpx

from app.settings import settings


def build_user_payload(
    *, email: str, password: str, full_name: str, workspace: str
) -> dict[str, Any]:
    """Build an Admin API payload; database triggers own tenant provisioning."""
    return {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {
            "full_name": full_name,
            "workspace": workspace,
        },
    }


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_user.py <email> <password> [full_name] [workspace]")
        return 1

    email = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else "Test User"
    workspace = sys.argv[4] if len(sys.argv) > 4 else "Default Workspace"
    url = f"{settings.supabase_url}/auth/v1/admin/users"
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }

    payload = build_user_payload(
        email=email,
        password=password,
        full_name=full_name,
        workspace=workspace,
    )

    print(f"Creating user {email} with Supabase Admin API...")
    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code in (200, 201):
            user_data = resp.json()
            print("Successfully created confirmed user!")
            print(f"ID: {user_data.get('id')}")
            print(f"Email: {user_data.get('email')}")
            tenant_id = user_data.get("app_metadata", {}).get("tenant_id")
            print(f"Tenant ID: {tenant_id}")
            return 0
        else:
            print(f"Error {resp.status_code}: {resp.text}")
            return 1
    except httpx.HTTPError as e:
        print(f"Request failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
