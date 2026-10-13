"""Threshold sweep.  uv run python scripts/run_threshold_analysis.py --rubric v1"""

import _bootstrap  # noqa: F401
from voice_eval.cli import app

if __name__ == "__main__":
    app(["thresholds", *__import__("sys").argv[1:]])
