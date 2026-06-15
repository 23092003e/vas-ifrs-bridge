"""Prompt composer — renders Jinja2 templates with context variables."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = Path(__file__).parents[5] / "prompts"

_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=False)


def render(template_path: str, **context) -> str:
    """Render a Jinja2 prompt template with the given context variables."""
    template = _env.get_template(template_path)
    return template.render(**context)
