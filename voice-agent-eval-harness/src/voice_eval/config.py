"""Configuration loading and repository-relative path resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def _find_root() -> Path:
    """Locate the repository root (the directory holding pyproject.toml)."""
    env_root = os.environ.get("VOICE_EVAL_ROOT")
    if env_root:
        return Path(env_root).resolve()
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists() and (parent / "configs").exists():
            return parent
    return Path.cwd().resolve()


ROOT: Path = _find_root()
CONFIG_DIR = ROOT / "configs"
RUBRIC_DIR = CONFIG_DIR / "rubrics"
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
DEMO_RESULTS_DIR = RESULTS_DIR / "demo"
EXPERIMENTS_DIR = RESULTS_DIR / "experiments"
ANALYSIS_DIR = RESULTS_DIR / "analysis"
CACHE_DIR = RESULTS_DIR / "cache"
REPORTS_DIR = ROOT / "reports"

TRANSCRIPTS_PATH = DATA_DIR / "transcripts.jsonl"
TRANSCRIPTS_CSV_PATH = DATA_DIR / "transcripts_readable.csv"
MANIFEST_PATH = DATA_DIR / "dataset_manifest.json"
ANNOTATION_SAMPLE_PATH = DATA_DIR / "annotation_sample.json"
ANNOTATION_TEMPLATE_PATH = DATA_DIR / "human_annotations_template.csv"
HUMAN_ANNOTATIONS_PATH = DATA_DIR / "human_annotations.csv"
ANNOTATION_DB_PATH = DATA_DIR / "annotations.db"


def rel(path: Path) -> str:
    """Return a repository-relative POSIX path for display and manifests."""
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=1)
def load_settings() -> dict[str, Any]:
    return _load_yaml(CONFIG_DIR / "settings.yaml")


@lru_cache(maxsize=1)
def load_experiment_defaults() -> dict[str, Any]:
    return _load_yaml(CONFIG_DIR / "experiment_defaults.yaml")


@dataclass(frozen=True)
class JudgeSettings:
    provider: str
    model: str
    max_tokens: int
    timeout_seconds: float
    max_retries: int
    min_seconds_between_requests: float
    effort: str
    api_key_env: str

    @property
    def api_key_present(self) -> bool:
        return bool(os.environ.get(self.api_key_env))


def judge_settings() -> JudgeSettings:
    """Resolve judge settings: environment variables override settings.yaml."""
    load_dotenv(ROOT / ".env", override=False)
    cfg = load_settings().get("judge", {})
    return JudgeSettings(
        provider=os.environ.get("JUDGE_PROVIDER", cfg.get("provider", "anthropic")),
        model=os.environ.get("JUDGE_MODEL", cfg.get("model", "claude-opus-5-5")),
        max_tokens=int(os.environ.get("JUDGE_MAX_TOKENS", cfg.get("max_tokens", 16000))),
        timeout_seconds=float(
            os.environ.get("JUDGE_TIMEOUT_SECONDS", cfg.get("timeout_seconds", 180))
        ),
        max_retries=int(os.environ.get("JUDGE_MAX_RETRIES", cfg.get("max_retries", 4))),
        min_seconds_between_requests=float(
            os.environ.get(
                "JUDGE_MIN_SECONDS_BETWEEN_REQUESTS", cfg.get("min_seconds_between_requests", 1.0)
            )
        ),
        effort=os.environ.get("JUDGE_EFFORT", cfg.get("effort", "high")),
        api_key_env=cfg.get("api_key_env", "ANTHROPIC_API_KEY"),
    )


@dataclass(frozen=True)
class DecisionPolicy:
    """Operational decision policy. Kept separate from rubric definitions."""

    pass_threshold: float = 75.0
    unconfirmed_gate_policy: str = "review_required"  # or "fail"
    review_required_binary_mapping: str = "as_fail"  # as_fail | as_pass | exclude
    route_injection_flagged_passes_to_review: bool = True
    cross_check_with_lexical_screen: bool = True

    @classmethod
    def from_settings(cls, **overrides: Any) -> DecisionPolicy:
        cfg = dict(load_settings().get("decision_policy", {}))
        cfg.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**cfg)
