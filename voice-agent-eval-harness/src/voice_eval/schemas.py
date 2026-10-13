"""Explicit, strictly validated data contracts for the harness.

Three families of records are kept deliberately separate:

* ``Transcript`` — the frozen synthetic benchmark artifact.
* ``JudgeOutput`` / ``Evaluation`` — what a judge returned, and the record we store after
  Python has re-validated it and recomputed the score and decision.
* ``HumanAnnotation`` — independent human labels, stored apart from judge outputs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DIMENSIONS: tuple[str, ...] = (
    "intent_capture",
    "objection_handling",
    "compliance_adherence",
    "fallback_grace",
    "resolution_quality",
)

GATE_IDS: tuple[str, ...] = (
    "G1_PRE_VERIFICATION_DISCLOSURE",
    "G2_THIRD_PARTY_DISCLOSURE",
    "G3_THREAT_OR_COERCION",
    "G4_STOP_CONTACT_OR_ESCALATION_FAILURE",
)

Score = Annotated[int, Field(ge=0, le=4)]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=False, frozen=False)


# --------------------------------------------------------------------------------------
# Dataset
# --------------------------------------------------------------------------------------


class ScenarioCategory(StrEnum):
    FIRST_TIME_DEFAULTER = "FIRST_TIME_DEFAULTER"
    REPEAT_DELINQUENT = "REPEAT_DELINQUENT"
    WRONG_NUMBER_OR_IDENTITY_MISMATCH = "WRONG_NUMBER_OR_IDENTITY_MISMATCH"
    PAYMENT_DISPUTE = "PAYMENT_DISPUTE"
    HOSTILE_OR_DISTRESSED = "HOSTILE_OR_DISTRESSED"


CATEGORY_CODES: dict[ScenarioCategory, str] = {
    ScenarioCategory.FIRST_TIME_DEFAULTER: "A",
    ScenarioCategory.REPEAT_DELINQUENT: "B",
    ScenarioCategory.WRONG_NUMBER_OR_IDENTITY_MISMATCH: "C",
    ScenarioCategory.PAYMENT_DISPUTE: "D",
    ScenarioCategory.HOSTILE_OR_DISTRESSED: "E",
}


class Speaker(StrEnum):
    AGENT = "agent"
    CONTACT = "contact"  # the person who answered: borrower or a third party


class ResolutionType(StrEnum):
    PAYMENT_COMMITMENT = "PAYMENT_COMMITMENT"
    PAYMENT_PLAN_REFERRAL = "PAYMENT_PLAN_REFERRAL"
    CALLBACK_SCHEDULED = "CALLBACK_SCHEDULED"
    DISPUTE_REFERRAL = "DISPUTE_REFERRAL"
    WRONG_NUMBER_CLOSED = "WRONG_NUMBER_CLOSED"
    ESCALATED_TO_SUPERVISOR = "ESCALATED_TO_SUPERVISOR"
    SUPPORT_REFERRAL = "SUPPORT_REFERRAL"
    SAFE_TERMINATION = "SAFE_TERMINATION"
    UNRESOLVED_ROUTED_FOR_REVIEW = "UNRESOLVED_ROUTED_FOR_REVIEW"


class Turn(StrictModel):
    turn_id: str = Field(pattern=r"^T\d{2,3}$")
    speaker: Speaker
    text: str = Field(min_length=1)


class BorrowerProfile(StrictModel):
    """Entirely fictional borrower attributes. No real customer data."""

    full_name: str
    date_of_birth: str
    postcode: str
    product_type: str
    outstanding_amount: float = Field(ge=0)
    instalment_amount: float = Field(ge=0)
    currency: str
    days_past_due: int = Field(ge=0)
    prior_missed_commitments: int = Field(ge=0)
    communication_style: str
    vulnerability_indicator: bool = False


class Transcript(StrictModel):
    transcript_id: str = Field(pattern=r"^BFSI-[A-E]-\d{3}$")
    scenario_category: ScenarioCategory
    scenario_subtype: str
    scenario_description: str
    difficulty_level: Literal["easy", "medium", "hard"]
    synthetic_borrower_profile: BorrowerProfile
    conversation_turns: list[Turn] = Field(min_length=4)
    intended_agent_behavior: list[str] = Field(min_length=1)
    expected_resolution_type: ResolutionType
    expected_critical_violations: list[str]
    agent_quality_tier: Literal["exemplary", "adequate", "deficient", "critical"]
    expected_outcome_band: Literal["PASS_EXPECTED", "BORDERLINE", "FAIL_EXPECTED"]
    modifiers: list[str] = Field(default_factory=list)
    ambiguity_notes: list[str] = Field(default_factory=list)
    dataset_version: str
    generation_seed: int

    @field_validator("expected_critical_violations")
    @classmethod
    def _known_gates(cls, v: list[str]) -> list[str]:
        unknown = [g for g in v if g not in GATE_IDS]
        if unknown:
            raise ValueError(f"unknown gate ids: {unknown}")
        return v

    @model_validator(mode="after")
    def _unique_turn_ids(self) -> Transcript:
        ids = [t.turn_id for t in self.conversation_turns]
        if len(ids) != len(set(ids)):
            raise ValueError("turn ids must be unique within a transcript")
        return self

    def turn_map(self) -> dict[str, Turn]:
        return {t.turn_id: t for t in self.conversation_turns}


# --------------------------------------------------------------------------------------
# Judge output (what the model must return) — strict schema
# --------------------------------------------------------------------------------------


class EvidenceType(StrEnum):
    DIRECT = "direct"
    INFERENCE = "inference"


class EvidenceItem(StrictModel):
    turn_id: str = Field(pattern=r"^T\d{2,3}$")
    quote: str = Field(min_length=1, max_length=600)
    evidence_type: EvidenceType = EvidenceType.DIRECT


class EvidenceStatus(StrEnum):
    SUFFICIENT = "sufficient"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"


class JudgeDimensionResult(StrictModel):
    dimension: Literal[
        "intent_capture",
        "objection_handling",
        "compliance_adherence",
        "fallback_grace",
        "resolution_quality",
    ]
    applicable: bool
    score: Score | None
    rationale: str = Field(min_length=1)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    evidence_status: EvidenceStatus

    @model_validator(mode="after")
    def _score_matches_applicability(self) -> JudgeDimensionResult:
        if self.applicable and self.score is None:
            raise ValueError(f"{self.dimension}: applicable dimension requires an integer score")
        if not self.applicable and self.score is not None:
            raise ValueError(f"{self.dimension}: non-applicable dimension must have null score")
        return self


class GateAssessment(StrEnum):
    VIOLATION = "VIOLATION"
    NO_VIOLATION = "NO_VIOLATION"
    UNCERTAIN = "UNCERTAIN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class JudgeGateResult(StrictModel):
    gate_id: Literal[
        "G1_PRE_VERIFICATION_DISCLOSURE",
        "G2_THIRD_PARTY_DISCLOSURE",
        "G3_THREAT_OR_COERCION",
        "G4_STOP_CONTACT_OR_ESCALATION_FAILURE",
    ]
    assessment: GateAssessment
    rationale: str = Field(min_length=1)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class JudgeOutput(StrictModel):
    """The structured object a judge must return. Totals it claims are NOT trusted."""

    transcript_id: str
    dimensions: list[JudgeDimensionResult]
    critical_gates: list[JudgeGateResult]
    claimed_overall_score: float | None = None
    claimed_decision: str | None = None
    uncertainty_notes: list[str] = Field(default_factory=list)
    injection_attempt_detected: bool = False

    @model_validator(mode="after")
    def _complete(self) -> JudgeOutput:
        dims = [d.dimension for d in self.dimensions]
        if sorted(dims) != sorted(DIMENSIONS):
            raise ValueError(f"judge must return each dimension exactly once, got {dims}")
        gates = [g.gate_id for g in self.critical_gates]
        if sorted(gates) != sorted(GATE_IDS):
            raise ValueError(f"judge must return each gate exactly once, got {gates}")
        return self


# --------------------------------------------------------------------------------------
# Stored evaluation record (after Python re-validation and recomputation)
# --------------------------------------------------------------------------------------


class Decision(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class AdjudicationStatus(StrEnum):
    CONFIRMED_VIOLATION = "CONFIRMED_VIOLATION"  # human-confirmed
    CONFIRMED_NO_VIOLATION = "CONFIRMED_NO_VIOLATION"  # human-confirmed
    HUMAN_UNCERTAIN = "HUMAN_UNCERTAIN"
    JUDGE_ALLEGED_UNCONFIRMED = "JUDGE_ALLEGED_UNCONFIRMED"
    JUDGE_CLEARED_UNCONFIRMED = "JUDGE_CLEARED_UNCONFIRMED"
    UNCERTAIN = "UNCERTAIN"  # judge uncertain, or judge vs screen conflict, or bad evidence
    NOT_APPLICABLE = "NOT_APPLICABLE"


class GateRecord(StrictModel):
    gate_id: str
    judge_assessment: GateAssessment
    screen_flag: bool | None = None  # deterministic lexical screen result, if run
    human_assessment: Literal["CONFIRMED", "NOT_PRESENT", "UNCERTAIN"] | None = None
    adjudication_status: AdjudicationStatus
    rationale: str = ""
    evidence: list[EvidenceItem] = Field(default_factory=list)
    evidence_verified: bool = True
    notes: list[str] = Field(default_factory=list)


class Evaluation(StrictModel):
    transcript_id: str
    dataset_version: str
    rubric_version: str
    judge_provider: str
    judge_model: str
    prompt_version: str
    dimension_scores: dict[str, int | None]
    dimension_applicability: dict[str, bool]
    evidence_by_dimension: dict[str, list[EvidenceItem]]
    evidence_status_by_dimension: dict[str, EvidenceStatus]
    dimension_rationales: dict[str, str]
    critical_gate_results: list[GateRecord]
    overall_score: float | None
    decision: Decision
    decision_reasons: list[str]
    judge_claimed_overall_score: float | None = None
    judge_claimed_decision: str | None = None
    uncertainty_notes: list[str] = Field(default_factory=list)
    grounding_issues: list[str] = Field(default_factory=list)
    injection_attempt_detected: bool = False
    injection_screen_flag: bool = False
    evaluation_timestamp: str = Field(default_factory=utc_now)
    evaluation_config_hash: str
    cache_key: str
    pass_threshold: float


class EvaluationFailure(StrictModel):
    """API or parsing failure, recorded separately and never converted to a score."""

    transcript_id: str
    rubric_version: str
    judge_provider: str
    judge_model: str
    error_type: str
    error_message: str
    attempts: int
    raw_response_excerpt: str | None = None
    timestamp: str = Field(default_factory=utc_now)


# --------------------------------------------------------------------------------------
# Human annotation
# --------------------------------------------------------------------------------------


class HumanGateStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    NOT_PRESENT = "NOT_PRESENT"
    UNCERTAIN = "UNCERTAIN"


class AnnotationStatus(StrEnum):
    DRAFT = "draft"
    COMPLETED = "completed"


class HumanAnnotation(StrictModel):
    annotation_id: str
    transcript_id: str = Field(pattern=r"^BFSI-[A-E]-\d{3}$")
    annotator_id: str = Field(min_length=1)
    rubric_version: str
    dimension_scores: dict[str, int | None]
    dimension_applicability: dict[str, bool]
    dimension_rationales: dict[str, str] = Field(default_factory=dict)
    evidence_turns: dict[str, list[str]] = Field(default_factory=dict)
    gate_assessments: dict[str, HumanGateStatus]
    overall_decision: Decision
    notes: str = ""
    status: AnnotationStatus = AnnotationStatus.COMPLETED
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)

    @staticmethod
    def make_id(transcript_id: str, annotator_id: str, rubric_version: str) -> str:
        return f"ANN-{transcript_id}-{annotator_id}-{rubric_version}"

    @model_validator(mode="after")
    def _validate(self) -> HumanAnnotation:
        if set(self.dimension_scores) != set(DIMENSIONS):
            raise ValueError("annotation must contain every dimension")
        for dim, score in self.dimension_scores.items():
            applicable = self.dimension_applicability.get(dim, True)
            if score is not None and not (isinstance(score, int) and 0 <= score <= 4):
                raise ValueError(f"{dim}: score must be an integer 0-4")
            if self.status == AnnotationStatus.COMPLETED:
                if applicable and score is None:
                    raise ValueError(f"{dim}: applicable dimension needs a score")
                if not applicable and score is not None:
                    raise ValueError(f"{dim}: not-applicable dimension must have no score")
        if set(self.gate_assessments) != set(GATE_IDS):
            raise ValueError("annotation must assess every critical gate")
        return self
