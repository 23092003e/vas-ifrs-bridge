"""Tool: map a single VAS account code to its IFRS equivalent."""

from __future__ import annotations


async def map_account(vas_code: str, tenant_id: str) -> dict:
    """Return IFRS classification for a VAS account code."""
    from app.gl.mapping_engine import map_accounts

    results = await map_accounts(
        [{"account_code": vas_code, "account_name": ""}],
        tenant_id=tenant_id,
    )
    if not results:
        raise ValueError(f"Unable to map VAS account {vas_code}")
    return results[0]
