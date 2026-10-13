"""Run an evaluation. Example:  uv run python scripts/run_evaluation.py --provider heuristic --rubric v1"""

import _bootstrap  # noqa: F401
from voice_eval.cli import app

if __name__ == "__main__":
    app(["evaluate", *__import__("sys").argv[1:]])
