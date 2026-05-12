"""Runs Unstructured.io on raw documents and writes normalised JSON output."""
from __future__ import annotations

import argparse


def main(input_path: str, output_path: str) -> None:
    """Process a document with Unstructured and save element JSON."""
    # TODO: call unstructured partition() and serialize elements
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    main(args.input, args.output)
