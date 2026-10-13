"""Experiment artifacts: one directory per run with manifest, evaluations and failures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from voice_eval.config import DEMO_RESULTS_DIR, EXPERIMENTS_DIR, rel
from voice_eval.schemas import DIMENSIONS, GATE_IDS, Evaluation, EvaluationFailure, utc_now

PROVENANCE_LABELS = {
    "demo_heuristic": "Saved demo evaluation — offline heuristic baseline (NOT an LLM)",
    "llm": "Actual LLM evaluation",
    "test": "Test fixture (not a research result)",
}


def provenance_for(provider: str, is_llm: bool) -> str:
    if is_llm:
        return "llm"
    return "demo_heuristic" if provider == "heuristic" else "test"


def evaluations_frame(evals: list[Evaluation]) -> pd.DataFrame:
    rows = []
    for e in evals:
        row: dict[str, Any] = {
            "transcript_id": e.transcript_id,
            "rubric_version": e.rubric_version,
            "judge_provider": e.judge_provider,
            "judge_model": e.judge_model,
            "overall_score": e.overall_score,
            "decision": e.decision.value,
            "injection_flag": e.injection_screen_flag or e.injection_attempt_detected,
            "n_grounding_issues": len(e.grounding_issues),
        }
        for d in DIMENSIONS:
            row[d] = e.dimension_scores[d]
        for g in e.critical_gate_results:
            row[f"{g.gate_id}__judge"] = g.judge_assessment.value
            row[f"{g.gate_id}__status"] = g.adjudication_status.value
        rows.append(row)
    cols = [
        "transcript_id",
        "rubric_version",
        "judge_provider",
        "judge_model",
        *DIMENSIONS,
        "overall_score",
        "decision",
        "injection_flag",
        "n_grounding_issues",
    ]
    cols += [f"{g}__{s}" for g in GATE_IDS for s in ("judge", "status")]
    return pd.DataFrame(rows, columns=cols)


def write_experiment(
    out_dir: Path,
    experiment_id: str,
    evals: list[Evaluation],
    fails: list[EvaluationFailure],
    meta: dict[str, Any],
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "evaluations.jsonl").open("w", encoding="utf-8") as fh:
        for e in evals:
            fh.write(e.model_dump_json() + "\n")
    with (out_dir / "failures.jsonl").open("w", encoding="utf-8") as fh:
        for f in fails:
            fh.write(f.model_dump_json() + "\n")
    evaluations_frame(evals).to_csv(out_dir / "scores.csv", index=False)
    requested = meta.get("n_requested", len(evals) + len(fails))
    manifest = {
        "experiment_id": experiment_id,
        "timestamp": utc_now(),
        **meta,
        "n_requested": requested,
        "n_successful": len(evals),
        "n_failed": len(fails),
        "status": "complete"
        if not fails and len(evals) == requested
        else ("partial" if evals else "failed"),
        "artifacts": {
            "evaluations": rel(out_dir / "evaluations.jsonl"),
            "failures": rel(out_dir / "failures.jsonl"),
            "scores_csv": rel(out_dir / "scores.csv"),
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


@dataclass
class ExperimentRecord:
    manifest: dict[str, Any]
    path: Path

    @property
    def id(self) -> str:
        return self.manifest["experiment_id"]

    def evaluations(self) -> list[Evaluation]:
        p = self.path / "evaluations.jsonl"
        if not p.exists():
            return []
        return [
            Evaluation.model_validate_json(line)
            for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def failures(self) -> list[EvaluationFailure]:
        p = self.path / "failures.jsonl"
        if not p.exists():
            return []
        return [
            EvaluationFailure.model_validate_json(line)
            for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


def list_experiments(
    roots: tuple[Path, ...] = (DEMO_RESULTS_DIR, EXPERIMENTS_DIR),
) -> list[ExperimentRecord]:
    records = []
    for root in roots:
        if not root.exists():
            continue
        for m in sorted(root.glob("*/manifest.json")):
            try:
                records.append(
                    ExperimentRecord(json.loads(m.read_text(encoding="utf-8")), m.parent)
                )
            except json.JSONDecodeError:
                continue
    records.sort(key=lambda r: r.manifest.get("timestamp", ""), reverse=True)
    return records


def latest_for(
    rubric_version: str,
    provenance: str | None = None,
    records: list[ExperimentRecord] | None = None,
    full_dataset_only: bool = False,
) -> ExperimentRecord | None:
    for r in records if records is not None else list_experiments():
        m = r.manifest
        if m.get("rubric_version") != rubric_version:
            continue
        if provenance and m.get("provenance") != provenance:
            continue
        if full_dataset_only and m.get("scope") != "all":
            continue
        return r
    return None
