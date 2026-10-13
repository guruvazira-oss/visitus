"""Threshold-sensitivity experiment.

Two populations are always reported separately:
* ``full_synthetic`` — all evaluated transcripts; judge decisions only (no ground truth).
* ``human_labeled``  — the human-annotated subset; judge decisions vs human labels.

Critical-gate overrides remain active at every cutoff (decisions are re-derived through
``scoring.decide``). The human reference decision does not change with the cutoff.
"""

from __future__ import annotations

import math

import pandas as pd

from voice_eval.analysis.agreement import binary_metrics, judge_decision_at, pair_up
from voice_eval.analysis.business_impact import BusinessAssumptions, bucket_shares, compute_impact
from voice_eval.config import DecisionPolicy
from voice_eval.schemas import AdjudicationStatus, Decision, Evaluation, HumanAnnotation, Transcript
from voice_eval.scoring import to_binary

_GATE_BLOCKING = {
    AdjudicationStatus.CONFIRMED_VIOLATION,
    AdjudicationStatus.JUDGE_ALLEGED_UNCONFIRMED,
    AdjudicationStatus.UNCERTAIN,
    AdjudicationStatus.HUMAN_UNCERTAIN,
}


def gate_override(e: Evaluation) -> bool:
    return any(g.adjudication_status in _GATE_BLOCKING for g in e.critical_gate_results)


def sweep(
    evals: list[Evaluation],
    cutoffs: list[float],
    policy: DecisionPolicy,
    humans: list[HumanAnnotation] | None = None,
    transcripts: list[Transcript] | None = None,
    band: float = 5.0,
    assumptions: BusinessAssumptions | None = None,
) -> pd.DataFrame:
    a = assumptions or BusinessAssumptions.defaults()
    pairs = pair_up(evals, humans or [], transcripts or []) if humans and transcripts else []
    rows = []
    for c in cutoffs:
        decs = [judge_decision_at(e, policy, c) for e in evals]
        n = len(decs)
        shares = bucket_shares(decs, [e.overall_score for e in evals], c, band)
        impact = compute_impact(shares, a, None, None)
        row = {
            "cutoff": c,
            "population": "full_synthetic",
            "n_evaluated": n,
            "n_pass": decs.count(Decision.PASS),
            "n_fail": decs.count(Decision.FAIL),
            "n_review_required": decs.count(Decision.REVIEW_REQUIRED),
            "pass_rate": decs.count(Decision.PASS) / n if n else math.nan,
            "fail_rate": decs.count(Decision.FAIL) / n if n else math.nan,
            "review_rate": decs.count(Decision.REVIEW_REQUIRED) / n if n else math.nan,
            "critical_gate_overrides": sum(gate_override(e) for e in evals),
            "n_borderline_pass": round(shares.p_borderline_pass * n),
            "est_reviewed_calls_per_month": impact["calls_sent_for_review"],
            "est_review_hours_per_month": impact["review_hours"],
            "n_human_labeled": len(pairs),
        }
        if pairs:
            hb, jb = [], []
            for p in pairs:
                x = to_binary(p.human.overall_decision, policy.review_required_binary_mapping)
                y = to_binary(
                    judge_decision_at(p.judge, policy, c), policy.review_required_binary_mapping
                )
                if x is not None and y is not None:
                    hb.append(x)
                    jb.append(y)
            m = binary_metrics(hb, jb)
            row.update(
                {
                    "human_agreement": m["raw_agreement"]["value"],
                    "human_agreement_ci_low": m["raw_agreement"]["ci_low"],
                    "human_agreement_ci_high": m["raw_agreement"]["ci_high"],
                    "false_pass_count": m["false_pass_count"],
                    "false_pass_rate": m["false_pass_rate"]["value"],
                    "false_fail_count": m["false_fail_count"],
                    "false_fail_rate": m["false_fail_rate"]["value"],
                    "kappa": m["kappa"]["value"],
                }
            )
        else:
            row.update(
                {
                    k: math.nan
                    for k in (
                        "human_agreement",
                        "human_agreement_ci_low",
                        "human_agreement_ci_high",
                        "false_pass_count",
                        "false_pass_rate",
                        "false_fail_count",
                        "false_fail_rate",
                        "kappa",
                    )
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def changed_classifications(
    evals: list[Evaluation], cutoffs: list[float], policy: DecisionPolicy
) -> pd.DataFrame:
    """Calls whose decision changes between consecutive cutoffs."""
    rows = []
    cs = sorted(cutoffs)
    for lo, hi in zip(cs, cs[1:], strict=False):
        for e in evals:
            a, b = judge_decision_at(e, policy, lo), judge_decision_at(e, policy, hi)
            if a != b:
                rows.append(
                    {
                        "from_cutoff": lo,
                        "to_cutoff": hi,
                        "transcript_id": e.transcript_id,
                        "overall_score": e.overall_score,
                        "decision_before": a.value,
                        "decision_after": b.value,
                    }
                )
    return pd.DataFrame(
        rows,
        columns=[
            "from_cutoff",
            "to_cutoff",
            "transcript_id",
            "overall_score",
            "decision_before",
            "decision_after",
        ],
    )


def human_error_rates_by_cutoff(
    evals: list[Evaluation],
    humans: list[HumanAnnotation],
    transcripts: list[Transcript],
    cutoffs: list[float],
    policy: DecisionPolicy,
) -> dict[float, tuple[float | None, float | None]]:
    """fp_rate = P(human FAIL | judge PASS); ff_rate = P(human PASS | judge not PASS)."""
    pairs = pair_up(evals, humans, transcripts)
    out: dict[float, tuple[float | None, float | None]] = {}
    for c in cutoffs:
        jp = [p for p in pairs if judge_decision_at(p.judge, policy, c) == Decision.PASS]
        jn = [p for p in pairs if judge_decision_at(p.judge, policy, c) != Decision.PASS]
        fp = (
            sum(1 for p in jp if to_binary(p.human.overall_decision, "as_fail") == "FAIL") / len(jp)
            if jp
            else None
        )
        ff = (
            sum(1 for p in jn if p.human.overall_decision == Decision.PASS) / len(jn)
            if jn
            else None
        )
        out[c] = (fp, ff)
    return out
