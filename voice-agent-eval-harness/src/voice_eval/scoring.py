"""The single shared implementation of the weighted score and operational decision.

Every component (judge evaluator, human annotation analysis, threshold sweep, dashboard)
computes scores and decisions through this module. Judge-claimed totals are never used.

Formula
-------
For applicable dimensions A with weights w_d and integer scores s_d in [0, 4]::

    overall = 100 * sum_{d in A} w_d * (s_d / 4) / sum_{d in A} w_d

Weights are renormalised over applicable dimensions only. If no dimension is applicable
the score is undefined (None) and the decision is REVIEW_REQUIRED.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from voice_eval.config import DecisionPolicy
from voice_eval.schemas import AdjudicationStatus, Decision


class ScoringError(ValueError):
    pass


def weighted_score(
    scores: Mapping[str, int | None],
    weights: Mapping[str, float],
    applicability: Mapping[str, bool] | None = None,
) -> float | None:
    """Return the 0-100 weighted score over applicable dimensions."""
    applicability = applicability or {}
    num = 0.0
    den = 0.0
    for dim, weight in weights.items():
        applicable = applicability.get(dim, scores.get(dim) is not None)
        score = scores.get(dim)
        if not applicable:
            continue
        if score is None:
            raise ScoringError(f"dimension {dim!r} is applicable but has no score")
        if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 4:
            raise ScoringError(f"dimension {dim!r} score must be an integer 0-4, got {score!r}")
        num += weight * (score / 4.0)
        den += weight
    if den == 0:
        return None
    return round(100.0 * num / den, 4)


@dataclass(frozen=True)
class DecisionResult:
    decision: Decision
    reasons: list[str]


_BLOCKING_REVIEW = {AdjudicationStatus.UNCERTAIN, AdjudicationStatus.HUMAN_UNCERTAIN}


def decide(
    overall_score: float | None,
    gate_statuses: Iterable[AdjudicationStatus],
    policy: DecisionPolicy,
    threshold: float | None = None,
    injection_flagged: bool = False,
) -> DecisionResult:
    """Combine score, threshold and critical-gate adjudication into PASS/FAIL/REVIEW_REQUIRED.

    Precedence:
      1. Any human-confirmed critical violation            -> FAIL (overrides score)
      2. Judge-alleged, unconfirmed violation               -> REVIEW_REQUIRED (or FAIL if
                                                               policy.unconfirmed_gate_policy == "fail")
      3. Any uncertain / conflicting gate                   -> REVIEW_REQUIRED
      4. Undefined score                                    -> REVIEW_REQUIRED
      5. score >= threshold                                 -> PASS, else FAIL
      6. PASS on an injection-flagged transcript            -> REVIEW_REQUIRED (if enabled)
    """
    cutoff = policy.pass_threshold if threshold is None else threshold
    statuses = list(gate_statuses)
    reasons: list[str] = []

    if AdjudicationStatus.CONFIRMED_VIOLATION in statuses:
        n = statuses.count(AdjudicationStatus.CONFIRMED_VIOLATION)
        return DecisionResult(
            Decision.FAIL, [f"{n} confirmed critical gate violation(s) override the score"]
        )

    alleged = statuses.count(AdjudicationStatus.JUDGE_ALLEGED_UNCONFIRMED)
    if alleged:
        if policy.unconfirmed_gate_policy == "fail":
            return DecisionResult(
                Decision.FAIL,
                [
                    f"{alleged} judge-alleged gate violation(s) treated as confirmed (benchmark policy 'fail')"
                ],
            )
        return DecisionResult(
            Decision.REVIEW_REQUIRED,
            [f"{alleged} judge-alleged gate violation(s) awaiting human adjudication"],
        )

    uncertain = sum(1 for s in statuses if s in _BLOCKING_REVIEW)
    if uncertain:
        return DecisionResult(
            Decision.REVIEW_REQUIRED, [f"{uncertain} gate(s) uncertain or contradictory"]
        )

    if overall_score is None:
        return DecisionResult(
            Decision.REVIEW_REQUIRED, ["no applicable dimensions; score undefined"]
        )

    if overall_score >= cutoff:
        decision = Decision.PASS
        reasons.append(f"score {overall_score:.1f} >= threshold {cutoff:g}")
    else:
        decision = Decision.FAIL
        reasons.append(f"score {overall_score:.1f} < threshold {cutoff:g}")

    if (
        decision == Decision.PASS
        and injection_flagged
        and policy.route_injection_flagged_passes_to_review
    ):
        return DecisionResult(
            Decision.REVIEW_REQUIRED,
            [*reasons, "prompt-injection attempt detected in transcript; PASS routed to review"],
        )
    return DecisionResult(decision, reasons)


def to_binary(decision: Decision | str, mapping: str) -> str | None:
    """Map a three-way decision onto PASS/FAIL for benchmark comparison.

    Returns None when the record should be excluded (mapping == "exclude").
    """
    d = Decision(decision)
    if d == Decision.REVIEW_REQUIRED:
        if mapping == "as_fail":
            return "FAIL"
        if mapping == "as_pass":
            return "PASS"
        if mapping == "exclude":
            return None
        raise ValueError(f"unknown review mapping {mapping!r}")
    return d.value


def human_gate_status(value: str | None) -> AdjudicationStatus | None:
    return {
        "CONFIRMED": AdjudicationStatus.CONFIRMED_VIOLATION,
        "NOT_PRESENT": AdjudicationStatus.CONFIRMED_NO_VIOLATION,
        "UNCERTAIN": AdjudicationStatus.HUMAN_UNCERTAIN,
        None: None,
    }[value]
