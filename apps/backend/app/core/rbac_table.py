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

# (HTTP method, route path prefix) → minimum role string required.
# "*" applies to every method.
ROUTE_ROLE_MAP: dict[tuple[str, str], str] = {
    ("*", "/v1/admin"): "admin",
    ("*", "/v1/admin/users"): "admin",
    ("*", "/v1/admin/audit"): "auditor",
    ("POST", "/v1/reports/generate"): "accountant",
    ("POST", "/v1/adjustments"): "accountant",
    ("POST", "/v1/gl"): "accountant",
    ("GET", "/v1/reports"): "auditor",
    ("PUT", "/v1/mappings"): "accountant",
    ("POST", "/v1/documents/upload"): "accountant",
}


def has_permission(role: str, action: str) -> bool:
    return action in PERMISSIONS.get(role, set())
