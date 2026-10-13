import pytest

from voice_eval.annotation.annotation_service import (
    AnnotationStore,
    BatchIncomplete,
    OverwriteRequiresConfirmation,
    stratified_sample,
)
from voice_eval.annotation.import_export import (
    annotation_to_row,
    export_csv,
    import_file,
    row_to_annotation,
    validate_rows,
)
from voice_eval.schemas import (
    DIMENSIONS,
    GATE_IDS,
    AnnotationStatus,
    Decision,
    HumanAnnotation,
    HumanGateStatus,
)


def _ann(tid="BFSI-A-001", annotator="u1", status=AnnotationStatus.COMPLETED, score=3):
    return HumanAnnotation(
        annotation_id=HumanAnnotation.make_id(tid, annotator, "v1"),
        transcript_id=tid,
        annotator_id=annotator,
        rubric_version="v1",
        dimension_scores=dict.fromkeys(DIMENSIONS, score),
        dimension_applicability=dict.fromkeys(DIMENSIONS, True),
        dimension_rationales=dict.fromkeys(DIMENSIONS, "ok"),
        evidence_turns={},
        gate_assessments=dict.fromkeys(GATE_IDS, HumanGateStatus.NOT_PRESENT),
        overall_decision=Decision.PASS,
        status=status,
    )


def test_roundtrip_csv(tmp_path):
    a = _ann()
    row = annotation_to_row(a)
    b = row_to_annotation(row)
    assert b.dimension_scores == a.dimension_scores
    assert b.gate_assessments == a.gate_assessments
    assert b.overall_decision == a.overall_decision


def test_stratified_sample_deterministic(transcripts):
    s1 = stratified_sample(transcripts, 6, 7301)
    s2 = stratified_sample(transcripts, 6, 7301)
    assert s1 == s2 and len(s1) == 30
    cats = {t.transcript_id: t.scenario_category.value for t in transcripts}
    from collections import Counter

    assert all(c == 6 for c in Counter(cats[i] for i in s1).values())


def test_import_detects_invalid_score(tmp_path):
    a = _ann()
    row = annotation_to_row(a)
    row["intent_capture_score"] = "9"
    rep = validate_rows([row])
    assert rep.invalid_rows and not rep.ok


def test_import_detects_duplicates():
    row = annotation_to_row(_ann())
    rep = validate_rows([row, dict(row)])
    assert rep.duplicate_ids


def test_import_detects_rubric_mismatch():
    row = annotation_to_row(_ann())
    rep = validate_rows([row], expected_rubric="v2")
    assert rep.rubric_mismatches


def test_import_reports_unknown_and_missing_ids():
    row = annotation_to_row(_ann("BFSI-A-001"))
    rep = validate_rows([row], sample_ids=["BFSI-A-002", "BFSI-A-003"])
    assert "BFSI-A-001" in rep.unknown_ids
    assert set(rep.missing_ids) == {"BFSI-A-002", "BFSI-A-003"}


def test_overwrite_protection(tmp_path):
    store = AnnotationStore(tmp_path / "db.sqlite")
    store.save(_ann())
    with pytest.raises(OverwriteRequiresConfirmation):
        store.save(_ann(score=1))
    store.save(_ann(score=1), confirm_overwrite=True)
    assert store.get(_ann().annotation_id).dimension_scores["intent_capture"] == 1


def test_draft_can_be_updated_without_confirm(tmp_path):
    store = AnnotationStore(tmp_path / "db.sqlite")
    store.save(_ann(status=AnnotationStatus.DRAFT))
    store.save(_ann(status=AnnotationStatus.DRAFT, score=2))  # no error


def test_freeze_requires_complete(tmp_path):
    store = AnnotationStore(tmp_path / "db.sqlite")
    store.save(_ann("BFSI-A-001"))
    with pytest.raises(BatchIncomplete):
        store.freeze_batch(["BFSI-A-001", "BFSI-A-002"], "u1", "v1", tmp_path / "out.csv")


def test_freeze_writes_hashed_batch(tmp_path):
    store = AnnotationStore(tmp_path / "db.sqlite")
    store.save(_ann("BFSI-A-001"))
    info = store.freeze_batch(["BFSI-A-001"], "u1", "v1", tmp_path / "out.csv")
    assert info["n"] == 1 and len(info["sha256"]) == 64
    assert store.is_frozen("u1", "v1")


def test_export_import_file_roundtrip(tmp_path):
    p = tmp_path / "x.csv"
    export_csv([_ann("BFSI-A-001"), _ann("BFSI-A-002")], p)
    rep = import_file(p)
    assert len(rep.annotations) == 2 and rep.ok
