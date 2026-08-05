from __future__ import annotations

from app.prompts.composer import render


def test_render_loads_templates_from_application_prompt_directory() -> None:
    rendered = render("system/base.vi.j2", app_name="VAS-IFRS Bridge")

    assert rendered == ""
