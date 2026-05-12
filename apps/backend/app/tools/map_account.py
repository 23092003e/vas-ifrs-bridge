"""Tool: map a single VAS account code to its IFRS equivalent."""
from __future__ import annotations


async def map_account(vas_code: str, tenant_id: str) -> dict:
    """Return IFRS classification for a VAS account code."""
    # TODO: rule lookup then LLM fallback
    return {"vas_code": vas_code, "ifrs_code": None, "confidence": 0.0}
