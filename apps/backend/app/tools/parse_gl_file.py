"""Tool: parse an uploaded GL file into a normalised account list."""

from __future__ import annotations

import anyio


async def parse_gl_file(file_path: str) -> list[dict]:
    """Parse xlsx/csv GL export and return normalised account rows."""
    from app.gl.parser import parse

    return await anyio.to_thread.run_sync(parse, file_path)
