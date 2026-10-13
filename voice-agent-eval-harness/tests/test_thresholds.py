from voice_eval.analysis.threshold_sensitivity import changed_classifications, sweep
from voice_eval.config import DecisionPolicy


def _evals(transcripts, rubric_v1):
    from voice_eval.config import JudgeSettings
    from voice_eval.judge.evaluator import Evaluator
    from voice_eval.judge.provider import HeuristicProvider

    s = JudgeSettings(
        "heuristic", "heuristic-baseline-v1", 4000, 5, 2, 0.0, "high", "ANTHROPIC_API_KEY"
    )
    p = HeuristicProvider(rubric_v1.heuristic_rules)
    p.register(transcripts)
    ev = Evaluator(p, rubric_v1, DecisionPolicy(), s, use_cache=False)
    evals, _ = ev.evaluate_many(transcripts)
    return evals


def test_sweep_monotone_pass_rate(transcripts, rubric_v1, policy):
    evals = _evals(transcripts, rubric_v1)
    df = sweep(evals, [50, 60, 70, 80, 90], policy)
    full = df[df["population"] == "full_synthetic"].sort_values("cutoff")
    assert list(full["pass_rate"]) == sorted(full["pass_rate"], reverse=True)


def test_gate_overrides_constant_across_cutoffs(transcripts, rubric_v1, policy):
    evals = _evals(transcripts, rubric_v1)
    df = sweep(evals, [50, 90], policy)
    assert df["critical_gate_overrides"].nunique() == 1


def test_changed_classifications_nonempty(transcripts, rubric_v1, policy):
    evals = _evals(transcripts, rubric_v1)
    ch = changed_classifications(evals, [50, 90], policy)
    assert not ch.empty
    assert set(ch["decision_before"]) <= {"PASS", "FAIL", "REVIEW_REQUIRED"}
