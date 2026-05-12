"""Static RBAC permission table mapping roles to allowed actions."""
from __future__ import annotations

from app.core.rbac import Role

# Maps (role, action) -> bool
# Actions: read, write, admin, export, manage_users
PERMISSIONS: dict[Role, set[str]] = {
    Role.OWNER: {"read", "write", "admin", "export", "manage_users"},
    Role.ADMIN: {"read", "write", "admin", "export", "manage_users"},
    Role.ACCOUNTANT: {"read", "write", "export"},
    Role.AUDITOR: {"read", "export"},
    Role.VIEWER: {"read"},
}


def has_permission(role: Role, action: str) -> bool:
    """Return True if the given role is allowed to perform action."""
    return action in PERMISSIONS.get(role, set())
