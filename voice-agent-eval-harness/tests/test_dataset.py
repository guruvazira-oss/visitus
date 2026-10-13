from voice_eval.dataset_validation import duplicate_check, validate_records
from voice_eval.generation import verify_reproducible
from voice_eval.schemas import ScenarioCategory


def test_exactly_100(records):
    assert len(records) == 100


def test_category_balance(records):
    rep = validate_records(records)
    assert rep.ok, rep.errors
    for cat in ScenarioCategory:
        assert rep.stats["by_category"][cat.value] == 20


def test_required_fields_present(records):
    for r in records:
        for f in (
            "transcript_id",
            "conversation_turns",
            "expected_critical_violations",
            "generation_seed",
        ):
            assert f in r


def test_no_exact_duplicates(records):
    assert duplicate_check(records)["exact_duplicate_conversations"] == 0


def test_near_duplicate_bound(records):
    assert duplicate_check(records)["max_pairwise_jaccard"] < 0.85


def test_deterministic(records):
    from voice_eval.generation.synthetic_generator import generate_dataset

    assert generate_dataset() == records
    assert generate_dataset(20260415) == generate_dataset(20260415)


def test_committed_file_reproducible():
    assert verify_reproducible()


def test_injection_classes_covered(records):
    rep = validate_records(records)
    assert len(rep.stats["prompt_injection_classes"]) == 5


def test_critical_tiers_have_expected_violation(records):
    for r in records:
        if r["agent_quality_tier"] == "critical":
            assert r["expected_critical_violations"]
        else:
            assert not r["expected_critical_violations"]


def test_turn_ids_unique_and_stable(transcripts):
    for t in transcripts:
        ids = [x.turn_id for x in t.conversation_turns]
        assert ids == sorted(ids, key=lambda s: int(s[1:]))
        assert len(ids) == len(set(ids))
