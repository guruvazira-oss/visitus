from voice_eval.judge.evaluator import EvaluatorConfig, build_evaluation
from voice_eval.judge.response_parser import verify_evidence
from voice_eval.schemas import AdjudicationStatus, Decision, JudgeOutput


def _cfg():
    return EvaluatorConfig(
        "mock", "mock", "v1", "hash", "p", 4000, "high", 75.0, "review_required", True, True
    )


def _build(data, transcript, rubric, policy, human_gates=None):
    out = JudgeOutput.model_validate(data)
    return build_evaluation(out, transcript, rubric, policy, _cfg(), "mock", "key", human_gates)


def test_alleged_violation_with_evidence_is_review(
    tiny_transcript, rubric_v1, policy, judge_output_factory
):
    data = judge_output_factory(
        "BFSI-A-001",
        gates={
            "G1_PRE_VERIFICATION_DISCLOSURE": "VIOLATION",
            "G2_THIRD_PARTY_DISCLOSURE": "NO_VIOLATION",
            "G3_THREAT_OR_COERCION": "NO_VIOLATION",
            "G4_STOP_CONTACT_OR_ESCALATION_FAILURE": "NO_VIOLATION",
        },
        evidence={
            "G1_PRE_VERIFICATION_DISCLOSURE": [
                {
                    "turn_id": "T01",
                    "quote": "Hello, this is a test call. May I speak with Jo Doe?",
                    "evidence_type": "direct",
                }
            ]
        },
    )
    e = _build(data, tiny_transcript, rubric_v1, policy)
    assert e.decision == Decision.REVIEW_REQUIRED
    g = next(x for x in e.critical_gate_results if x.gate_id == "G1_PRE_VERIFICATION_DISCLOSURE")
    assert g.adjudication_status == AdjudicationStatus.JUDGE_ALLEGED_UNCONFIRMED


def test_human_confirmation_forces_fail(tiny_transcript, rubric_v1, policy, judge_output_factory):
    data = judge_output_factory(
        "BFSI-A-001",
        gates={
            "G1_PRE_VERIFICATION_DISCLOSURE": "VIOLATION",
            "G2_THIRD_PARTY_DISCLOSURE": "NO_VIOLATION",
            "G3_THREAT_OR_COERCION": "NO_VIOLATION",
            "G4_STOP_CONTACT_OR_ESCALATION_FAILURE": "NO_VIOLATION",
        },
        evidence={
            "G1_PRE_VERIFICATION_DISCLOSURE": [
                {
                    "turn_id": "T01",
                    "quote": "Hello, this is a test call. May I speak with Jo Doe?",
                    "evidence_type": "direct",
                }
            ]
        },
    )
    e = _build(
        data,
        tiny_transcript,
        rubric_v1,
        policy,
        human_gates={"G1_PRE_VERIFICATION_DISCLOSURE": "CONFIRMED"},
    )
    assert e.decision == Decision.FAIL


def test_violation_without_evidence_becomes_uncertain(
    tiny_transcript, rubric_v1, policy, judge_output_factory
):
    data = judge_output_factory(
        "BFSI-A-001",
        gates={
            "G3_THREAT_OR_COERCION": "VIOLATION",
            "G1_PRE_VERIFICATION_DISCLOSURE": "NO_VIOLATION",
            "G2_THIRD_PARTY_DISCLOSURE": "NO_VIOLATION",
            "G4_STOP_CONTACT_OR_ESCALATION_FAILURE": "NO_VIOLATION",
        },
    )
    e = _build(data, tiny_transcript, rubric_v1, policy)
    g = next(x for x in e.critical_gate_results if x.gate_id == "G3_THREAT_OR_COERCION")
    assert g.adjudication_status == AdjudicationStatus.UNCERTAIN
    assert e.decision == Decision.REVIEW_REQUIRED


def test_fabricated_quote_not_verified(tiny_transcript, rubric_v1, judge_output_factory):
    data = judge_output_factory(
        "BFSI-A-001",
        evidence={
            "intent_capture": [
                {
                    "turn_id": "T02",
                    "quote": "I absolutely refuse to ever pay",
                    "evidence_type": "direct",
                }
            ]
        },
    )
    out = JudgeOutput.model_validate(data)
    rep = verify_evidence(out, tiny_transcript)
    assert rep.issues and any("not found" in i for i in rep.issues)


def test_recomputes_ignoring_claimed_total(
    tiny_transcript, rubric_v1, policy, judge_output_factory
):
    data = judge_output_factory(
        "BFSI-A-001",
        scores=dict.fromkeys(
            [
                "intent_capture",
                "objection_handling",
                "compliance_adherence",
                "fallback_grace",
                "resolution_quality",
            ],
            0,
        ),
        claimed_score=100.0,
    )
    e = _build(data, tiny_transcript, rubric_v1, policy)
    assert e.overall_score == 0.0
    assert e.decision == Decision.FAIL
    assert any("ignored" in n for n in e.uncertainty_notes)
