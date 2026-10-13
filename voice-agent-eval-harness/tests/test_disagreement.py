from voice_eval.analysis.disagreement import (
    ROOT_CAUSES,
    spec_conformance_register,
    spec_conformance_summary,
)
from voice_eval.config import DecisionPolicy
from voice_eval.pipeline import select_experiment


def test_spec_register_builds_and_has_valid_causes(transcripts):
    rec = select_experiment("v1")
    evals = rec.evaluations()
    df = spec_conformance_register(evals, transcripts, DecisionPolicy())
    assert set(df["root_cause_category"]) <= set(ROOT_CAUSES)
    assert set(df["reference"]) == {"synthetic_spec"}


def test_spec_summary_tiers(transcripts):
    rec = select_experiment("v1")
    s = spec_conformance_summary(rec.evaluations(), transcripts, DecisionPolicy())
    tiers = s["tiers"].set_index("agent_quality_tier")
    # by construction the critical tier should rarely be PASS under the heuristic baseline
    assert tiers.loc["critical", "PASS"] <= tiers.loc["exemplary", "PASS"]
