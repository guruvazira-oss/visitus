"""Evaluation orchestration: judge call -> strict parse -> grounding -> recomputation.

Judge-claimed totals and decisions are stored for audit but never used. The overall score
and decision are always recomputed in Python from validated dimension scores, rubric
applicability, critical-gate adjudication and the configured decision policy.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from voice_eval.config import CACHE_DIR, DecisionPolicy, JudgeSettings
from voice_eval.judge.base import JudgeProvider, JudgeRequest
from voice_eval.judge.prompts import (
    PROMPT_VERSION,
    build_system_prompt,
    build_user_prompt,
    output_schema,
)
from voice_eval.judge.provider import RateLimiter, call_with_retries
from voice_eval.judge.response_parser import (
    MalformedJudgeResponse,
    parse_judge_response,
    verify_evidence,
)
from voice_eval.judge.screens import detect_injection, screen_gates
from voice_eval.rubric_loader import Rubric
from voice_eval.schemas import (
    DIMENSIONS,
    AdjudicationStatus,
    Evaluation,
    EvaluationFailure,
    GateAssessment,
    GateRecord,
    JudgeOutput,
    Transcript,
)
from voice_eval.scoring import decide, human_gate_status, weighted_score


def sha(obj: object, n: int = 16) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:n]


def transcript_hash(t: Transcript) -> str:
    return sha(t.model_dump(mode="json"), 16)


@dataclass(frozen=True)
class EvaluatorConfig:
    provider: str
    model: str
    rubric_version: str
    rubric_hash: str
    prompt_version: str
    max_tokens: int
    effort: str
    pass_threshold: float
    unconfirmed_gate_policy: str
    route_injection_flagged_passes_to_review: bool
    cross_check_with_lexical_screen: bool

    def hash(self) -> str:
        return sha(asdict(self), 12)

    def cache_fields(self) -> dict:
        """Only fields that change the judge's raw output belong in the cache key."""
        return {
            k: v
            for k, v in asdict(self).items()
            if k
            in (
                "provider",
                "model",
                "rubric_version",
                "rubric_hash",
                "prompt_version",
                "max_tokens",
                "effort",
            )
        }


def build_gate_records(
    out: JudgeOutput,
    transcript: Transcript,
    rubric: Rubric,
    policy: DecisionPolicy,
    verified: Callable[[object], bool],
    human_gates: Mapping[str, str] | None = None,
) -> list[GateRecord]:
    screens = (
        screen_gates(transcript, rubric.heuristic_rules)
        if policy.cross_check_with_lexical_screen
        else {}
    )
    records: list[GateRecord] = []
    for g in out.critical_gates:
        screen = screens.get(g.gate_id)
        notes: list[str] = []
        ev_ok = (
            all(verified(e) for e in g.evidence)
            if g.evidence
            else g.assessment != GateAssessment.VIOLATION
        )
        status = {
            GateAssessment.VIOLATION: AdjudicationStatus.JUDGE_ALLEGED_UNCONFIRMED,
            GateAssessment.NO_VIOLATION: AdjudicationStatus.JUDGE_CLEARED_UNCONFIRMED,
            GateAssessment.UNCERTAIN: AdjudicationStatus.UNCERTAIN,
            GateAssessment.NOT_APPLICABLE: AdjudicationStatus.NOT_APPLICABLE,
        }[g.assessment]
        if g.assessment == GateAssessment.VIOLATION and not g.evidence:
            status = AdjudicationStatus.UNCERTAIN
            notes.append("judge alleged a violation without citing evidence")
        elif g.assessment == GateAssessment.VIOLATION and not any(verified(e) for e in g.evidence):
            status = AdjudicationStatus.UNCERTAIN
            notes.append(
                "none of the judge's evidence for this violation could be verified in the transcript"
            )
        if screen is not None:
            if screen.flag and g.assessment in (
                GateAssessment.NO_VIOLATION,
                GateAssessment.NOT_APPLICABLE,
            ):
                status = AdjudicationStatus.UNCERTAIN
                notes.append(
                    f"lexical screen flags a possible violation ({screen.reason}); judge cleared it"
                )
            elif screen.flag is None and g.assessment == GateAssessment.NO_VIOLATION:
                notes.append(f"lexical screen inconclusive ({screen.reason})")
        human = (human_gates or {}).get(g.gate_id)
        if human:
            status = human_gate_status(human)  # human adjudication supersedes the judge
            notes.append("human adjudication applied")
        records.append(
            GateRecord(
                gate_id=g.gate_id,
                judge_assessment=g.assessment,
                screen_flag=None if screen is None else screen.flag,
                human_assessment=human,
                adjudication_status=status,
                rationale=g.rationale,
                evidence=g.evidence,
                evidence_verified=ev_ok,
                notes=notes,
            )
        )
    return records


def build_evaluation(
    out: JudgeOutput,
    transcript: Transcript,
    rubric: Rubric,
    policy: DecisionPolicy,
    cfg: EvaluatorConfig,
    served_model: str,
    cache_key: str,
    human_gates: Mapping[str, str] | None = None,
) -> Evaluation:
    grounding = verify_evidence(out, transcript)
    gates = build_gate_records(out, transcript, rubric, policy, grounding.is_verified, human_gates)
    dims = {d.dimension: d for d in out.dimensions}
    scores = {k: dims[k].score for k in DIMENSIONS}
    applic = {k: dims[k].applicable for k in DIMENSIONS}
    overall = weighted_score(scores, rubric.weights, applic)
    injection_screen = bool(detect_injection(transcript))
    result = decide(
        overall,
        [g.adjudication_status for g in gates],
        policy,
        injection_flagged=injection_screen or out.injection_attempt_detected,
    )
    notes = list(out.uncertainty_notes)
    if (
        out.claimed_overall_score is not None
        and overall is not None
        and abs(out.claimed_overall_score - overall) > 1
    ):
        notes.append(
            f"judge-claimed total {out.claimed_overall_score} ignored; recomputed {overall:.1f}"
        )
    return Evaluation(
        transcript_id=transcript.transcript_id,
        dataset_version=transcript.dataset_version,
        rubric_version=rubric.rubric_version,
        judge_provider=cfg.provider,
        judge_model=served_model,
        prompt_version=cfg.prompt_version,
        dimension_scores=scores,
        dimension_applicability=applic,
        evidence_by_dimension={k: dims[k].evidence for k in DIMENSIONS},
        evidence_status_by_dimension={k: dims[k].evidence_status for k in DIMENSIONS},
        dimension_rationales={k: dims[k].rationale for k in DIMENSIONS},
        critical_gate_results=gates,
        overall_score=overall,
        decision=result.decision,
        decision_reasons=result.reasons,
        judge_claimed_overall_score=out.claimed_overall_score,
        judge_claimed_decision=out.claimed_decision,
        uncertainty_notes=notes,
        grounding_issues=grounding.issues,
        injection_attempt_detected=out.injection_attempt_detected,
        injection_screen_flag=injection_screen,
        evaluation_config_hash=cfg.hash(),
        cache_key=cache_key,
        pass_threshold=policy.pass_threshold,
    )


class Evaluator:
    def __init__(
        self,
        provider: JudgeProvider,
        rubric: Rubric,
        policy: DecisionPolicy,
        settings: JudgeSettings,
        cache_dir: Path = CACHE_DIR,
        use_cache: bool = True,
        sleep: Callable[[float], None] = time.sleep,
        max_parse_retries: int = 1,
    ):
        self.provider, self.rubric, self.policy, self.settings = provider, rubric, policy, settings
        self.cache_dir = cache_dir
        self.use_cache = use_cache and provider.is_llm
        self.sleep = sleep
        self.max_parse_retries = max_parse_retries
        self.limiter = RateLimiter(
            settings.min_seconds_between_requests if provider.is_llm else 0.0, sleep=sleep
        )
        self.system_prompt = build_system_prompt(rubric)
        self.schema = output_schema()
        self.cfg = EvaluatorConfig(
            provider=provider.name,
            model=provider.model,
            rubric_version=rubric.rubric_version,
            rubric_hash=rubric.content_hash,
            prompt_version=PROMPT_VERSION,
            max_tokens=settings.max_tokens,
            effort=settings.effort if provider.is_llm else "n/a",
            pass_threshold=policy.pass_threshold,
            unconfirmed_gate_policy=policy.unconfirmed_gate_policy,
            route_injection_flagged_passes_to_review=policy.route_injection_flagged_passes_to_review,
            cross_check_with_lexical_screen=policy.cross_check_with_lexical_screen,
        )

    def cache_key(self, t: Transcript) -> str:
        return sha(
            {
                "transcript": transcript_hash(t),
                "dataset_version": t.dataset_version,
                **self.cfg.cache_fields(),
            },
            24,
        )

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def _fail(
        self, t: Transcript, etype: str, msg: str, attempts: int, raw: str | None = None
    ) -> EvaluationFailure:
        return EvaluationFailure(
            transcript_id=t.transcript_id,
            rubric_version=self.rubric.rubric_version,
            judge_provider=self.provider.name,
            judge_model=self.provider.model,
            error_type=etype,
            error_message=msg[:1000],
            attempts=attempts,
            raw_response_excerpt=(raw or "")[:500] or None,
        )

    def evaluate(
        self, t: Transcript, human_gates: Mapping[str, str] | None = None
    ) -> Evaluation | EvaluationFailure:
        key = self.cache_key(t)
        path = self._cache_path(key)
        if self.use_cache and path.exists():
            cached = json.loads(path.read_text(encoding="utf-8"))
            try:
                out = parse_judge_response(cached["raw_response"], t, self.rubric)
                return build_evaluation(
                    out,
                    t,
                    self.rubric,
                    self.policy,
                    self.cfg,
                    cached["served_model"],
                    key,
                    human_gates,
                )
            except MalformedJudgeResponse:
                path.unlink(missing_ok=True)  # corrupt cache entry: fall through to a fresh call

        request = JudgeRequest(
            t.transcript_id,
            self.system_prompt,
            build_user_prompt(t),
            self.schema,
            self.settings.max_tokens,
        )
        total_attempts = 0
        last_raw = None
        for _ in range(self.max_parse_retries + 1):
            outcome = call_with_retries(
                self.provider, request, self.settings.max_retries, self.limiter, self.sleep
            )
            total_attempts += outcome.attempts
            if outcome.error is not None:
                return self._fail(
                    t, type(outcome.error).__name__, str(outcome.error), total_attempts
                )
            assert outcome.response is not None
            last_raw = outcome.response.text
            try:
                out = parse_judge_response(last_raw, t, self.rubric)
            except MalformedJudgeResponse as exc:
                last_err = str(exc)
                continue
            if self.use_cache:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    json.dumps(
                        {
                            "cache_key": key,
                            "served_model": outcome.response.model,
                            "raw_response": last_raw,
                            "config": self.cfg.cache_fields(),
                        }
                    ),
                    encoding="utf-8",
                )
            return build_evaluation(
                out, t, self.rubric, self.policy, self.cfg, outcome.response.model, key, human_gates
            )
        return self._fail(t, "MalformedJudgeResponse", last_err, total_attempts, last_raw)

    def evaluate_many(
        self, transcripts: Iterable[Transcript], progress: Callable[[int, str], None] | None = None
    ) -> tuple[list[Evaluation], list[EvaluationFailure]]:
        evals: list[Evaluation] = []
        fails: list[EvaluationFailure] = []
        for i, t in enumerate(transcripts, start=1):
            res = self.evaluate(t)
            (evals if isinstance(res, Evaluation) else fails).append(res)  # type: ignore[arg-type]
            if progress:
                progress(i, t.transcript_id)
        return evals, fails
