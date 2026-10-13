"""Disagreement registers.

Two registers with different references, never mixed:

* ``human_disagreement_register`` — judge vs independent human labels (the research result).
* ``spec_conformance_register``   — judge vs the generator's synthetic test specification
  (expected gate violations and outcome band). This is a *dataset/judge sanity check*, not
  human agreement, and the synthetic spec is not ground truth.

Root causes are auto-*suggested* from observable signals and marked ``suggested_auto``.
A human adjudicator can override them in ``data/disagreement_adjudications.csv``; those
overrides are merged by ``record_id`` and survive regeneration.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from voice_eval.analysis.agreement import judge_decision_at, judge_gate_label, pair_up
from voice_eval.config import DATA_DIR, DecisionPolicy
from voice_eval.schemas import DIMENSIONS, Evaluation, HumanAnnotation, Transcript
from voice_eval.scoring import to_binary

ROOT_CAUSES = [
    "AMBIGUOUS_ANCHOR",
    "MISSING_EVIDENCE",
    "UNSUPPORTED_JUDGE_INFERENCE",
    "OVERLY_STRICT_SCORING",
    "OVERLY_LENIENT_SCORING",
    "INCORRECT_APPLICABILITY",
    "TONE_OUTCOME_CONFUSION",
    "INCORRECT_CRITICAL_GATE_CLASSIFICATION",
    "HUMAN_ANNOTATION_UNCERTAINTY",
    "DATASET_AMBIGUITY",
    "UNCLASSIFIED",
]
CHANGE_STATUSES = [
    "proposed",
    "accepted",
    "implemented_in_v2",
    "implemented_in_v3",
    "rejected",
    "none",
]
ADJUDICATIONS_PATH = DATA_DIR / "disagreement_adjudications.csv"

REGISTER_COLUMNS = [
    "record_id",
    "reference",
    "transcript_id",
    "scenario_category",
    "dimension",
    "human_score",
    "judge_score",
    "score_difference",
    "human_rationale",
    "judge_rationale",
    "relevant_evidence",
    "root_cause_category",
    "root_cause_status",
    "proposed_rubric_change",
    "change_status",
    "final_adjudication",
    "rubric_version",
]


def _suggest(
    diff: int | None, judge_app: bool, human_app: bool, e: Evaluation, dim: str, t: Transcript
) -> str:
    if judge_app != human_app:
        return "INCORRECT_APPLICABILITY"
    if t.ambiguity_notes:
        return "DATASET_AMBIGUITY"
    if (
        e.evidence_status_by_dimension.get(dim)
        and e.evidence_status_by_dimension[dim].value != "sufficient"
    ):
        return "MISSING_EVIDENCE"
    if any(i.startswith(dim) for i in e.grounding_issues):
        return "UNSUPPORTED_JUDGE_INFERENCE"
    if diff is not None and diff >= 2:
        return "OVERLY_LENIENT_SCORING"
    if diff is not None and diff <= -2:
        return "OVERLY_STRICT_SCORING"
    return "AMBIGUOUS_ANCHOR"


def _evidence_text(e: Evaluation, dim: str) -> str:
    return " | ".join(
        f"{x.turn_id}: {x.quote[:140]}" for x in e.evidence_by_dimension.get(dim, [])[:3]
    )


def human_disagreement_register(
    evals: list[Evaluation],
    humans: list[HumanAnnotation],
    transcripts: list[Transcript],
    policy: DecisionPolicy,
) -> pd.DataFrame:
    rows = []
    for p in pair_up(evals, humans, transcripts):
        e, h, t = p.judge, p.human, p.transcript
        for d in DIMENSIONS:
            hs, js = h.dimension_scores[d], e.dimension_scores[d]
            happ, japp = h.dimension_applicability.get(d, True), e.dimension_applicability[d]
            if hs == js and happ == japp:
                continue
            diff = (js - hs) if (hs is not None and js is not None) else None
            rows.append(
                {
                    "record_id": f"{e.rubric_version}:{t.transcript_id}:{d}",
                    "reference": "human",
                    "transcript_id": t.transcript_id,
                    "scenario_category": t.scenario_category.value,
                    "dimension": d,
                    "human_score": hs,
                    "judge_score": js,
                    "score_difference": diff,
                    "human_rationale": h.dimension_rationales.get(d, ""),
                    "judge_rationale": e.dimension_rationales[d],
                    "relevant_evidence": _evidence_text(e, d),
                    "root_cause_category": _suggest(diff, japp, happ, e, d, t),
                    "root_cause_status": "suggested_auto",
                    "proposed_rubric_change": "",
                    "change_status": "proposed",
                    "final_adjudication": "",
                    "rubric_version": e.rubric_version,
                }
            )
        for g in e.critical_gate_results:
            hl, jl = h.gate_assessments[g.gate_id].value, judge_gate_label(g.judge_assessment)
            if hl == jl:
                continue
            rows.append(
                {
                    "record_id": f"{e.rubric_version}:{t.transcript_id}:{g.gate_id}",
                    "reference": "human",
                    "transcript_id": t.transcript_id,
                    "scenario_category": t.scenario_category.value,
                    "dimension": g.gate_id,
                    "human_score": hl,
                    "judge_score": jl,
                    "score_difference": None,
                    "human_rationale": h.notes,
                    "judge_rationale": g.rationale,
                    "relevant_evidence": " | ".join(
                        f"{x.turn_id}: {x.quote[:140]}" for x in g.evidence[:3]
                    ),
                    "root_cause_category": "INCORRECT_CRITICAL_GATE_CLASSIFICATION"
                    if hl != "UNCERTAIN"
                    else "HUMAN_ANNOTATION_UNCERTAINTY",
                    "root_cause_status": "suggested_auto",
                    "proposed_rubric_change": "",
                    "change_status": "proposed",
                    "final_adjudication": "",
                    "rubric_version": e.rubric_version,
                }
            )
        hd, jd = h.overall_decision, judge_decision_at(e, policy)
        if hd != jd:
            rows.append(
                {
                    "record_id": f"{e.rubric_version}:{t.transcript_id}:DECISION",
                    "reference": "human",
                    "transcript_id": t.transcript_id,
                    "scenario_category": t.scenario_category.value,
                    "dimension": "OVERALL_DECISION",
                    "human_score": hd.value,
                    "judge_score": jd.value,
                    "score_difference": None,
                    "human_rationale": h.notes,
                    "judge_rationale": "; ".join(e.decision_reasons),
                    "relevant_evidence": f"judge overall {e.overall_score}",
                    "root_cause_category": "OVERLY_LENIENT_SCORING"
                    if to_binary(jd, "as_fail") == "PASS"
                    else "OVERLY_STRICT_SCORING",
                    "root_cause_status": "suggested_auto",
                    "proposed_rubric_change": "",
                    "change_status": "proposed",
                    "final_adjudication": "",
                    "rubric_version": e.rubric_version,
                }
            )
    return apply_adjudications(pd.DataFrame(rows, columns=REGISTER_COLUMNS))


def spec_conformance_register(
    evals: list[Evaluation], transcripts: list[Transcript], policy: DecisionPolicy
) -> pd.DataFrame:
    """Judge vs synthetic test specification. NOT human agreement."""
    tmap = {t.transcript_id: t for t in transcripts}
    rows = []
    for e in evals:
        t = tmap.get(e.transcript_id)
        if t is None:
            continue
        expected = set(t.expected_critical_violations)
        for g in e.critical_gate_results:
            alleged = g.judge_assessment.value
            exp = g.gate_id in expected
            if (exp and alleged == "VIOLATION") or (
                not exp and alleged in ("NO_VIOLATION", "NOT_APPLICABLE")
            ):
                continue
            cause = (
                "DATASET_AMBIGUITY"
                if t.ambiguity_notes
                else "INCORRECT_CRITICAL_GATE_CLASSIFICATION"
                if alleged != "UNCERTAIN"
                else "AMBIGUOUS_ANCHOR"
            )
            rows.append(
                {
                    "record_id": f"spec:{e.rubric_version}:{t.transcript_id}:{g.gate_id}",
                    "reference": "synthetic_spec",
                    "transcript_id": t.transcript_id,
                    "scenario_category": t.scenario_category.value,
                    "dimension": g.gate_id,
                    "human_score": "EXPECTED_VIOLATION" if exp else "NOT_EXPECTED",
                    "judge_score": alleged,
                    "score_difference": None,
                    "human_rationale": "; ".join(t.ambiguity_notes) or "synthetic specification",
                    "judge_rationale": g.rationale,
                    "relevant_evidence": " | ".join(
                        f"{x.turn_id}: {x.quote[:140]}" for x in g.evidence[:3]
                    ),
                    "root_cause_category": cause,
                    "root_cause_status": "suggested_auto",
                    "proposed_rubric_change": "",
                    "change_status": "proposed",
                    "final_adjudication": "",
                    "rubric_version": e.rubric_version,
                }
            )
        dec = judge_decision_at(e, policy)
        band = t.expected_outcome_band
        mismatch = (band == "PASS_EXPECTED" and dec != dec.PASS) or (
            band == "FAIL_EXPECTED" and dec == dec.PASS
        )
        if mismatch:
            low = [
                d
                for d in DIMENSIONS
                if e.dimension_scores[d] is not None and e.dimension_scores[d] <= 2
            ]
            rows.append(
                {
                    "record_id": f"spec:{e.rubric_version}:{t.transcript_id}:DECISION",
                    "reference": "synthetic_spec",
                    "transcript_id": t.transcript_id,
                    "scenario_category": t.scenario_category.value,
                    "dimension": "OVERALL_DECISION",
                    "human_score": band,
                    "judge_score": dec.value,
                    "score_difference": None,
                    "human_rationale": f"tier={t.agent_quality_tier}",
                    "judge_rationale": "; ".join(e.decision_reasons),
                    "relevant_evidence": f"overall {e.overall_score}; low dimensions: {', '.join(low) or 'none'}",
                    "root_cause_category": "OVERLY_STRICT_SCORING"
                    if band == "PASS_EXPECTED"
                    else "OVERLY_LENIENT_SCORING",
                    "root_cause_status": "suggested_auto",
                    "proposed_rubric_change": "",
                    "change_status": "proposed",
                    "final_adjudication": "",
                    "rubric_version": e.rubric_version,
                }
            )
    return apply_adjudications(pd.DataFrame(rows, columns=REGISTER_COLUMNS))


def apply_adjudications(df: pd.DataFrame, path: Path = ADJUDICATIONS_PATH) -> pd.DataFrame:
    if df.empty or not path.exists():
        return df
    adj = pd.read_csv(path, dtype=str).fillna("")
    editable = [
        "root_cause_category",
        "proposed_rubric_change",
        "change_status",
        "final_adjudication",
    ]
    adj = adj[[c for c in ["record_id", *editable] if c in adj.columns]].set_index("record_id")
    df = df.copy()
    for i, rid in df["record_id"].items():
        if rid in adj.index:
            for c in adj.columns:
                if adj.at[rid, c]:
                    df.at[i, c] = adj.at[rid, c]
            df.at[i, "root_cause_status"] = "human_adjudicated"
    return df


def spec_conformance_summary(
    evals: list[Evaluation], transcripts: list[Transcript], policy: DecisionPolicy
) -> dict:
    """Gate-level confusion against expected violations and decision mix per quality tier."""
    tmap = {t.transcript_id: t for t in transcripts}
    gate_rows = []
    from voice_eval.schemas import GATE_IDS

    for gid in GATE_IDS:
        tp = fp = fn = tn = unc = 0
        for e in evals:
            t = tmap[e.transcript_id]
            a = next(g for g in e.critical_gate_results if g.gate_id == gid).judge_assessment.value
            exp = gid in t.expected_critical_violations
            if a == "UNCERTAIN":
                unc += 1
            elif exp and a == "VIOLATION":
                tp += 1
            elif exp:
                fn += 1
            elif a == "VIOLATION":
                fp += 1
            else:
                tn += 1
        gate_rows.append(
            {
                "gate_id": gid,
                "expected_and_alleged": tp,
                "alleged_not_expected": fp,
                "expected_not_alleged": fn,
                "neither": tn,
                "uncertain": unc,
            }
        )
    tier_rows = []
    for tier in ("exemplary", "adequate", "deficient", "critical"):
        sub = [e for e in evals if tmap[e.transcript_id].agent_quality_tier == tier]
        decs = [judge_decision_at(e, policy).value for e in sub]
        scores = [e.overall_score for e in sub if e.overall_score is not None]
        tier_rows.append(
            {
                "agent_quality_tier": tier,
                "n": len(sub),
                "mean_score": round(sum(scores) / len(scores), 1) if scores else None,
                "PASS": decs.count("PASS"),
                "FAIL": decs.count("FAIL"),
                "REVIEW_REQUIRED": decs.count("REVIEW_REQUIRED"),
            }
        )
    return {"gates": pd.DataFrame(gate_rows), "tiers": pd.DataFrame(tier_rows)}
