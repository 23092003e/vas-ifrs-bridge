"""Static RBAC permission table — no imports from rbac.py to avoid circular deps."""

from __future__ import annotations

# role string → set of allowed actions
PERMISSIONS: dict[str, set[str]] = {
    "owner": {"read", "write", "admin", "export", "manage_users"},
    "admin": {"read", "write", "admin", "export", "manage_users"},
    "accountant": {"read", "write", "export"},
    "auditor": {"read", "export"},
    "viewer": {"read"},
}

# route path prefix → minimum role string required (None = no role gate)
ROUTE_ROLE_MAP: dict[str, str] = {
    "/v1/admin": "admin",
    "/v1/admin/users": "admin",
    "/v1/admin/audit": "auditor",
    "/v1/reports/generate": "accountant",
    "/v1/adjustments/generate": "accountant",
    "/v1/gl/uploads": "accountant",
    "/v1/documents": "accountant",
}


def has_permission(role: str, action: str) -> bool:
    return action in PERMISSIONS.get(role, set())
