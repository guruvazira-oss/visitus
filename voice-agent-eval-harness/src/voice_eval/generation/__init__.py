"""Synthetic dataset generation and the frozen-artifact writer."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from voice_eval.config import MANIFEST_PATH, TRANSCRIPTS_CSV_PATH, TRANSCRIPTS_PATH, rel
from voice_eval.dataset_loader import write_jsonl
from voice_eval.dataset_validation import file_sha256, validate_records
from voice_eval.generation.synthetic_generator import (
    COMPANY,
    DATASET_VERSION,
    GENERATION_SEED,
    generate_dataset,
)
from voice_eval.schemas import utc_now

__all__ = ["generate_dataset", "write_dataset", "verify_reproducible", "GenerationResult"]


@dataclass
class GenerationResult:
    path: Path
    sha256: str
    written: bool
    message: str


class FrozenDatasetError(RuntimeError):
    pass


def _serialise(records: list[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


def verify_reproducible(path: Path = TRANSCRIPTS_PATH, seed: int = GENERATION_SEED) -> bool:
    """Regenerate in memory and compare with the committed artifact byte for byte."""
    return path.exists() and path.read_text(encoding="utf-8") == _serialise(generate_dataset(seed))


def write_csv(records: list[dict], path: Path = TRANSCRIPTS_CSV_PATH) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "transcript_id",
                "scenario_category",
                "scenario_subtype",
                "difficulty_level",
                "agent_quality_tier",
                "expected_critical_violations",
                "turn_id",
                "speaker",
                "text",
            ]
        )
        for r in records:
            for t in r["conversation_turns"]:
                w.writerow(
                    [
                        r["transcript_id"],
                        r["scenario_category"],
                        r["scenario_subtype"],
                        r["difficulty_level"],
                        r["agent_quality_tier"],
                        ";".join(r["expected_critical_violations"]),
                        t["turn_id"],
                        t["speaker"],
                        t["text"],
                    ]
                )


def write_manifest(records: list[dict], path: Path = TRANSCRIPTS_PATH) -> dict:
    report = validate_records(records)
    manifest = {
        "dataset_version": DATASET_VERSION,
        "generation_seed": GENERATION_SEED,
        "generator": "src/voice_eval/generation/synthetic_generator.py (deterministic templates, no LLM)",
        "fictional_institution": COMPANY,
        "n_transcripts": len(records),
        "transcripts_file": rel(path),
        "transcripts_sha256": file_sha256(path),
        "readable_csv": rel(TRANSCRIPTS_CSV_PATH),
        "generated_at": utc_now(),
        "validation_ok": report.ok,
        "validation_errors": report.errors,
        "validation_warnings": report.warnings,
        "statistics": report.stats,
        "disclaimers": [
            "All conversations, people, institutions and policies are fictional.",
            "intended_agent_behavior and expected_critical_violations are synthetic test "
            "specifications written by the generator author, not independent ground truth.",
            "The committed transcripts.jsonl is the frozen experimental artifact.",
        ],
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def write_dataset(
    path: Path = TRANSCRIPTS_PATH, force: bool = False, seed: int = GENERATION_SEED
) -> GenerationResult:
    records = generate_dataset(seed)
    if path.exists() and not force:
        if path.read_text(encoding="utf-8") == _serialise(records):
            return GenerationResult(
                path,
                file_sha256(path),
                False,
                "Frozen dataset already present and identical to a fresh generation; nothing written.",
            )
        raise FrozenDatasetError(
            f"{rel(path)} exists and differs from the generator output. The committed dataset is "
            "the frozen experimental artifact; pass --force only if you intend to create a new "
            "dataset version (and bump dataset.version)."
        )
    write_jsonl(records, path)
    write_csv(records)
    write_manifest(records, path)
    return GenerationResult(
        path, file_sha256(path), True, f"Wrote {len(records)} transcripts to {rel(path)}."
    )
