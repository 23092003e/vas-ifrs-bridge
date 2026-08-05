"""Prompt registry — loads prompt metadata from prompts/registry.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml

_REGISTRY_PATH = Path(__file__).with_name("registry.yaml")


def load_registry() -> dict:
    """Load and return the prompt registry YAML."""
    with _REGISTRY_PATH.open() as f:
        return yaml.safe_load(f)
