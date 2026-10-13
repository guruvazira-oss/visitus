"""Import human annotations.  uv run python scripts/import_annotations.py data/human_annotations.csv --rubric v1"""

import _bootstrap  # noqa: F401
from voice_eval.cli import app

if __name__ == "__main__":
    app(["import-annotations", *__import__("sys").argv[1:]])
