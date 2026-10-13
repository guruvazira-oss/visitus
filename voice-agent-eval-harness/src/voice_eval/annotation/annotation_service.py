"""Human annotation workflow: frozen stratified sample, local store, completion, freezing.

Protocol enforced here:
1. The 30-transcript sample is drawn by stratified random sampling with a fixed seed and
   frozen to ``data/annotation_sample.json`` BEFORE any judge results are inspected.
2. Annotations are stored in SQLite, separate from judge outputs.
3. Completed labels cannot be overwritten without explicit confirmation.
4. Freezing exports the batch to ``data/human_annotations.csv`` with a SHA-256 hash; after
   freezing, every edit requires confirmation and is written to the audit log.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from voice_eval.annotation.import_export import export_csv, import_file
from voice_eval.config import (
    ANNOTATION_DB_PATH,
    ANNOTATION_SAMPLE_PATH,
    HUMAN_ANNOTATIONS_PATH,
    load_experiment_defaults,
    rel,
)
from voice_eval.database import audit, connect
from voice_eval.schemas import (
    AnnotationStatus,
    HumanAnnotation,
    ScenarioCategory,
    Transcript,
    utc_now,
)


class OverwriteRequiresConfirmation(RuntimeError):
    pass


class SampleAlreadyFrozen(RuntimeError):
    pass


class BatchIncomplete(RuntimeError):
    pass


# --------------------------------------------------------------------------------------
# Sampling
# --------------------------------------------------------------------------------------


def stratified_sample(
    transcripts: list[Transcript], per_category: int, seed: int, exclude: set[str] | None = None
) -> list[str]:
    """Simple random sample without replacement within each scenario category.

    Transcripts are sorted by id before sampling so the result depends only on the seed and
    the frozen dataset, never on file order.
    """
    exclude = exclude or set()
    by_cat: dict[str, list[str]] = defaultdict(list)
    for t in sorted(transcripts, key=lambda x: x.transcript_id):
        if t.transcript_id not in exclude:
            by_cat[t.scenario_category.value].append(t.transcript_id)
    rng = random.Random(seed)
    ids: list[str] = []
    for cat in ScenarioCategory:  # fixed category order
        pool = by_cat.get(cat.value, [])
        if len(pool) < per_category:
            raise ValueError(f"category {cat.value} has only {len(pool)} transcripts")
        ids.extend(sorted(rng.sample(pool, per_category)))
    return ids


def create_sample(
    transcripts: list[Transcript], path: Path = ANNOTATION_SAMPLE_PATH, force: bool = False
) -> dict[str, Any]:
    cfg = load_experiment_defaults()["annotation"]
    if path.exists() and not force:
        raise SampleAlreadyFrozen(f"{rel(path)} already exists; the annotation sample is frozen.")
    ids = stratified_sample(transcripts, cfg["per_category"], cfg["sampling_seed"])
    holdout = stratified_sample(
        transcripts, cfg["holdout_sample_size"] // 5, cfg["holdout_sampling_seed"], exclude=set(ids)
    )
    dataset_version = transcripts[0].dataset_version
    payload = {
        "purpose": "Frozen calibration sample for independent human annotation.",
        "dataset_version": dataset_version,
        "procedure": (
            "Stratified simple random sampling without replacement: transcripts sorted by id, "
            f"{cfg['per_category']} drawn per scenario category with random.Random(seed).sample, "
            "categories processed in fixed enum order. Frozen before any judge output was inspected."
        ),
        "sampling_seed": cfg["sampling_seed"],
        "sample_size": len(ids),
        "transcript_ids": ids,
        "holdout": {
            "purpose": "Held-out validation sample; label only AFTER rubric development is finished.",
            "sampling_seed": cfg["holdout_sampling_seed"],
            "transcript_ids": holdout,
            "status": "not labelled — validation pending",
        },
        "frozen_at": utc_now(),
    }
    payload["sha256"] = hashlib.sha256(json.dumps(ids).encode()).hexdigest()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def load_sample(path: Path = ANNOTATION_SAMPLE_PATH) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def sample_ids(path: Path = ANNOTATION_SAMPLE_PATH) -> list[str]:
    s = load_sample(path)
    return list(s["transcript_ids"]) if s else []


# --------------------------------------------------------------------------------------
# Store
# --------------------------------------------------------------------------------------


@dataclass
class CompletionStatus:
    total: int
    completed: list[str]
    drafts: list[str]
    missing: list[str]

    @property
    def n_completed(self) -> int:
        return len(self.completed)

    @property
    def fraction(self) -> float:
        return self.n_completed / self.total if self.total else 0.0

    @property
    def is_complete(self) -> bool:
        return self.total > 0 and self.n_completed == self.total


class AnnotationStore:
    def __init__(self, db_path: Path = ANNOTATION_DB_PATH):
        self.db_path = db_path

    def get(self, annotation_id: str) -> HumanAnnotation | None:
        with connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT payload FROM annotations WHERE annotation_id = ?", (annotation_id,)
            ).fetchone()
        return HumanAnnotation.model_validate_json(row["payload"]) if row else None

    def get_for(
        self, transcript_id: str, annotator_id: str, rubric_version: str
    ) -> HumanAnnotation | None:
        return self.get(HumanAnnotation.make_id(transcript_id, annotator_id, rubric_version))

    def list(
        self, annotator_id: str | None = None, rubric_version: str | None = None
    ) -> list[HumanAnnotation]:
        q, args = "SELECT payload FROM annotations WHERE 1=1", []
        if annotator_id:
            q += " AND annotator_id = ?"
            args.append(annotator_id)
        if rubric_version:
            q += " AND rubric_version = ?"
            args.append(rubric_version)
        with connect(self.db_path) as conn:
            rows = conn.execute(q + " ORDER BY transcript_id", args).fetchall()
        return [HumanAnnotation.model_validate_json(r["payload"]) for r in rows]

    def is_frozen(self, annotator_id: str, rubric_version: str) -> bool:
        with connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM annotation_batches WHERE annotator_id = ? AND rubric_version = ?",
                (annotator_id, rubric_version),
            ).fetchone()
        return row is not None

    def save(self, ann: HumanAnnotation, confirm_overwrite: bool = False) -> HumanAnnotation:
        existing = self.get(ann.annotation_id)
        frozen = self.is_frozen(ann.annotator_id, ann.rubric_version)
        if existing and existing.status == AnnotationStatus.COMPLETED and not confirm_overwrite:
            raise OverwriteRequiresConfirmation(
                f"{ann.annotation_id} is already completed; confirm to overwrite."
            )
        if frozen and not confirm_overwrite:
            raise OverwriteRequiresConfirmation(
                f"batch for {ann.annotator_id}/{ann.rubric_version} is frozen; confirm to edit."
            )
        now = utc_now()
        ann = ann.model_copy(
            update={
                "updated_at": now,
                "created_at": existing.created_at if existing else ann.created_at,
            }
        )
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO annotations VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ann.annotation_id,
                    ann.transcript_id,
                    ann.annotator_id,
                    ann.rubric_version,
                    ann.status.value,
                    ann.model_dump_json(),
                    ann.created_at,
                    ann.updated_at,
                ),
            )
            audit(
                conn,
                "overwrite" if existing else "create",
                ann.annotation_id,
                {"status": ann.status.value, "after_freeze": frozen},
            )
        return ann

    def completion(
        self, ids: list[str], annotator_id: str, rubric_version: str
    ) -> CompletionStatus:
        anns = {a.transcript_id: a for a in self.list(annotator_id, rubric_version)}
        completed = [t for t in ids if t in anns and anns[t].status == AnnotationStatus.COMPLETED]
        drafts = [t for t in ids if t in anns and anns[t].status == AnnotationStatus.DRAFT]
        missing = [t for t in ids if t not in anns]
        return CompletionStatus(len(ids), completed, drafts, missing)

    def import_annotations(
        self, anns: list[HumanAnnotation], confirm_overwrite: bool = False
    ) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {"saved": [], "skipped_existing": []}
        for a in anns:
            try:
                self.save(a, confirm_overwrite=confirm_overwrite)
                result["saved"].append(a.transcript_id)
            except OverwriteRequiresConfirmation:
                result["skipped_existing"].append(a.transcript_id)
        return result

    def freeze_batch(
        self,
        ids: list[str],
        annotator_id: str,
        rubric_version: str,
        export_path: Path = HUMAN_ANNOTATIONS_PATH,
    ) -> dict[str, Any]:
        status = self.completion(ids, annotator_id, rubric_version)
        if not status.is_complete:
            raise BatchIncomplete(
                f"{status.n_completed}/{status.total} completed; missing {status.missing}, drafts {status.drafts}"
            )
        anns = [a for a in self.list(annotator_id, rubric_version) if a.transcript_id in ids]
        export_csv(anns, export_path)
        digest = hashlib.sha256(export_path.read_bytes()).hexdigest()
        batch_id = f"BATCH-{annotator_id}-{rubric_version}-{utc_now()}"
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO annotation_batches VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    batch_id,
                    annotator_id,
                    rubric_version,
                    utc_now(),
                    len(anns),
                    rel(export_path),
                    digest,
                    json.dumps(ids),
                ),
            )
            audit(conn, "freeze_batch", None, {"batch_id": batch_id, "sha256": digest})
        return {
            "batch_id": batch_id,
            "n": len(anns),
            "export_path": rel(export_path),
            "sha256": digest,
        }


# --------------------------------------------------------------------------------------
# Loading the frozen batch for analysis
# --------------------------------------------------------------------------------------


@dataclass
class HumanLabelState:
    annotations: list[HumanAnnotation]
    sample_ids: list[str]
    missing_ids: list[str]
    report: dict[str, Any]

    @property
    def n_required(self) -> int:
        return len(self.sample_ids)

    @property
    def complete(self) -> bool:
        return bool(self.sample_ids) and not self.missing_ids and self.report.get("ok", False)


def load_human_labels(
    path: Path = HUMAN_ANNOTATIONS_PATH, sample_path: Path = ANNOTATION_SAMPLE_PATH
) -> HumanLabelState:
    """Load the frozen human batch. Never fabricates: missing labels stay missing."""
    ids = sample_ids(sample_path)
    if not path.exists():
        return HumanLabelState(
            [], ids, list(ids), {"ok": False, "errors": [f"{rel(path)} not found"]}
        )
    rep = import_file(path, sample_ids=ids or None)
    return HumanLabelState(rep.annotations, ids, rep.missing_ids if ids else [], rep.summary())
