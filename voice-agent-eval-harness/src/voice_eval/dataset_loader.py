"""Read the frozen transcript dataset. Never regenerates data as a side effect."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

from voice_eval.config import TRANSCRIPTS_PATH
from voice_eval.schemas import Transcript


class DatasetMissingError(FileNotFoundError):
    pass


def load_transcripts(path: Path = TRANSCRIPTS_PATH) -> list[Transcript]:
    if not path.exists():
        raise DatasetMissingError(
            f"{path} not found. Generate it once with `uv run python scripts/generate_dataset.py`."
        )
    out: list[Transcript] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                out.append(Transcript.model_validate_json(line))
            except Exception as exc:  # surface the line number with the validation error
                raise ValueError(f"{path.name}:{line_no}: {exc}") from exc
    return out


@lru_cache(maxsize=4)
def _cached(path_str: str, mtime: float) -> tuple[Transcript, ...]:
    return tuple(load_transcripts(Path(path_str)))


def load_transcripts_cached(path: Path = TRANSCRIPTS_PATH) -> list[Transcript]:
    return list(_cached(str(path), path.stat().st_mtime if path.exists() else 0.0))


def transcript_index(transcripts: list[Transcript]) -> dict[str, Transcript]:
    return {t.transcript_id: t for t in transcripts}


def transcripts_frame(transcripts: list[Transcript]) -> pd.DataFrame:
    rows = []
    for t in transcripts:
        rows.append(
            {
                "transcript_id": t.transcript_id,
                "scenario_category": t.scenario_category.value,
                "scenario_subtype": t.scenario_subtype,
                "difficulty_level": t.difficulty_level,
                "agent_quality_tier": t.agent_quality_tier,
                "expected_outcome_band": t.expected_outcome_band,
                "expected_resolution_type": t.expected_resolution_type.value,
                "expected_critical_violations": ";".join(t.expected_critical_violations),
                "modifiers": ";".join(t.modifiers),
                "n_turns": len(t.conversation_turns),
                "n_words": sum(len(turn.text.split()) for turn in t.conversation_turns),
                "communication_style": t.synthetic_borrower_profile.communication_style,
            }
        )
    return pd.DataFrame(rows)


def render_transcript_text(t: Transcript) -> str:
    return "\n".join(
        f"[{turn.turn_id}] {turn.speaker.value.upper()}: {turn.text}"
        for turn in t.conversation_turns
    )


def write_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=False) + "\n")
