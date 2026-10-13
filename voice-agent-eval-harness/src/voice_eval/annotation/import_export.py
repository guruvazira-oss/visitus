"""CSV/JSON import and export of human annotations, with validation."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from voice_eval.schemas import (
    DIMENSIONS,
    GATE_IDS,
    AnnotationStatus,
    Decision,
    HumanAnnotation,
    HumanGateStatus,
    utc_now,
)

BASE_COLUMNS = ["annotation_id", "transcript_id", "annotator_id", "rubric_version", "status"]
DIM_COLUMNS = [
    f"{d}_{s}" for d in DIMENSIONS for s in ("score", "applicable", "rationale", "evidence_turns")
]
GATE_COLUMNS = [f"gate_{g}" for g in GATE_IDS]
TAIL_COLUMNS = ["overall_decision", "notes", "created_at", "updated_at"]
CSV_COLUMNS = BASE_COLUMNS + DIM_COLUMNS + GATE_COLUMNS + TAIL_COLUMNS


def annotation_to_row(a: HumanAnnotation) -> dict[str, str]:
    row: dict[str, str] = {
        "annotation_id": a.annotation_id,
        "transcript_id": a.transcript_id,
        "annotator_id": a.annotator_id,
        "rubric_version": a.rubric_version,
        "status": a.status.value,
        "overall_decision": a.overall_decision.value,
        "notes": a.notes,
        "created_at": a.created_at,
        "updated_at": a.updated_at,
    }
    for d in DIMENSIONS:
        s = a.dimension_scores.get(d)
        row[f"{d}_score"] = "" if s is None else str(s)
        row[f"{d}_applicable"] = "true" if a.dimension_applicability.get(d, True) else "false"
        row[f"{d}_rationale"] = a.dimension_rationales.get(d, "")
        row[f"{d}_evidence_turns"] = ";".join(a.evidence_turns.get(d, []))
    for g in GATE_IDS:
        row[f"gate_{g}"] = a.gate_assessments[g].value
    return row


def export_csv(annotations: list[HumanAnnotation], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for a in sorted(annotations, key=lambda x: x.transcript_id):
            w.writerow(annotation_to_row(a))
    return path


def export_json(annotations: list[HumanAnnotation], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        a.model_dump(mode="json") for a in sorted(annotations, key=lambda x: x.transcript_id)
    ]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def export_template(
    sample_ids: list[str], path: Path, rubric_version: str, annotator_id: str = ""
) -> Path:
    """Blank template: one row per sampled transcript, all label fields empty."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for tid in sample_ids:
            row = dict.fromkeys(CSV_COLUMNS, "")
            row.update(
                {
                    "transcript_id": tid,
                    "annotator_id": annotator_id,
                    "rubric_version": rubric_version,
                    "status": "draft",
                }
            )
            row.update({f"{d}_applicable": "true" for d in DIMENSIONS})
            w.writerow(row)
    return path


def _bool(v: Any, default: bool = True) -> bool:
    if v is None or str(v).strip() == "":
        return default
    s = str(v).strip().lower()
    if s in ("true", "1", "yes", "y"):
        return True
    if s in ("false", "0", "no", "n", "na", "n/a"):
        return False
    raise ValueError(f"invalid boolean {v!r}")


def _score(v: Any) -> int | None:
    if v is None or str(v).strip() == "":
        return None
    s = str(v).strip()
    if not s.lstrip("-").isdigit():
        raise ValueError(f"score {v!r} is not an integer")
    return int(s)


def row_to_annotation(row: dict[str, Any]) -> HumanAnnotation:
    tid = str(row.get("transcript_id", "")).strip()
    annotator = str(row.get("annotator_id", "")).strip()
    rubric = str(row.get("rubric_version", "")).strip()
    scores, applic, rats, evid = {}, {}, {}, {}
    for d in DIMENSIONS:
        scores[d] = _score(row.get(f"{d}_score"))
        applic[d] = _bool(row.get(f"{d}_applicable"))
        rats[d] = str(row.get(f"{d}_rationale") or "")
        ev = str(row.get(f"{d}_evidence_turns") or "")
        evid[d] = [x.strip() for x in ev.split(";") if x.strip()]
    gates = {}
    for g in GATE_IDS:
        v = str(row.get(f"gate_{g}") or "").strip().upper()
        if not v:
            raise ValueError(f"gate {g} not assessed")
        gates[g] = HumanGateStatus(v)
    decision = str(row.get("overall_decision") or "").strip().upper()
    if not decision:
        raise ValueError("overall_decision missing")
    return HumanAnnotation(
        annotation_id=str(row.get("annotation_id") or "").strip()
        or HumanAnnotation.make_id(tid, annotator, rubric),
        transcript_id=tid,
        annotator_id=annotator,
        rubric_version=rubric,
        dimension_scores=scores,
        dimension_applicability=applic,
        dimension_rationales=rats,
        evidence_turns=evid,
        gate_assessments=gates,
        overall_decision=Decision(decision),
        notes=str(row.get("notes") or ""),
        status=AnnotationStatus(str(row.get("status") or "completed").strip().lower()),
        created_at=str(row.get("created_at") or "") or utc_now(),
        updated_at=str(row.get("updated_at") or "") or utc_now(),
    )


def _is_blank(row: dict[str, Any]) -> bool:
    label_cols = [f"{d}_score" for d in DIMENSIONS] + GATE_COLUMNS + ["overall_decision"]
    return all(str(row.get(c) or "").strip() == "" for c in label_cols)


@dataclass
class ImportReport:
    annotations: list[HumanAnnotation] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    missing_ids: list[str] = field(default_factory=list)
    unknown_ids: list[str] = field(default_factory=list)
    duplicate_ids: list[str] = field(default_factory=list)
    invalid_rows: list[str] = field(default_factory=list)
    rubric_mismatches: list[str] = field(default_factory=list)
    blank_rows: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.errors
            or self.duplicate_ids
            or self.invalid_rows
            or self.rubric_mismatches
            or self.unknown_ids
        )

    def summary(self) -> dict[str, Any]:
        return {
            "valid_annotations": len(self.annotations),
            "ok": self.ok,
            "missing_ids": self.missing_ids,
            "unknown_ids": self.unknown_ids,
            "duplicate_ids": self.duplicate_ids,
            "invalid_rows": self.invalid_rows,
            "rubric_mismatches": self.rubric_mismatches,
            "blank_rows": self.blank_rows,
            "errors": self.errors,
        }


def read_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON import must be a list of annotation objects")
        rows = []
        for obj in data:  # accept either the flat CSV shape or the nested model shape
            if "dimension_scores" in obj:
                rows.append(annotation_to_row(HumanAnnotation.model_validate(obj)))
            else:
                rows.append(obj)
        return rows
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def validate_rows(
    rows: list[dict[str, Any]],
    sample_ids: list[str] | None = None,
    expected_rubric: str | None = None,
    require_completed: bool = True,
) -> ImportReport:
    rep = ImportReport()
    seen: dict[tuple[str, str], int] = {}
    for i, row in enumerate(rows, start=2):  # header is line 1
        tid = str(row.get("transcript_id") or "").strip()
        label = f"line {i} ({tid or 'no transcript_id'})"
        if _is_blank(row):
            rep.blank_rows.append(tid or label)
            continue
        key = (tid, str(row.get("annotator_id") or "").strip())
        if key in seen:
            rep.duplicate_ids.append(
                f"{tid} (annotator {key[1] or '?'}, lines {seen[key]} and {i})"
            )
            continue
        seen[key] = i
        if sample_ids is not None and tid not in sample_ids:
            rep.unknown_ids.append(tid)
            continue
        rubric = str(row.get("rubric_version") or "").strip()
        if expected_rubric and rubric != expected_rubric:
            rep.rubric_mismatches.append(f"{tid}: {rubric or 'blank'} != {expected_rubric}")
            continue
        try:
            ann = row_to_annotation(row)
        except (ValueError, ValidationError) as exc:
            msg = exc.errors()[0]["msg"] if isinstance(exc, ValidationError) else str(exc)
            rep.invalid_rows.append(f"{label}: {msg}")
            continue
        if require_completed and ann.status != AnnotationStatus.COMPLETED:
            rep.blank_rows.append(tid)
            continue
        rep.annotations.append(ann)
    if sample_ids is not None:
        have = {a.transcript_id for a in rep.annotations}
        rep.missing_ids = [t for t in sample_ids if t not in have]
    return rep


def import_file(
    path: Path, sample_ids: list[str] | None = None, expected_rubric: str | None = None
) -> ImportReport:
    try:
        rows = read_rows(path)
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        rep = ImportReport()
        rep.errors.append(f"could not read {path.name}: {exc}")
        return rep
    return validate_rows(rows, sample_ids, expected_rubric)
