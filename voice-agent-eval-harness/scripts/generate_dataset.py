"""Generate the frozen synthetic dataset (refuses to overwrite a different existing file).

Usage:  uv run python scripts/generate_dataset.py [--force] [--verify]
"""

import _bootstrap  # noqa: F401
from voice_eval.cli import app

if __name__ == "__main__":
    app(["generate-dataset", *__import__("sys").argv[1:]])
