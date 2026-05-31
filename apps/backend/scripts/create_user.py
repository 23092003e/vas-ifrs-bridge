#!/usr/bin/env python3
import sys
import uuid
import httpx
from app.settings import settings

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_user.py <email> <password> [full_name] [workspace]")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else "Test User"
    workspace = sys.argv[4] if len(sys.argv) > 4 else "Default Workspace"
    tenant_id = str(uuid.uuid4())

    url = f"{settings.supabase_url}/auth/v1/admin/users"
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "email": email,
        "password": password,
        "email_confirm": True,  # Automatically mark email as confirmed
        "user_metadata": {
            "full_name": full_name,
            "workspace": workspace,
            "tenant_id": tenant_id,
            "role": "admin"
        }
    }

    print(f"Creating user {email} with Supabase Admin API...")
    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code in (200, 201):
            user_data = resp.json()
            print("Successfully created confirmed user!")
            print(f"ID: {user_data.get('id')}")
            print(f"Email: {user_data.get('email')}")
            print(f"Tenant ID: {tenant_id}")
        else:
            print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    main()
