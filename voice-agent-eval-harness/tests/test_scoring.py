import pytest

from voice_eval.config import DecisionPolicy
from voice_eval.schemas import AdjudicationStatus, Decision
from voice_eval.scoring import ScoringError, decide, to_binary, weighted_score

W = {
    "intent_capture": 0.2,
    "objection_handling": 0.2,
    "compliance_adherence": 0.3,
    "fallback_grace": 0.15,
    "resolution_quality": 0.15,
}


def test_all_fours_is_100():
    assert weighted_score(dict.fromkeys(W, 4), W) == 100.0


def test_all_zeros_is_0():
    assert weighted_score(dict.fromkeys(W, 0), W) == 0.0


def test_weighting_matches_manual():
    scores = {
        "intent_capture": 4,
        "objection_handling": 2,
        "compliance_adherence": 3,
        "fallback_grace": 1,
        "resolution_quality": 0,
    }
    expected = 100 * (0.2 * 1.0 + 0.2 * 0.5 + 0.3 * 0.75 + 0.15 * 0.25 + 0.15 * 0.0)
    assert weighted_score(scores, W) == pytest.approx(expected)


def test_renormalisation_on_na():
    scores = {
        "intent_capture": 4,
        "objection_handling": None,
        "compliance_adherence": 4,
        "fallback_grace": 4,
        "resolution_quality": 4,
    }
    app = {
        "intent_capture": True,
        "objection_handling": False,
        "compliance_adherence": True,
        "fallback_grace": True,
        "resolution_quality": True,
    }
    assert weighted_score(scores, W, app) == 100.0  # NA dim excluded, weights renormalise


def test_all_na_is_none():
    assert weighted_score(dict.fromkeys(W, None), W, dict.fromkeys(W, False)) is None


def test_invalid_score_raises():
    with pytest.raises(ScoringError):
        weighted_score({**dict.fromkeys(W, 3), "intent_capture": 7}, W)
    with pytest.raises(ScoringError):
        weighted_score({**dict.fromkeys(W, 3), "intent_capture": None}, W, dict.fromkeys(W, True))


def test_threshold_classification():
    p = DecisionPolicy(pass_threshold=75)
    assert decide(80, [], p).decision == Decision.PASS
    assert decide(75, [], p).decision == Decision.PASS
    assert decide(74.9, [], p).decision == Decision.FAIL


def test_confirmed_gate_overrides_high_score():
    p = DecisionPolicy(pass_threshold=75)
    r = decide(99, [AdjudicationStatus.CONFIRMED_VIOLATION], p)
    assert r.decision == Decision.FAIL


def test_alleged_gate_routes_to_review():
    p = DecisionPolicy(pass_threshold=75, unconfirmed_gate_policy="review_required")
    assert (
        decide(99, [AdjudicationStatus.JUDGE_ALLEGED_UNCONFIRMED], p).decision
        == Decision.REVIEW_REQUIRED
    )


def test_alleged_gate_fail_policy():
    p = DecisionPolicy(pass_threshold=75, unconfirmed_gate_policy="fail")
    assert decide(99, [AdjudicationStatus.JUDGE_ALLEGED_UNCONFIRMED], p).decision == Decision.FAIL


def test_uncertain_gate_review():
    p = DecisionPolicy(pass_threshold=75)
    assert decide(99, [AdjudicationStatus.UNCERTAIN], p).decision == Decision.REVIEW_REQUIRED


def test_none_score_review():
    assert decide(None, [], DecisionPolicy()).decision == Decision.REVIEW_REQUIRED


def test_injection_pass_routed_to_review():
    p = DecisionPolicy(pass_threshold=75, route_injection_flagged_passes_to_review=True)
    assert decide(90, [], p, injection_flagged=True).decision == Decision.REVIEW_REQUIRED
    p2 = DecisionPolicy(pass_threshold=75, route_injection_flagged_passes_to_review=False)
    assert decide(90, [], p2, injection_flagged=True).decision == Decision.PASS


def test_to_binary_mapping():
    assert to_binary(Decision.REVIEW_REQUIRED, "as_fail") == "FAIL"
    assert to_binary(Decision.REVIEW_REQUIRED, "as_pass") == "PASS"
    assert to_binary(Decision.REVIEW_REQUIRED, "exclude") is None
    assert to_binary(Decision.PASS, "as_fail") == "PASS"
