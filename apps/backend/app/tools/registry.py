"""Tool registry — maps tool names to callable implementations."""
from __future__ import annotations

from app.tools.search_shared_kb import search_shared_kb
from app.tools.search_tenant_kb import search_tenant_kb
from app.tools.parse_gl_file import parse_gl_file
from app.tools.map_account import map_account
from app.tools.generate_adjustment import generate_adjustment
from app.tools.export_report import export_report

TOOL_REGISTRY: dict[str, object] = {
    "search_shared_kb": search_shared_kb,
    "search_tenant_kb": search_tenant_kb,
    "parse_gl_file": parse_gl_file,
    "map_account": map_account,
    "generate_adjustment": generate_adjustment,
    "export_report": export_report,
}
