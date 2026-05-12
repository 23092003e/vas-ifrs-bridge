"""Batch embedding script — embeds documents and upserts into Qdrant."""
from __future__ import annotations

import argparse


def main(scope: str) -> None:
    """Embed all pending documents for the given scope (shared|tenant)."""
    # TODO: query pending documents, embed, upsert to Qdrant
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["shared", "tenant"], default="shared")
    args = parser.parse_args()
    main(args.scope)
