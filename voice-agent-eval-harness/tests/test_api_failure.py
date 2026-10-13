import pytest

from voice_eval.config import DecisionPolicy
from voice_eval.judge.base import JudgeRequest, PermanentProviderError, TransientProviderError
from voice_eval.judge.evaluator import Evaluator
from voice_eval.judge.provider import MockProvider, RateLimiter, call_with_retries
from voice_eval.schemas import EvaluationFailure


def _settings():
    from voice_eval.config import JudgeSettings

    return JudgeSettings("mock", "mock-judge", 4000, 5, 3, 0.0, "high", "ANTHROPIC_API_KEY")


def _req():
    return JudgeRequest("BFSI-A-001", "sys", "user", {}, 4000)


def test_retries_then_succeeds(judge_output_factory):
    calls = {"n": 0}

    def script(_req):
        calls["n"] += 1
        if calls["n"] < 3:
            return TransientProviderError("rate limited", retry_after=0.0)
        return judge_output_factory("BFSI-A-001")

    p = MockProvider(script)
    out = call_with_retries(p, _req(), max_retries=3, sleep=lambda s: None)
    assert out.response is not None and out.attempts == 3


def test_permanent_error_fails_fast():
    p = MockProvider([PermanentProviderError("bad key")])
    out = call_with_retries(p, _req(), max_retries=3, sleep=lambda s: None)
    assert out.response is None and out.attempts == 1


def test_transient_exhausts_retries():
    p = MockProvider([TransientProviderError("x", 0.0)] * 10)
    out = call_with_retries(p, _req(), max_retries=2, sleep=lambda s: None)
    assert out.response is None and out.attempts == 3


def test_api_failure_recorded_not_scored(tiny_transcript, rubric_v1):
    p = MockProvider([PermanentProviderError("boom")])
    ev = Evaluator(
        p, rubric_v1, DecisionPolicy(), _settings(), use_cache=False, sleep=lambda s: None
    )
    res = ev.evaluate(tiny_transcript)
    assert isinstance(res, EvaluationFailure)
    assert res.error_type == "PermanentProviderError"


def test_malformed_response_recorded(tiny_transcript, rubric_v1):
    p = MockProvider(["this is not json"] * 5)
    ev = Evaluator(
        p, rubric_v1, DecisionPolicy(), _settings(), use_cache=False, sleep=lambda s: None
    )
    res = ev.evaluate(tiny_transcript)
    assert isinstance(res, EvaluationFailure)
    assert res.error_type == "MalformedJudgeResponse"


def test_rate_limiter_spacing():
    t = {"now": 0.0}
    slept = []
    rl = RateLimiter(
        1.0,
        clock=lambda: t["now"],
        sleep=lambda s: (slept.append(s), t.__setitem__("now", t["now"] + s)),
    )
    rl.wait()
    rl.wait()
    assert slept and slept[0] == pytest.approx(1.0)
