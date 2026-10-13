"""Validate data/transcripts.jsonl: schema, balance, required fields, duplicates.

Usage:  uv run python scripts/validate_dataset.py
"""

import _bootstrap  # noqa: F401
from voice_eval.cli import app

if __name__ == "__main__":
    app(["validate-dataset", *__import__("sys").argv[1:]])
