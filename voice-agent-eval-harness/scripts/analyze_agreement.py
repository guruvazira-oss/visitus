"""Compute agreement.  uv run python scripts/analyze_agreement.py --rubric v1"""

import _bootstrap  # noqa: F401
from voice_eval.cli import app

if __name__ == "__main__":
    app(["agreement", *__import__("sys").argv[1:]])
