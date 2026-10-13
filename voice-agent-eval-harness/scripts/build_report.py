"""Build reports and charts.  uv run python scripts/build_report.py"""

import _bootstrap  # noqa: F401
from voice_eval.cli import app

if __name__ == "__main__":
    app(["report"])
