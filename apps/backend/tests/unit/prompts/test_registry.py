from __future__ import annotations

from app.prompts.registry import load_registry


def test_prompt_registry_loads_bundled_metadata() -> None:
    registry = load_registry()

    assert registry["prompts"]["retrieval_qa"]["template"] == "system/retrieval_qa.j2"
