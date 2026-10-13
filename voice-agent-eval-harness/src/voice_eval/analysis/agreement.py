"""Human-vs-judge agreement metrics.

Terminology (kept distinct on purpose):
* *agreement*  — how often two raters give the same label (exact / within-one / binary).
* *accuracy*   — not used: there is no ground truth, only a human reference.
* *reliability* — not claimed: one annotator cannot establish inter-annotator reliability.

Denominators (n) are reported with every metric. Binary metrics treat PASS as the positive
class, with the human label as reference:

    TP = judge PASS & human PASS      FP (false pass) = judge PASS & human FAIL
    FN (false fail) = judge FAIL & human PASS      TN = judge FAIL & human FAIL

    PASS precision = TP/(TP+FP)   PASS recall = TP/(TP+FN)
    FAIL precision = TN/(TN+FN)   FAIL recall = TN/(TN+FP)
    false-pass rate = FP/(FP+TN)  — share of human-FAIL calls the judge passed
    false-fail rate = FN/(FN+TP)  — share of human-PASS calls the judge failed
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from voice_eval.analysis.confidence_intervals import bootstrap_ci, wilson_interval
from voice_eval.analysis.confusion import (
    BINARY_LABELS,
    DECISION_LABELS,
    GATE_LABELS,
    ORDINAL_LABELS,
    confusion_frame,
)
from voice_eval.config import DecisionPolicy, load_experiment_defaults
from voice_eval.schemas import (
    DIMENSIONS,
    GATE_IDS,
    AdjudicationStatus,
    Decision,
    Evaluation,
    GateAssessment,
    HumanAnnotation,
    Transcript,
)
from voice_eval.scoring import decide, to_binary


def _stats_cfg() -> dict[str, Any]:
    return load_experiment_defaults().get("statistics", {})


def safe_kappa(
    a: Sequence, b: Sequence, weights: str | None = None, labels: Sequence | None = None
) -> float:
    """Cohen's kappa; NaN when undefined (e.g. both raters use a single identical label)."""
    if len(a) == 0:
        return math.nan
    if len(set(a) | set(b)) < 2:
        return math.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        k = cohen_kappa_score(
            list(a), list(b), weights=weights, labels=list(labels) if labels else None
        )
    return float(k) if not np.isnan(k) else math.nan


def proportion(k: int, n: int) -> dict[str, Any]:
    conf = _stats_cfg().get("confidence_level", 0.95)
    lo, hi = wilson_interval(k, n, conf)
    return {
        "k": k,
        "n": n,
        "value": (k / n) if n else math.nan,
        "ci_low": lo,
        "ci_high": hi,
        "ci_method": "wilson",
    }


def kappa_with_ci(
    a: Sequence, b: Sequence, weights: str | None = None, labels: Sequence | None = None
) -> dict[str, Any]:
    cfg = _stats_cfg()
    k = safe_kappa(a, b, weights, labels)
    lo, hi = (math.nan, math.nan)
    if not math.isnan(k):
        lo, hi = bootstrap_ci(
            lambda x, y: safe_kappa(x, y, weights, labels),
            [a, b],
            cfg.get("bootstrap_resamples", 2000),
            cfg.get("bootstrap_seed", 11),
            cfg.get("confidence_level", 0.95),
        )
    return {
        "value": k,
        "n": len(a),
        "ci_low": lo,
        "ci_high": hi,
        "ci_method": "bootstrap_percentile",
        "weights": weights or "none",
    }


# --------------------------------------------------------------------------------------


def judge_decision_at(
    e: Evaluation, policy: DecisionPolicy, threshold: float | None = None
) -> Decision:
    """Re-derive the judge-only decision (no human gate info) at a given threshold."""
    statuses = []
    for g in e.critical_gate_results:
        s = g.adjudication_status
        if g.human_assessment:  # strip any human adjudication: compare the judge alone
            s = {
                GateAssessment.VIOLATION: AdjudicationStatus.JUDGE_ALLEGED_UNCONFIRMED,
                GateAssessment.NO_VIOLATION: AdjudicationStatus.JUDGE_CLEARED_UNCONFIRMED,
                GateAssessment.UNCERTAIN: AdjudicationStatus.UNCERTAIN,
                GateAssessment.NOT_APPLICABLE: AdjudicationStatus.NOT_APPLICABLE,
            }[g.judge_assessment]
        statuses.append(s)
    return decide(
        e.overall_score,
        statuses,
        policy,
        threshold,
        injection_flagged=e.injection_screen_flag or e.injection_attempt_detected,
    ).decision


def judge_gate_label(a: GateAssessment) -> str:
    return {
        GateAssessment.VIOLATION: "CONFIRMED",
        GateAssessment.NO_VIOLATION: "NOT_PRESENT",
        GateAssessment.NOT_APPLICABLE: "NOT_PRESENT",
        GateAssessment.UNCERTAIN: "UNCERTAIN",
    }[a]


@dataclass
class Pair:
    transcript: Transcript
    human: HumanAnnotation
    judge: Evaluation


def pair_up(
    evals: list[Evaluation], humans: list[HumanAnnotation], transcripts: list[Transcript]
) -> list[Pair]:
    """Pair judge and human labels by transcript. With several annotators, the first
    (alphabetical annotator_id) is used as the reference and the choice is documented."""
    tmap = {t.transcript_id: t for t in transcripts}
    emap = {e.transcript_id: e for e in evals}
    hmap: dict[str, HumanAnnotation] = {}
    for h in sorted(humans, key=lambda x: (x.transcript_id, x.annotator_id)):
        hmap.setdefault(h.transcript_id, h)
    return [Pair(tmap[t], hmap[t], emap[t]) for t in sorted(hmap) if t in emap and t in tmap]


def ordinal_metrics(h: Sequence[int], j: Sequence[int]) -> dict[str, Any]:
    h_arr, j_arr = np.asarray(h), np.asarray(j)
    n = len(h_arr)
    diff = np.abs(h_arr - j_arr) if n else np.array([])
    cfg = _stats_cfg()
    mae = float(diff.mean()) if n else math.nan
    mae_ci = (
        bootstrap_ci(
            lambda a, b: float(np.abs(a - b).mean()),
            [h_arr, j_arr],
            cfg.get("bootstrap_resamples", 2000),
            cfg.get("bootstrap_seed", 11),
        )
        if n >= 2
        else (math.nan, math.nan)
    )
    return {
        "n": n,
        "exact_agreement": proportion(int((diff == 0).sum()), n),
        "within_one_agreement": proportion(int((diff <= 1).sum()), n),
        "mae": {
            "value": mae,
            "n": n,
            "ci_low": mae_ci[0],
            "ci_high": mae_ci[1],
            "ci_method": "bootstrap_percentile",
        },
        "kappa_unweighted": kappa_with_ci(list(h), list(j), None, ORDINAL_LABELS),
        "kappa_quadratic": kappa_with_ci(list(h), list(j), "quadratic", ORDINAL_LABELS),
        "mean_signed_difference_judge_minus_human": float((j_arr - h_arr).mean())
        if n
        else math.nan,
    }


def binary_metrics(human: Sequence[str], judge: Sequence[str]) -> dict[str, Any]:
    pairs = list(zip(human, judge, strict=True))
    tp = sum(1 for h, j in pairs if h == "PASS" and j == "PASS")
    fp = sum(1 for h, j in pairs if h == "FAIL" and j == "PASS")
    fn = sum(1 for h, j in pairs if h == "PASS" and j == "FAIL")
    tn = sum(1 for h, j in pairs if h == "FAIL" and j == "FAIL")
    n = len(pairs)

    def f1(p: float, r: float) -> float:
        return 2 * p * r / (p + r) if p + r and not (math.isnan(p) or math.isnan(r)) else math.nan

    pp, pr = proportion(tp, tp + fp), proportion(tp, tp + fn)
    fpp, fr = proportion(tn, tn + fn), proportion(tn, tn + fp)
    return {
        "n": n,
        "tp": tp,
        "fp_false_pass": fp,
        "fn_false_fail": fn,
        "tn": tn,
        "human_pass_prevalence": proportion(tp + fn, n),
        "raw_agreement": proportion(tp + tn, n),
        "pass_precision": pp,
        "pass_recall": pr,
        "fail_precision": fpp,
        "fail_recall": fr,
        "pass_f1": f1(pp["value"], pr["value"]),
        "fail_f1": f1(fpp["value"], fr["value"]),
        "false_pass_rate": proportion(fp, fp + tn),
        "false_fail_rate": proportion(fn, fn + tp),
        "false_pass_count": fp,
        "false_fail_count": fn,
        "kappa": kappa_with_ci(list(human), list(judge), None, BINARY_LABELS),
        "confusion": confusion_frame(human, judge, BINARY_LABELS),
    }


@dataclass
class AgreementResult:
    rubric_version: str
    n_pairs: int
    review_mapping: str
    threshold: float
    per_dimension: dict[str, dict[str, Any]] = field(default_factory=dict)
    applicability: dict[str, dict[str, Any]] = field(default_factory=dict)
    binary: dict[str, Any] = field(default_factory=dict)
    three_way: dict[str, Any] = field(default_factory=dict)
    gates: dict[str, dict[str, Any]] = field(default_factory=dict)
    per_scenario: pd.DataFrame = field(default_factory=pd.DataFrame)
    critical_split: dict[str, Any] = field(default_factory=dict)
    mapping_sensitivity: pd.DataFrame = field(default_factory=pd.DataFrame)
    excluded_review: int = 0
    human_self_consistency: dict[str, Any] = field(default_factory=dict)


def compute_agreement(
    evals: list[Evaluation],
    humans: list[HumanAnnotation],
    transcripts: list[Transcript],
    policy: DecisionPolicy,
    threshold: float | None = None,
) -> AgreementResult:
    cutoff = policy.pass_threshold if threshold is None else threshold
    pairs = pair_up(evals, humans, transcripts)
    res = AgreementResult(
        evals[0].rubric_version if evals else "?",
        len(pairs),
        policy.review_required_binary_mapping,
        cutoff,
    )

    for d in DIMENSIONS:
        both = [
            (p.human.dimension_scores[d], p.judge.dimension_scores[d])
            for p in pairs
            if p.human.dimension_scores[d] is not None and p.judge.dimension_scores[d] is not None
        ]
        res.per_dimension[d] = ordinal_metrics([x for x, _ in both], [y for _, y in both])
        app_agree = sum(
            1
            for p in pairs
            if p.human.dimension_applicability.get(d, True) == p.judge.dimension_applicability[d]
        )
        res.applicability[d] = proportion(app_agree, len(pairs))

    hd = [p.human.overall_decision for p in pairs]
    jd = [judge_decision_at(p.judge, policy, cutoff) for p in pairs]
    res.three_way = {
        "agreement": proportion(sum(1 for a, b in zip(hd, jd, strict=True) if a == b), len(pairs)),
        "kappa": kappa_with_ci([x.value for x in hd], [x.value for x in jd], None, DECISION_LABELS),
        "confusion": confusion_frame([x.value for x in hd], [x.value for x in jd], DECISION_LABELS),
    }

    def binarise(mapping: str) -> tuple[list[str], list[str], int]:
        hb, jb, excluded = [], [], 0
        for a, b in zip(hd, jd, strict=True):
            x, y = to_binary(a, mapping), to_binary(b, mapping)
            if x is None or y is None:
                excluded += 1
                continue
            hb.append(x)
            jb.append(y)
        return hb, jb, excluded

    hb, jb, res.excluded_review = binarise(policy.review_required_binary_mapping)
    res.binary = binary_metrics(hb, jb)

    rows = []
    for mapping in ("as_fail", "as_pass", "exclude"):
        x, y, exc = binarise(mapping)
        m = binary_metrics(x, y)
        rows.append(
            {
                "review_mapping": mapping,
                "n": m["n"],
                "excluded": exc,
                "raw_agreement": m["raw_agreement"]["value"],
                "false_pass": m["false_pass_count"],
                "false_fail": m["false_fail_count"],
                "kappa": m["kappa"]["value"],
            }
        )
    res.mapping_sensitivity = pd.DataFrame(rows)

    for g in GATE_IDS:
        h_lab = [p.human.gate_assessments[g].value for p in pairs]
        j_lab = [
            judge_gate_label(
                next(x for x in p.judge.critical_gate_results if x.gate_id == g).judge_assessment
            )
            for p in pairs
        ]
        missed = sum(
            1 for a, b in zip(h_lab, j_lab, strict=True) if a == "CONFIRMED" and b != "CONFIRMED"
        )
        over = sum(
            1 for a, b in zip(h_lab, j_lab, strict=True) if a != "CONFIRMED" and b == "CONFIRMED"
        )
        res.gates[g] = {
            "agreement": proportion(
                sum(1 for a, b in zip(h_lab, j_lab, strict=True) if a == b), len(pairs)
            ),
            "human_confirmed": h_lab.count("CONFIRMED"),
            "judge_alleged": j_lab.count("CONFIRMED"),
            "judge_missed_confirmed": missed,
            "judge_overcalled": over,
            "kappa": kappa_with_ci(h_lab, j_lab, None, GATE_LABELS),
            "confusion": confusion_frame(h_lab, j_lab, GATE_LABELS),
        }

    srows = []
    for cat in sorted({p.transcript.scenario_category.value for p in pairs}):
        sub = [
            (p, a, b)
            for p, a, b in zip(pairs, hd, jd, strict=True)
            if p.transcript.scenario_category.value == cat
        ]
        agree = sum(1 for _, a, b in sub if to_binary(a, "as_fail") == to_binary(b, "as_fail"))
        diffs = [
            abs(p.human.dimension_scores[d] - p.judge.dimension_scores[d])
            for p, _, _ in sub
            for d in DIMENSIONS
            if p.human.dimension_scores[d] is not None and p.judge.dimension_scores[d] is not None
        ]
        prop = proportion(agree, len(sub))
        srows.append(
            {
                "scenario_category": cat,
                "n": len(sub),
                "binary_agreement": prop["value"],
                "ci_low": prop["ci_low"],
                "ci_high": prop["ci_high"],
                "dimension_mae": float(np.mean(diffs)) if diffs else math.nan,
            }
        )
    res.per_scenario = pd.DataFrame(srows)

    crit = [
        i
        for i, p in enumerate(pairs)
        if any(v.value == "CONFIRMED" for v in p.human.gate_assessments.values())
    ]
    non = [i for i in range(len(pairs)) if i not in crit]
    for name, idx in (("human_confirmed_critical", crit), ("no_human_confirmed_critical", non)):
        x = [to_binary(hd[i], "as_fail") for i in idx]
        y = [to_binary(jd[i], "as_fail") for i in idx]
        m = binary_metrics(x, y)
        res.critical_split[name] = {
            "n": len(idx),
            "raw_agreement": m["raw_agreement"],
            "false_pass": m["false_pass_count"],
            "false_fail": m["false_fail_count"],
        }

    # Does each human's selected decision match what their own scores/gates imply?
    from voice_eval.rubric_loader import load_rubric
    from voice_eval.scoring import human_gate_status, weighted_score

    consistent = 0
    for p in pairs:
        rub = load_rubric(p.human.rubric_version)
        s = weighted_score(p.human.dimension_scores, rub.weights, p.human.dimension_applicability)
        implied = decide(
            s,
            [human_gate_status(v.value) for v in p.human.gate_assessments.values()],
            policy,
            cutoff,
        ).decision
        consistent += implied == p.human.overall_decision
    res.human_self_consistency = proportion(consistent, len(pairs))
    return res


def agreement_summary_rows(res: AgreementResult) -> pd.DataFrame:
    rows = []
    for d, m in res.per_dimension.items():
        rows.append(
            {
                "rubric_version": res.rubric_version,
                "dimension": d,
                "n": m["n"],
                "exact_agreement": m["exact_agreement"]["value"],
                "exact_ci_low": m["exact_agreement"]["ci_low"],
                "exact_ci_high": m["exact_agreement"]["ci_high"],
                "within_one": m["within_one_agreement"]["value"],
                "mae": m["mae"]["value"],
                "kappa_quadratic": m["kappa_quadratic"]["value"],
                "kappa_unweighted": m["kappa_unweighted"]["value"],
            }
        )
    return pd.DataFrame(rows)
