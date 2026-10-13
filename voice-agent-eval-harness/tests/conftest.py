from __future__ import annotations

import pytest

from voice_eval.config import DecisionPolicy, JudgeSettings
from voice_eval.dataset_loader import load_transcripts
from voice_eval.generation.synthetic_generator import generate_dataset
from voice_eval.rubric_loader import load_rubric
from voice_eval.schemas import (
    DIMENSIONS,
    GATE_IDS,
    Transcript,
)


@pytest.fixture(scope="session")
def records():
    return generate_dataset()


@pytest.fixture(scope="session")
def transcripts():
    return load_transcripts()


@pytest.fixture(scope="session")
def rubric_v1():
    return load_rubric("v1")


@pytest.fixture
def policy():
    return DecisionPolicy()


@pytest.fixture
def test_settings():
    return JudgeSettings(
        provider="mock",
        model="mock-judge",
        max_tokens=4000,
        timeout_seconds=5,
        max_retries=2,
        min_seconds_between_requests=0.0,
        effort="high",
        api_key_env="ANTHROPIC_API_KEY",
    )


def make_judge_output(
    transcript_id: str,
    scores=None,
    applicable=None,
    gates=None,
    evidence=None,
    injection=False,
    claimed_score=None,
):
    scores = scores or dict.fromkeys(DIMENSIONS, 3)
    applicable = applicable or dict.fromkeys(DIMENSIONS, True)
    gates = gates or dict.fromkeys(GATE_IDS, "NO_VIOLATION")
    dims = []
    for d in DIMENSIONS:
        app = applicable[d]
        ev = (evidence or {}).get(d, [])
        dims.append(
            {
                "dimension": d,
                "applicable": app,
                "score": scores[d] if app else None,
                "rationale": f"rationale for {d}",
                "evidence": ev,
                "evidence_status": "sufficient" if ev or not app else "missing",
            }
        )
    crit = []
    for g in GATE_IDS:
        a = gates[g]
        crit.append(
            {
                "gate_id": g,
                "assessment": a,
                "rationale": f"gate {g}",
                "evidence": (evidence or {}).get(g, []),
            }
        )
    return {
        "transcript_id": transcript_id,
        "dimensions": dims,
        "critical_gates": crit,
        "claimed_overall_score": claimed_score,
        "claimed_decision": None,
        "uncertainty_notes": [],
        "injection_attempt_detected": injection,
    }


@pytest.fixture
def judge_output_factory():
    return make_judge_output


@pytest.fixture(scope="session")
def tiny_transcript() -> Transcript:
    return Transcript.model_validate(
        {
            "transcript_id": "BFSI-A-001",
            "scenario_category": "FIRST_TIME_DEFAULTER",
            "scenario_subtype": "x",
            "scenario_description": "d",
            "difficulty_level": "easy",
            "synthetic_borrower_profile": {
                "full_name": "Jo Doe",
                "date_of_birth": "1 January 1990",
                "postcode": "AB1 2CD",
                "product_type": "personal loan",
                "outstanding_amount": 1000.0,
                "instalment_amount": 100.0,
                "currency": "USD-fictional",
                "days_past_due": 10,
                "prior_missed_commitments": 0,
                "communication_style": "formal",
                "vulnerability_indicator": False,
            },
            "conversation_turns": [
                {
                    "turn_id": "T01",
                    "speaker": "agent",
                    "text": "Hello, this is a test call. May I speak with Jo Doe?",
                },
                {"turn_id": "T02", "speaker": "contact", "text": "Yes, speaking."},
                {"turn_id": "T03", "speaker": "agent", "text": "Thank you, you're verified."},
                {"turn_id": "T04", "speaker": "contact", "text": "I will pay on Friday."},
            ],
            "intended_agent_behavior": ["be nice"],
            "expected_resolution_type": "PAYMENT_COMMITMENT",
            "expected_critical_violations": [],
            "agent_quality_tier": "exemplary",
            "expected_outcome_band": "PASS_EXPECTED",
            "modifiers": [],
            "ambiguity_notes": [],
            "dataset_version": "bfsi-collections-v1.0",
            "generation_seed": 20260415,
        }
    )
