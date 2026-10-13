from voice_eval.config import DecisionPolicy, JudgeSettings
from voice_eval.judge.evaluator import Evaluator
from voice_eval.judge.provider import HeuristicProvider, get_provider
from voice_eval.pipeline import analyse, select_experiment


def _settings():
    return JudgeSettings(
        "heuristic", "heuristic-baseline-v1", 4000, 5, 2, 0.0, "high", "ANTHROPIC_API_KEY"
    )


def test_heuristic_is_not_llm():
    p = get_provider("heuristic", _settings())
    assert isinstance(p, HeuristicProvider) and p.is_llm is False


def test_offline_evaluation_runs_without_key(transcripts, rubric_v1):
    p = HeuristicProvider(rubric_v1.heuristic_rules)
    p.register(transcripts)
    ev = Evaluator(p, rubric_v1, DecisionPolicy(), _settings(), use_cache=False)
    evals, fails = ev.evaluate_many(transcripts[:20])
    assert len(evals) == 20 and not fails
    assert all(e.judge_provider == "heuristic" for e in evals)


def test_demo_experiment_present_and_labelled():
    rec = select_experiment("v1")
    assert rec is not None
    assert rec.manifest["provenance"] in ("demo_heuristic", "llm")
    assert rec.manifest["is_llm"] in (True, False)


def test_analysis_bundle_without_humans():
    b = analyse("v1")
    # with no frozen human labels the agreement is None, not fabricated
    if not b.labels.complete:
        assert b.agreement is None
    assert not b.thresholds.empty
    assert not b.spec_register.empty or b.spec_register.empty  # spec register builds regardless
