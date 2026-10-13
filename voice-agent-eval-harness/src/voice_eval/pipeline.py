"""High-level operations shared by the CLI, scripts and dashboard."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from voice_eval.analysis.agreement import AgreementResult, agreement_summary_rows, compute_agreement
from voice_eval.analysis.business_impact import BusinessAssumptions, impact_sweep
from voice_eval.analysis.disagreement import (
    human_disagreement_register,
    spec_conformance_register,
    spec_conformance_summary,
)
from voice_eval.analysis.threshold_sensitivity import (
    changed_classifications,
    human_error_rates_by_cutoff,
    sweep,
)
from voice_eval.annotation.annotation_service import HumanLabelState, load_human_labels
from voice_eval.config import (
    ANALYSIS_DIR,
    DEMO_RESULTS_DIR,
    EXPERIMENTS_DIR,
    DecisionPolicy,
    judge_settings,
    load_experiment_defaults,
    rel,
)
from voice_eval.dataset_loader import load_transcripts
from voice_eval.judge.evaluator import Evaluator
from voice_eval.judge.provider import HeuristicProvider, get_provider
from voice_eval.reporting.experiment_registry import (
    ExperimentRecord,
    latest_for,
    list_experiments,
    provenance_for,
    write_experiment,
)
from voice_eval.rubric_loader import load_rubric
from voice_eval.schemas import Evaluation, Transcript, utc_now


class ConfigurationError(RuntimeError):
    pass


def run_evaluation(
    rubric_version: str,
    provider_name: str,
    ids: list[str] | None = None,
    demo: bool = False,
    use_cache: bool = True,
    threshold: float | None = None,
    progress: Any = None,
) -> dict[str, Any]:
    settings = judge_settings()
    rubric = load_rubric(rubric_version)
    policy = DecisionPolicy.from_settings(pass_threshold=threshold)
    transcripts = load_transcripts()
    if ids:
        known = {t.transcript_id for t in transcripts}
        unknown = [i for i in ids if i not in known]
        if unknown:
            raise ConfigurationError(f"unknown transcript ids: {unknown}")
        transcripts = [t for t in transcripts if t.transcript_id in set(ids)]
    if provider_name == "anthropic" and not settings.api_key_present:
        raise ConfigurationError(
            f"{settings.api_key_env} is not set. Copy .env.example to .env and add a key to run a live LLM "
            "evaluation, or use --provider heuristic for the offline baseline (not an LLM)."
        )
    provider = get_provider(provider_name, settings, rubric.heuristic_rules)
    if isinstance(provider, HeuristicProvider):
        provider.register(transcripts)
    evaluator = Evaluator(provider, rubric, policy, settings, use_cache=use_cache)
    evals, fails = evaluator.evaluate_many(transcripts, progress)

    provenance = provenance_for(provider.name, provider.is_llm)
    scope = "all" if not ids else "subset"
    if demo:
        if provider.is_llm:
            raise ConfigurationError("--demo is reserved for the offline heuristic baseline")
        exp_id = f"demo_{provider.name}_{rubric_version}" + ("" if scope == "all" else "_subset")
        out_dir = DEMO_RESULTS_DIR / exp_id
    else:
        stamp = utc_now().replace(":", "").replace("-", "").replace("+0000", "Z")
        exp_id = f"{stamp}_{rubric_version}_{provider.name}_{evaluator.cfg.hash()[:6]}"
        out_dir = EXPERIMENTS_DIR / exp_id
    meta = {
        "provenance": provenance,
        "dataset_version": transcripts[0].dataset_version if transcripts else None,
        "rubric_version": rubric_version,
        "rubric_hash": rubric.content_hash,
        "judge_provider": provider.name,
        "judge_model": provider.model,
        "served_models": sorted({e.judge_model for e in evals}),
        "is_llm": provider.is_llm,
        "prompt_version": evaluator.cfg.prompt_version,
        "evaluation_config_hash": evaluator.cfg.hash(),
        "evaluation_config": evaluator.cfg.__dict__,
        "scope": scope,
        "n_requested": len(transcripts),
        "transcript_ids": [t.transcript_id for t in transcripts] if ids else "all",
    }
    return write_experiment(out_dir, exp_id, evals, fails, meta)


def select_experiment(
    rubric_version: str, experiment_id: str | None = None
) -> ExperimentRecord | None:
    """Prefer an explicit id; else the latest full-dataset LLM run; else the saved demo."""
    records = list_experiments()
    if experiment_id:
        return next((r for r in records if r.id == experiment_id), None)
    return (
        latest_for(rubric_version, "llm", records, full_dataset_only=True)
        or latest_for(rubric_version, "demo_heuristic", records, full_dataset_only=True)
        or latest_for(rubric_version, None, records)
    )


def _clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_clean(v) for v in obj]
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="split")
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


@dataclass
class AnalysisBundle:
    rubric_version: str
    experiment: ExperimentRecord | None
    evals: list[Evaluation]
    transcripts: list[Transcript]
    labels: HumanLabelState
    policy: DecisionPolicy
    agreement: AgreementResult | None
    human_register: pd.DataFrame
    spec_register: pd.DataFrame
    spec_summary: dict[str, pd.DataFrame]
    thresholds: pd.DataFrame
    changes: pd.DataFrame
    impact: pd.DataFrame

    @property
    def human_status(self) -> str:
        if not self.labels.sample_ids:
            return "sample_not_frozen"
        return "complete" if self.labels.complete else "pending"


def analyse(
    rubric_version: str, experiment_id: str | None = None, policy: DecisionPolicy | None = None
) -> AnalysisBundle:
    policy = policy or DecisionPolicy.from_settings()
    defaults = load_experiment_defaults()
    cutoffs = [float(c) for c in defaults["threshold_sweep"]["cutoffs"]]
    band = float(defaults["threshold_sweep"]["borderline_band"])
    transcripts = load_transcripts()
    exp = select_experiment(rubric_version, experiment_id)
    evals = exp.evaluations() if exp else []
    labels = load_human_labels()
    humans = labels.annotations if labels.complete else []
    agreement = compute_agreement(evals, humans, transcripts, policy) if humans and evals else None
    human_reg = (
        human_disagreement_register(evals, humans, transcripts, policy)
        if agreement
        else pd.DataFrame()
    )
    spec_reg = spec_conformance_register(evals, transcripts, policy) if evals else pd.DataFrame()
    spec_sum = spec_conformance_summary(evals, transcripts, policy) if evals else {}
    th = (
        sweep(evals, cutoffs, policy, humans or None, transcripts, band)
        if evals
        else pd.DataFrame()
    )
    ch = changed_classifications(evals, cutoffs, policy) if evals else pd.DataFrame()
    rates = (
        human_error_rates_by_cutoff(evals, humans, transcripts, cutoffs, policy) if humans else None
    )
    imp = (
        impact_sweep(evals, cutoffs, policy, BusinessAssumptions.defaults(), rates, band)
        if evals
        else pd.DataFrame()
    )
    return AnalysisBundle(
        rubric_version,
        exp,
        evals,
        transcripts,
        labels,
        policy,
        agreement,
        human_reg,
        spec_reg,
        spec_sum,
        th,
        ch,
        imp,
    )


def write_analysis(b: AnalysisBundle, out_dir: Path = ANALYSIS_DIR) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    v = b.rubric_version
    paths: dict[str, str] = {}

    def save(df: pd.DataFrame, name: str) -> None:
        p = out_dir / name
        df.to_csv(p, index=False)
        paths[name] = rel(p)

    status = {
        "rubric_version": v,
        "experiment_id": b.experiment.id if b.experiment else None,
        "provenance": b.experiment.manifest.get("provenance") if b.experiment else None,
        "judge_model": b.experiment.manifest.get("judge_model") if b.experiment else None,
        "human_labels": {
            "status": b.human_status,
            "required": b.labels.n_required,
            "completed": len(b.labels.annotations),
            "missing": b.labels.missing_ids,
        },
        "policy": b.policy.__dict__,
        "generated_at": utc_now(),
    }
    if b.agreement:
        a = b.agreement
        status["agreement"] = _clean(
            {
                "n_pairs": a.n_pairs,
                "binary": {k: v2 for k, v2 in a.binary.items() if k != "confusion"},
                "three_way": {k: v2 for k, v2 in a.three_way.items() if k != "confusion"},
                "per_dimension": a.per_dimension,
                "applicability": a.applicability,
                "gates": {
                    g: {k: v2 for k, v2 in m.items() if k != "confusion"}
                    for g, m in a.gates.items()
                },
                "critical_split": a.critical_split,
                "human_self_consistency": a.human_self_consistency,
                "excluded_review": a.excluded_review,
            }
        )
        save(agreement_summary_rows(a), f"agreement_dimensions_{v}.csv")
        save(a.per_scenario, f"agreement_scenarios_{v}.csv")
        save(a.mapping_sensitivity, f"review_mapping_sensitivity_{v}.csv")
        save(a.binary["confusion"].reset_index(names="reference"), f"confusion_binary_{v}.csv")
        save(b.human_register, f"disagreement_register_human_{v}.csv")
    else:
        status["agreement"] = (
            "PENDING — human annotations incomplete; no agreement metrics computed."
        )
    if not b.spec_register.empty or b.evals:
        save(b.spec_register, f"spec_conformance_register_{v}.csv")
        if b.spec_summary:
            save(b.spec_summary["gates"], f"spec_conformance_gates_{v}.csv")
            save(b.spec_summary["tiers"], f"spec_conformance_tiers_{v}.csv")
        save(b.thresholds, f"threshold_sensitivity_{v}.csv")
        save(b.changes, f"threshold_changed_classifications_{v}.csv")
        save(b.impact, f"business_impact_{v}.csv")
    p = out_dir / f"analysis_status_{v}.json"
    p.write_text(json.dumps(_clean(status), indent=2, default=str) + "\n", encoding="utf-8")
    paths[p.name] = rel(p)
    return paths
