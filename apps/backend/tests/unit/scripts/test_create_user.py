import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.create_user import build_user_payload


def test_build_user_payload_leaves_tenant_provisioning_to_database() -> None:
    payload = build_user_payload(
        email="owner@example.test",
        password="not-a-real-password",
        full_name="Test Owner",
        workspace="Finance Team",
    )

    assert payload == {
        "email": "owner@example.test",
        "password": "not-a-real-password",
        "email_confirm": True,
        "user_metadata": {
            "full_name": "Test Owner",
            "workspace": "Finance Team",
        },
    }
    assert "app_metadata" not in payload
    assert "tenant_id" not in payload["user_metadata"]
    assert "role" not in payload["user_metadata"]
