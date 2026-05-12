"""Prompt registry — loads prompt metadata from prompts/registry.yaml."""
from __future__ import annotations

import yaml
from pathlib import Path

_REGISTRY_PATH = Path(__file__).parents[5] / "prompts" / "registry.yaml"


def load_registry() -> dict:
    """Load and return the prompt registry YAML."""
    with _REGISTRY_PATH.open() as f:
        return yaml.safe_load(f)
