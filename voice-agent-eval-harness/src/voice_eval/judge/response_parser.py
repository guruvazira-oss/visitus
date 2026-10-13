"""Parse and strictly validate judge responses; verify evidence grounding."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from pydantic import ValidationError

from voice_eval.rubric_loader import Rubric
from voice_eval.schemas import EvidenceItem, JudgeOutput, Transcript


class MalformedJudgeResponse(ValueError):
    def __init__(self, message: str, raw: str = ""):
        super().__init__(message)
        self.raw = raw


def _extract_json(raw: str) -> str:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        return fence.group(1)
    if text.startswith("{"):
        return text
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise MalformedJudgeResponse("no JSON object found in judge response", raw)
    return text[start : end + 1]


def parse_judge_response(raw: str, transcript: Transcript, rubric: Rubric) -> JudgeOutput:
    """Strictly parse a judge response. Raises MalformedJudgeResponse on any violation."""
    if not raw or not raw.strip():
        raise MalformedJudgeResponse("empty judge response", raw)
    try:
        data = json.loads(_extract_json(raw))
    except json.JSONDecodeError as exc:
        raise MalformedJudgeResponse(f"invalid JSON: {exc}", raw) from exc
    if not isinstance(data, dict):
        raise MalformedJudgeResponse("judge response is not a JSON object", raw)
    try:
        out = JudgeOutput.model_validate(data)
    except ValidationError as exc:
        first = exc.errors()[0]
        loc = ".".join(str(x) for x in first["loc"])
        raise MalformedJudgeResponse(f"schema violation at {loc}: {first['msg']}", raw) from exc
    if out.transcript_id != transcript.transcript_id:
        raise MalformedJudgeResponse(
            f"transcript_id mismatch: expected {transcript.transcript_id}, got {out.transcript_id}",
            raw,
        )
    for d in out.dimensions:
        if not d.applicable and rubric.dimension(d.dimension).applicability.always_applicable:
            raise MalformedJudgeResponse(
                f"{d.dimension} is always applicable under rubric {rubric.rubric_version} but was marked N/A",
                raw,
            )
    return out


def _norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


@dataclass
class GroundingReport:
    verified: dict[int, bool] = field(default_factory=dict)  # id(evidence) -> verified
    issues: list[str] = field(default_factory=list)

    def is_verified(self, ev: EvidenceItem) -> bool:
        return self.verified.get(id(ev), False)


def verify_evidence(out: JudgeOutput, transcript: Transcript) -> GroundingReport:
    """Check each cited turn exists and each direct quote appears verbatim (normalised)."""
    turns = {t.turn_id: _norm(t.text) for t in transcript.conversation_turns}
    rep = GroundingReport()
    items: list[tuple[str, EvidenceItem]] = [
        (d.dimension, e) for d in out.dimensions for e in d.evidence
    ]
    items += [(g.gate_id, e) for g in out.critical_gates for e in g.evidence]
    for owner, ev in items:
        if ev.turn_id not in turns:
            rep.verified[id(ev)] = False
            rep.issues.append(f"{owner}: cited turn {ev.turn_id} does not exist")
            continue
        quote = _norm(ev.quote.strip(" .\"'…"))
        ok = quote in turns[ev.turn_id] if ev.evidence_type.value == "direct" else True
        rep.verified[id(ev)] = ok
        if not ok:
            rep.issues.append(
                f"{owner}: quote not found verbatim in {ev.turn_id}: {ev.quote[:80]!r}"
            )
    for d in out.dimensions:
        if d.applicable and not d.evidence and d.evidence_status.value == "sufficient":
            rep.issues.append(f"{d.dimension}: evidence_status 'sufficient' but no evidence cited")
    return rep
