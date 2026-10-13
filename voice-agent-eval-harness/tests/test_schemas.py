import pytest
from pydantic import ValidationError

from voice_eval.schemas import (
    HumanAnnotation,
    JudgeDimensionResult,
    JudgeOutput,
    Transcript,
)


def test_dimension_score_bounds():
    with pytest.raises(ValidationError):
        JudgeDimensionResult(
            dimension="intent_capture",
            applicable=True,
            score=5,
            rationale="x",
            evidence=[],
            evidence_status="sufficient",
        )


def test_applicable_requires_score():
    with pytest.raises(ValidationError):
        JudgeDimensionResult(
            dimension="intent_capture",
            applicable=True,
            score=None,
            rationale="x",
            evidence=[],
            evidence_status="missing",
        )


def test_not_applicable_forbids_score():
    with pytest.raises(ValidationError):
        JudgeDimensionResult(
            dimension="objection_handling",
            applicable=False,
            score=2,
            rationale="x",
            evidence=[],
            evidence_status="sufficient",
        )


def test_judge_output_requires_all_dims(judge_output_factory):
    data = judge_output_factory("BFSI-A-001")
    data["dimensions"] = data["dimensions"][:4]
    with pytest.raises(ValidationError):
        JudgeOutput.model_validate(data)


def test_judge_output_requires_all_gates(judge_output_factory):
    data = judge_output_factory("BFSI-A-001")
    data["critical_gates"] = data["critical_gates"][:3]
    with pytest.raises(ValidationError):
        JudgeOutput.model_validate(data)


def test_transcript_rejects_unknown_gate(tiny_transcript):
    d = tiny_transcript.model_dump(mode="json")
    d["expected_critical_violations"] = ["G9_FAKE"]
    with pytest.raises(ValidationError):
        Transcript.model_validate(d)


def test_transcript_rejects_extra_field(tiny_transcript):
    d = tiny_transcript.model_dump(mode="json")
    d["surprise"] = 1
    with pytest.raises(ValidationError):
        Transcript.model_validate(d)


def test_human_annotation_requires_all_dims():
    with pytest.raises(ValidationError):
        HumanAnnotation(
            annotation_id="A",
            transcript_id="BFSI-A-001",
            annotator_id="u",
            rubric_version="v1",
            dimension_scores={"intent_capture": 3},
            dimension_applicability={},
            gate_assessments={},
            overall_decision="PASS",
        )
