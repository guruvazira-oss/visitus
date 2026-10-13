"""Illustrative operational-cost model. All monetary inputs are hypothetical assumptions.

Every evaluated call is assigned to exactly ONE review bucket (no double counting), in
priority order: REVIEW_REQUIRED > FAIL > borderline PASS > other PASS.

Let N = calls per month and p_rr, p_fail, p_bpass, p_opass the shares of evaluated calls in
each bucket (sum = 1), with review shares s_rr, s_fail, s_b, s_audit.

    reviewed_calls   = N * (p_rr*s_rr + p_fail*s_fail + p_bpass*s_b + p_opass*s_audit)
    review_hours     = reviewed_calls * review_minutes_per_call / 60
    review_expense   = reviewed_calls * review_cost_per_call
    capacity_short   = max(0, review_hours - reviewer_hours_capacity)
    undetected_fp    = N * (p_bpass*(1-s_b) + p_opass*(1-s_audit)) * fp_rate
                       where fp_rate = P(human FAIL | judge PASS) = 1 - PASS precision
    fp_exposure      = undetected_fp * false_pass_cost
    unreviewed_ff    = N * (p_fail*(1-s_fail) + p_rr*(1-s_rr)) * ff_rate
                       where ff_rate = P(human PASS | judge FAIL or REVIEW_REQUIRED)
    ff_cost          = unreviewed_ff * false_fail_cost
    total            = review_expense + fp_exposure + ff_cost + fixed_monthly_platform_cost

Error rates come from the human-labelled subset when available; otherwise they are explicit,
user-supplied assumptions. The lowest-cost threshold is never presented as a recommendation:
compliance requirements and risk tolerance take precedence over this illustrative model.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, fields
from typing import Any

import pandas as pd

from voice_eval.config import DecisionPolicy, load_experiment_defaults
from voice_eval.schemas import Decision, Evaluation

FORMULAS = __doc__


@dataclass
class BusinessAssumptions:
    calls_per_month: float = 50000
    review_cost_per_call: float = 6.5
    review_minutes_per_call: float = 9.0
    share_failed_reviewed: float = 0.5
    share_borderline_reviewed: float = 0.25
    share_review_required_reviewed: float = 1.0
    additional_random_audit_share: float = 0.02
    false_pass_cost: float = 120.0
    false_fail_cost: float = 15.0
    reviewer_hours_capacity_per_month: float = 1600
    fixed_monthly_platform_cost: float = 2500.0

    @classmethod
    def defaults(cls) -> BusinessAssumptions:
        cfg = load_experiment_defaults().get("business_impact", {})
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in cfg.items() if k in names})

    def validate(self) -> None:
        for name in (
            "share_failed_reviewed",
            "share_borderline_reviewed",
            "share_review_required_reviewed",
            "additional_random_audit_share",
        ):
            v = getattr(self, name)
            if not 0 <= v <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        for f in fields(self):
            if getattr(self, f.name) < 0:
                raise ValueError(f"{f.name} must be non-negative")


@dataclass
class BucketShares:
    p_review_required: float
    p_fail: float
    p_borderline_pass: float
    p_other_pass: float
    n_evaluated: int


def bucket_shares(
    decisions: list[Decision], scores: list[float | None], threshold: float, band: float
) -> BucketShares:
    n = len(decisions)
    if n == 0:
        return BucketShares(0, 0, 0, 0, 0)
    rr = sum(1 for d in decisions if d == Decision.REVIEW_REQUIRED)
    fail = sum(1 for d in decisions if d == Decision.FAIL)
    bpass = sum(
        1
        for d, s in zip(decisions, scores, strict=True)
        if d == Decision.PASS and s is not None and s < threshold + band
    )
    opass = n - rr - fail - bpass
    return BucketShares(rr / n, fail / n, bpass / n, opass / n, n)


def compute_impact(
    shares: BucketShares, a: BusinessAssumptions, fp_rate: float | None, ff_rate: float | None
) -> dict[str, Any]:
    a.validate()
    N = a.calls_per_month
    reviewed = N * (
        shares.p_review_required * a.share_review_required_reviewed
        + shares.p_fail * a.share_failed_reviewed
        + shares.p_borderline_pass * a.share_borderline_reviewed
        + shares.p_other_pass * a.additional_random_audit_share
    )
    hours = reviewed * a.review_minutes_per_call / 60
    expense = reviewed * a.review_cost_per_call
    unreviewed_pass = N * (
        shares.p_borderline_pass * (1 - a.share_borderline_reviewed)
        + shares.p_other_pass * (1 - a.additional_random_audit_share)
    )
    unreviewed_nonpass = N * (
        shares.p_fail * (1 - a.share_failed_reviewed)
        + shares.p_review_required * (1 - a.share_review_required_reviewed)
    )
    fp_exposure = unreviewed_pass * fp_rate * a.false_pass_cost if fp_rate is not None else math.nan
    ff_cost = unreviewed_nonpass * ff_rate * a.false_fail_cost if ff_rate is not None else math.nan
    total = (
        expense
        + a.fixed_monthly_platform_cost
        + (0 if math.isnan(fp_exposure) else fp_exposure)
        + (0 if math.isnan(ff_cost) else ff_cost)
    )
    return {
        "expected_passes": N * (shares.p_borderline_pass + shares.p_other_pass),
        "expected_failures": N * shares.p_fail,
        "expected_review_required": N * shares.p_review_required,
        "calls_sent_for_review": reviewed,
        "review_hours": hours,
        "review_expense": expense,
        "false_pass_exposure": fp_exposure,
        "false_fail_opportunity_cost": ff_cost,
        "fixed_platform_cost": a.fixed_monthly_platform_cost,
        "total_operational_cost": total,
        "total_is_partial": math.isnan(fp_exposure) or math.isnan(ff_cost),
        "capacity_shortfall_hours": max(0.0, hours - a.reviewer_hours_capacity_per_month),
        "fp_rate_used": fp_rate,
        "ff_rate_used": ff_rate,
    }


def impact_sweep(
    evals: list[Evaluation],
    cutoffs: list[float],
    policy: DecisionPolicy,
    a: BusinessAssumptions,
    rates_by_cutoff: dict[float, tuple[float | None, float | None]] | None = None,
    band: float = 5.0,
) -> pd.DataFrame:
    from voice_eval.analysis.agreement import judge_decision_at

    rows = []
    for c in cutoffs:
        decs = [judge_decision_at(e, policy, c) for e in evals]
        shares = bucket_shares(decs, [e.overall_score for e in evals], c, band)
        fp, ff = (rates_by_cutoff or {}).get(c, (None, None))
        r = compute_impact(shares, a, fp, ff)
        rows.append(
            {
                "cutoff": c,
                **{k: v for k, v in r.items() if k not in ("fp_rate_used", "ff_rate_used")},
                "fp_rate_used": fp,
                "ff_rate_used": ff,
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["lowest_illustrative_cost"] = (
            df["total_operational_cost"] == df["total_operational_cost"].min()
        )
    return df


def assumptions_table(a: BusinessAssumptions) -> pd.DataFrame:
    units = {
        "calls_per_month": "calls / month",
        "review_cost_per_call": "currency / reviewed call",
        "review_minutes_per_call": "minutes",
        "share_failed_reviewed": "fraction of FAIL calls",
        "share_borderline_reviewed": "fraction of borderline PASS calls",
        "share_review_required_reviewed": "fraction of REVIEW_REQUIRED calls",
        "additional_random_audit_share": "fraction of other PASS calls",
        "false_pass_cost": "currency / undetected false pass",
        "false_fail_cost": "currency / unreviewed false fail",
        "reviewer_hours_capacity_per_month": "hours / month",
        "fixed_monthly_platform_cost": "currency / month",
    }
    return pd.DataFrame(
        [
            {"assumption": k, "value": v, "unit": units[k], "source": "hypothetical (illustrative)"}
            for k, v in asdict(a).items()
        ]
    )
