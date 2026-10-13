"""Dataset validation: schema, category balance, required fields, duplicate content."""

from __future__ import annotations

import hashlib
import itertools
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from voice_eval.schemas import ScenarioCategory, Transcript

REQUIRED_FIELDS = (
    "transcript_id",
    "scenario_category",
    "scenario_description",
    "difficulty_level",
    "synthetic_borrower_profile",
    "conversation_turns",
    "intended_agent_behavior",
    "expected_resolution_type",
    "expected_critical_violations",
    "dataset_version",
    "generation_seed",
)
EXPECTED_TOTAL = 100
EXPECTED_PER_CATEGORY = 20
NEAR_DUPLICATE_THRESHOLD = 0.85


@dataclass
class ValidationReport:
    total: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def _shingles(text: str, k: int = 5) -> set[str]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(words[i : i + k]) for i in range(max(len(words) - k + 1, 1))}


def _jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def conversation_text(record: dict[str, Any]) -> str:
    return "\n".join(t["text"] for t in record["conversation_turns"])


def duplicate_check(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Exact duplicate detection (hash) and near-duplicate detection (5-gram Jaccard)."""
    hashes = Counter(hashlib.sha256(conversation_text(r).encode()).hexdigest() for r in records)
    exact_dupes = sum(c - 1 for c in hashes.values() if c > 1)
    sh = {r["transcript_id"]: _shingles(conversation_text(r)) for r in records}
    pairs = []
    for a, b in itertools.combinations(sh, 2):
        sim = _jaccard(sh[a], sh[b])
        pairs.append((sim, a, b))
    pairs.sort(reverse=True)
    near = [(round(s, 3), a, b) for s, a, b in pairs if s >= NEAR_DUPLICATE_THRESHOLD]
    sims = [p[0] for p in pairs]
    return {
        "exact_duplicate_conversations": exact_dupes,
        "near_duplicate_threshold": NEAR_DUPLICATE_THRESHOLD,
        "near_duplicate_pairs": near,
        "max_pairwise_jaccard": round(sims[0], 3) if sims else 0.0,
        "mean_pairwise_jaccard": round(sum(sims) / len(sims), 4) if sims else 0.0,
        "top_5_most_similar": [(round(s, 3), a, b) for s, a, b in pairs[:5]],
    }


def validate_records(records: list[dict[str, Any]]) -> ValidationReport:
    rep = ValidationReport(total=len(records))
    ids = Counter()
    for i, rec in enumerate(records):
        missing = [f for f in REQUIRED_FIELDS if f not in rec]
        if missing:
            rep.errors.append(f"record {i}: missing required fields {missing}")
            continue
        try:
            t = Transcript.model_validate(rec)
        except ValidationError as exc:
            rep.errors.append(f"record {i} ({rec.get('transcript_id')}): {exc.errors()[0]['msg']}")
            continue
        ids[t.transcript_id] += 1
        if t.agent_quality_tier == "critical" and not t.expected_critical_violations:
            rep.errors.append(f"{t.transcript_id}: critical tier without expected violation")
        if t.agent_quality_tier != "critical" and t.expected_critical_violations:
            rep.errors.append(f"{t.transcript_id}: non-critical tier lists expected violations")
        speakers = {turn.speaker.value for turn in t.conversation_turns}
        if speakers != {"agent", "contact"}:
            rep.errors.append(f"{t.transcript_id}: both speakers must appear")

    dup_ids = [k for k, v in ids.items() if v > 1]
    if dup_ids:
        rep.errors.append(f"duplicate transcript ids: {dup_ids}")
    if len(records) != EXPECTED_TOTAL:
        rep.errors.append(f"expected {EXPECTED_TOTAL} transcripts, found {len(records)}")

    cats = Counter(r.get("scenario_category") for r in records)
    for cat in ScenarioCategory:
        if cats.get(cat.value, 0) != EXPECTED_PER_CATEGORY:
            rep.errors.append(
                f"category {cat.value}: expected {EXPECTED_PER_CATEGORY}, found {cats.get(cat.value, 0)}"
            )

    dups = duplicate_check(records) if records else {}
    if dups.get("exact_duplicate_conversations"):
        rep.errors.append(f"{dups['exact_duplicate_conversations']} exact duplicate conversations")
    if dups.get("near_duplicate_pairs"):
        rep.warnings.append(
            f"{len(dups['near_duplicate_pairs'])} near-duplicate pairs (Jaccard >= {NEAR_DUPLICATE_THRESHOLD})"
        )

    rep.stats = distribution_stats(records)
    rep.stats["duplicate_check"] = dups
    return rep


def distribution_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    turns = [len(r["conversation_turns"]) for r in records]
    words = [len(conversation_text(r).split()) for r in records]
    mods = Counter(m.split(":")[0] for r in records for m in r.get("modifiers", []))
    inj = Counter(m.split(":")[1] for r in records for m in r.get("modifiers", []) if ":" in m)
    gates = Counter(g for r in records for g in r.get("expected_critical_violations", []))
    return {
        "by_category": dict(Counter(r["scenario_category"] for r in records)),
        "by_subtype": dict(
            Counter(f"{r['scenario_category']}/{r['scenario_subtype']}" for r in records)
        ),
        "by_difficulty": dict(Counter(r["difficulty_level"] for r in records)),
        "by_quality_tier": dict(Counter(r["agent_quality_tier"] for r in records)),
        "by_outcome_band": dict(Counter(r["expected_outcome_band"] for r in records)),
        "by_expected_resolution": dict(Counter(r["expected_resolution_type"] for r in records)),
        "by_communication_style": dict(
            Counter(r["synthetic_borrower_profile"]["communication_style"] for r in records)
        ),
        "expected_gate_violations": dict(gates),
        "modifiers": dict(mods),
        "prompt_injection_classes": dict(inj),
        "turns": {"min": min(turns), "max": max(turns), "mean": round(sum(turns) / len(turns), 2)},
        "words": {"min": min(words), "max": max(words), "mean": round(sum(words) / len(words), 1)},
    }


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]
