"""Generate reports/*.md from saved artifacts only.

Numbers are read from the analysis/experiment outputs, never typed by hand. When an
experiment or human labels are missing, the relevant section is marked PENDING rather than
fabricated. The final writeup includes a word count so the ~1,500-word target is checkable.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from voice_eval.analysis.business_impact import FORMULAS, BusinessAssumptions, assumptions_table
from voice_eval.config import REPORTS_DIR, DecisionPolicy, load_experiment_defaults
from voice_eval.pipeline import AnalysisBundle, analyse
from voice_eval.rubric_loader import available_rubrics, load_rubric
from voice_eval.schemas import DIMENSIONS, GATE_IDS, utc_now

DISCLAIMERS = [
    "All conversations, people, institutions and policies are fictional and synthetic.",
    "The initial human-labelled sample is only 30 transcripts.",
    "A single annotator cannot establish inter-annotator reliability.",
    "Synthetic scenario expectations are test specifications, not independent human ground truth.",
    "Repeated tuning against the same 30 labels risks overfitting; a held-out sample is reserved but not yet labelled.",
    "Results may not generalise to other models, languages, real calls or financial institutions.",
    "The compliance gates implement a fictional benchmark policy and certify no legal or regulatory compliance.",
]


def _pct(x: float | None) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x * 100:.1f}%"


def _num(x: float | None, nd: int = 2) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


def _ci(m: dict) -> str:
    return f"{_pct(m['value'])} (95% CI {_pct(m['ci_low'])}–{_pct(m['ci_high'])}, n={m['n']})"


def _df(df: pd.DataFrame, floatfmt: int = 3) -> str:
    if df.empty:
        return "_(no rows)_"
    d = df.copy()
    for c in d.select_dtypes("float").columns:
        d[c] = d[c].map(lambda v: "" if pd.isna(v) else f"{v:.{floatfmt}f}")
    return d.to_markdown(index=False)


def _bundles() -> dict[str, AnalysisBundle]:
    return {v: analyse(v) for v in available_rubrics()}


def methodology_md(bundles: dict[str, AnalysisBundle]) -> str:
    r1 = load_rubric("v1")
    defaults = load_experiment_defaults()
    lines = [
        "# Methodology",
        "",
        "_Generated from committed artifacts. All data is synthetic; see disclaimers._",
        "",
        "## 1. Dataset",
        "100 fictional BFSI collections-call transcripts, 20 per scenario category, generated "
        "deterministically from a fixed seed by `src/voice_eval/generation/synthetic_generator.py` "
        "(no LLM involved, so the committed `data/transcripts.jsonl` is byte-reproducible). Each "
        "category contains five sub-scenarios crossed with four agent-quality tiers (exemplary, "
        "adequate, deficient, critical), plus randomised fictional borrower profiles, "
        "communication styles and modifiers (repeated questions, contradictions, agent "
        "uncertainty and five classes of prompt-injection attempt aimed at the judge).",
        "",
        "## 2. Benchmark policy (fictional)",
        f"Policy reference: {r1.policy_reference}",
        "The rubric scores five dimensions 0–4 and defines four critical compliance gates:",
    ]
    for g in r1.critical_gates:
        lines.append(f"- **{g.gate_id}** — {g.name}: {g.violation_definition.strip()}")
    lines += [
        "",
        "## 3. Scoring",
        "A single module (`scoring.py`) computes the weighted score over applicable dimensions "
        "with weights renormalised when a dimension is genuinely not applicable:",
        "",
        "```",
        "overall = 100 * sum_applicable(w_d * score_d/4) / sum_applicable(w_d)",
        "```",
        "Dimension weights: " + ", ".join(f"{d}={r1.weights[d]:.0%}" for d in DIMENSIONS) + ".",
        "A confirmed critical-gate violation forces FAIL regardless of the score. A judge-alleged "
        "but unconfirmed violation, or contradictory evidence, yields REVIEW_REQUIRED until a human "
        "adjudicates. The default pass threshold is "
        f"{DecisionPolicy.from_settings().pass_threshold:g}/100 — an initial configurable cutoff, not a "
        "validated production threshold — and lives in `configs/settings.yaml`, separate from the rubric.",
        "",
        "## 4. LLM-as-judge",
        "The judge returns a strictly validated JSON object (Pydantic). The judge's own claimed "
        "total and decision are stored for audit but never used: Python recomputes both from the "
        "validated dimension scores, applicability rules and gate adjudication. Evidence quotes are "
        "verified verbatim against the cited turn; unverifiable gate allegations are downgraded to "
        "UNCERTAIN. API failures are recorded separately and never converted into a passing score.",
        "",
        "## 5. Prompt-injection defence (not claimed to be perfect)",
        "The rubric and instructions are in the system prompt; the transcript is untrusted data in "
        "the user message, JSON-escaped inside a `<transcript_data>` envelope with `<`/`>` escaped so "
        "transcript text cannot forge the envelope. Tested attack classes: "
        f"{', '.join(sorted(bundles['v1'].transcripts[0].modifiers) or ['see dataset'])}; the full set "
        "is direct instructions, fake system messages, quoted instructions, requests to suppress a "
        "compliance failure and attempts to redefine the scale. "
        f"The dataset contains {sum(1 for t in bundles['v1'].transcripts if any(m.startswith('prompt_injection') for m in t.modifiers))} "
        "injection-bearing transcripts.",
        "",
        "## 6. Human annotation protocol",
        f"A stratified random sample of {defaults['annotation']['sample_size']} transcripts "
        f"(seed {defaults['annotation']['sampling_seed']}, {defaults['annotation']['per_category']} per category) "
        "is frozen to `data/annotation_sample.json` before any judge output is inspected. Humans "
        "annotate independently of judge outputs; labels are stored separately and frozen with a "
        "SHA-256 hash before agreement is computed. A held-out sample is reserved for validation.",
        "",
        "## 7. Metrics",
        "Per-dimension exact and within-one agreement, MAE, and Cohen's kappa (unweighted and "
        "quadratic-weighted); binary PASS/FAIL precision, recall, F1, false-pass and false-fail "
        "rates with explicit denominators; three-way decision agreement; per-gate agreement. "
        "Proportions use Wilson score intervals; kappa and MAE use a seeded percentile bootstrap. "
        "REVIEW_REQUIRED is mapped to the binary comparison per a configurable policy "
        f"(default: {DecisionPolicy.from_settings().review_required_binary_mapping}); sensitivity to that "
        "choice is reported.",
        "",
        "## Disclaimers",
        *[f"- {d}" for d in DISCLAIMERS],
        "",
    ]
    return "\n".join(lines)


def disagreement_md(bundles: dict[str, AnalysisBundle]) -> str:
    lines = [
        "# Disagreement analysis",
        "",
        "_Two references are reported separately: independent human labels (the research "
        "result) and the synthetic test specification (a sanity check, not ground truth)._",
        "",
    ]
    for v, b in bundles.items():
        lines += [
            f"## Rubric {v}",
            f"Experiment: `{b.experiment.id if b.experiment else 'none'}` "
            f"[{b.experiment.manifest.get('provenance') if b.experiment else 'n/a'}]",
            "",
        ]
        if not b.evals:
            lines += ["_No evaluation available — PENDING._", ""]
            continue
        if not b.spec_register.empty:
            counts = b.spec_register["root_cause_category"].value_counts()
            lines += [
                "**Judge vs synthetic spec — suggested root causes:**",
                _df(counts.rename_axis("root_cause").reset_index(name="count")),
                "",
            ]
            ex = b.spec_register.head(4)[
                ["transcript_id", "dimension", "human_score", "judge_score", "root_cause_category"]
            ]
            lines += ["Representative records (fictional excerpts):", _df(ex), ""]
        else:
            lines += ["Judge matches the synthetic spec on all gates and decision bands.", ""]
        if b.agreement is not None and not b.human_register.empty:
            counts = b.human_register["root_cause_category"].value_counts()
            lines += [
                "**Judge vs human labels — suggested root causes:**",
                _df(counts.rename_axis("root_cause").reset_index(name="count")),
                "",
            ]
        elif b.agreement is None:
            lines += ["**Judge vs human labels:** PENDING — human annotations incomplete.", ""]
        else:
            lines += ["**Judge vs human labels:** full agreement on the labelled subset.", ""]
    return "\n".join(lines)


def threshold_md(bundles: dict[str, AnalysisBundle]) -> str:
    lines = [
        "# Threshold-sensitivity results",
        "",
        "_Critical-gate overrides remain active at every cutoff. The full-synthetic population "
        "has no human ground truth; the human-labelled columns are populated only when the "
        "30-label batch is complete._",
        "",
    ]
    for v, b in bundles.items():
        lines += [f"## Rubric {v}"]
        if b.thresholds.empty:
            lines += ["_PENDING — no evaluation._", ""]
            continue
        cols = [
            "cutoff",
            "n_pass",
            "n_fail",
            "n_review_required",
            "pass_rate",
            "critical_gate_overrides",
            "est_reviewed_calls_per_month",
            "human_agreement",
            "false_pass_count",
            "false_fail_count",
        ]
        lines += [_df(b.thresholds[cols]), ""]
        if not b.changes.empty:
            lines += [
                "Calls that change classification between consecutive cutoffs:",
                _df(b.changes.head(12)),
                "",
            ]
    return "\n".join(lines)


def _n_words(text: str) -> int:
    body = "\n".join(ln for ln in text.splitlines() if not ln.strip().startswith(("|", "#", "```")))
    return len(body.split())


def final_writeup_md(bundles: dict[str, AnalysisBundle]) -> str:
    b1 = bundles["v1"]
    pol = DecisionPolicy.from_settings()
    exp = b1.experiment
    prov = exp.manifest.get("provenance") if exp else "none"
    model = exp.manifest.get("judge_model") if exp else "n/a"
    scores = [e.overall_score for e in b1.evals if e.overall_score is not None]
    mean_score = sum(scores) / len(scores) if scores else float("nan")
    human_done = b1.agreement is not None
    L = [
        "# Can an LLM reliably evaluate conversational-AI collections calls?",
        "",
        f"_Status: judge provenance **{prov}**, served model **{model}**. "
        f"Human-agreement validation: **{'complete' if human_done else 'PENDING'}** "
        f"({len(b1.labels.annotations)}/{b1.labels.n_required} frozen labels)._",
        "",
        "## 1. Executive summary",
        "This project is a reproducible harness for the question of whether an LLM can reliably "
        "judge the quality, compliance and resolution effectiveness of collections-call agents, and "
        "whether human feedback improves that judge. It ships 100 fictional transcripts, three "
        "versioned rubrics, a schema-validated LLM-as-judge whose score and decision are recomputed "
        "in Python, an independent human-annotation workflow, agreement and disagreement analysis, "
        "rubric calibration, and a threshold-sensitivity and illustrative-cost study. It is a "
        "benchmark, not a production collections system, and it certifies no real compliance. The "
        "value of the harness is methodological: it demonstrates a defensible way to evaluate an "
        "evaluator, with every number traceable to a committed artifact and every absent number "
        "declared PENDING rather than invented. Where a reader expects a headline agreement figure "
        "they will instead find either a calibrated interval with its denominator and method stated, "
        "or an explicit statement that the labels needed to compute it do not yet exist.",
        "",
        "## 2. Motivation",
        "Voice agents in banking collections operate under conduct and privacy constraints where a "
        "single bad call carries regulatory and human cost. Manual QA samples a few percent of "
        "calls. An LLM judge could review every call — but only if we can show where it agrees with "
        "trained humans and, more importantly, where and how it fails. This harness is built to "
        "surface those failures honestly rather than to advertise a headline agreement number. The "
        "central design commitment is that the system never trusts the judge's own arithmetic or "
        "its self-reported verdict: those are stored only for audit. Instead the weighted score and "
        "the operational decision are recomputed deterministically in Python from the validated "
        "dimension scores, the rubric's applicability rules, and the adjudicated critical gates. "
        "This separation means a judge can be wrong about the total while still being useful about "
        "the evidence, and it makes the whole pipeline auditable: given the same validated judge "
        "output, two people will always obtain the same decision. It also means that measuring a "
        "judge is partly measuring the rubric, which is why rubric calibration is a first-class "
        "part of the workflow rather than an afterthought.",
        "",
        "## 3. Dataset design",
        f"The {len(b1.transcripts)} transcripts span five scenario categories — first-time "
        "defaulter, repeat delinquent, wrong-number/identity mismatch, payment dispute, and "
        "hostile/distressed — with 20 each. Five sub-scenarios per category are crossed with four "
        "agent-quality tiers, so the set exercises exemplary handling, borderline calls, "
        "non-critical failures and deliberate critical violations (threats, pre-verification or "
        "third-party disclosure, ignored stop-contact or escalation). Borrower profiles, "
        "communication styles, conversation length and modifiers vary; critical violations are "
        "sometimes embedded in otherwise-polite calls so that the gate override is genuinely tested. "
        "The generator is deterministic and the committed file is the frozen experimental artifact; "
        "`intended_agent_behavior` and `expected_critical_violations` are synthetic test "
        "specifications, not independent ground truth.",
        "",
        "## 4. Rubric design",
        "Each rubric scores intent capture (20%), objection handling (20%), compliance adherence "
        "(30%), fallback grace (15%) and resolution quality (15%) on an anchored 0–4 scale with a "
        "separate anchor, evidence requirement, positive/negative examples and applicability rule "
        "per dimension. Payment is explicitly not the only successful outcome: dispute referrals, "
        "escalations, safe terminations and appropriately routed unresolved calls can score full "
        "marks. Four configurable critical gates sit outside the weighted score.",
        "",
        "## 5. LLM-as-judge methodology",
        "The judge returns strict JSON with per-dimension scores, evidence (turn id plus verbatim "
        "quote), rationales, gate assessments and uncertainty notes. Python re-validates the schema, "
        "verifies each quote against the cited turn after Unicode normalisation, recomputes the "
        "weighted score and the PASS/FAIL/REVIEW_REQUIRED decision, and ignores the judge's own "
        "claimed total. A gate violation whose supporting quote cannot be found verbatim in the "
        "cited turn is downgraded to UNCERTAIN, which routes the call to REVIEW_REQUIRED rather than "
        "letting an ungrounded allegation fail it; a confirmed violation, by contrast, overrides the "
        "score outright. Responses are retried with exponential backoff on transient errors (rate "
        "limits, timeouts, overloaded servers) and fail fast on permanent ones (authentication, "
        "refusals); every failure is recorded in a separate failures file and is never silently "
        "converted into a passing score. Results are cached on a key combining the transcript "
        "content, dataset version, rubric version, model identifier and prompt version, so reruns "
        "are cheap and comparable. Transcript text is treated as untrusted input; tested "
        "prompt-injection classes are evaluated as borrower speech rather than obeyed. Injection "
        "resistance is tested, not claimed perfect.",
        "",
        "## 6. Human annotation protocol",
        f"A stratified sample of {b1.labels.n_required} transcripts is frozen before any judge "
        "output is inspected; humans label independently, and the batch is hashed before agreement "
        "is computed. A held-out sample is reserved for a stronger generalisation claim.",
        "",
        "## 7. Agreement results",
    ]
    if human_done:
        bm = b1.agreement.binary
        L += [
            f"On the {bm['n']}-call labelled subset (threshold {pol.pass_threshold:g}, REVIEW_REQUIRED "
            f"mapped {pol.review_required_binary_mapping}), binary PASS/FAIL raw agreement was "
            f"{_ci(bm['raw_agreement'])}, Cohen's kappa {_num(bm['kappa']['value'])}, with "
            f"{bm['false_pass_count']} false passes and {bm['false_fail_count']} false fails. "
            "Per-dimension exact agreement (small n; wide intervals): "
            + ", ".join(
                f"{d} {_pct(m['exact_agreement']['value'])}"
                for d, m in b1.agreement.per_dimension.items()
            )
            + ".",
            "Because n is 30, these intervals are wide and must not be read as proof of "
            "generalisation.",
        ]
    else:
        L += [
            "**PENDING.** No agreement percentages are reported because the 30-label human batch is "
            "not yet complete. The pipeline refuses to compute or display agreement numbers without "
            "the underlying labels. Run the annotation workflow, freeze the batch, then `voice-eval "
            "agreement`."
        ]
    L += [
        "",
        "## 8. Disagreement analysis",
        "The harness builds a disagreement register (per transcript, dimension, both rationales, the "
        "relevant evidence, a suggested root cause and a change status) and a separate "
        "spec-conformance register against the synthetic specification. Root-cause categories cover "
        "ambiguous anchors, missing evidence, unsupported inference, over-strict/over-lenient "
        "scoring, incorrect applicability, tone/outcome confusion, gate misclassification and "
        "dataset ambiguity.",
        "",
        "## 9. Rubric evolution",
        "Three immutable rubric versions are maintained. v1 is the baseline; v2 clarifies ambiguous "
        "anchors and applicability; v3 makes targeted calibration changes. Each change records the "
        "previous and updated definitions, motivation, expected improvement and potential "
        "regressions, and versions are compared on the same frozen transcripts and labels. v3 is not "
        "assumed better: improvement is measured, and tuning against the same 30 labels is flagged "
        "as an overfitting risk pending the held-out sample. Concretely, v2 widens the objection "
        "handling applicability rule so that a third party denying their identity still counts as "
        "pushback (preventing judges from inflating agreement by marking hard wrong-number calls "
        "not-applicable), sharpens the fallback-grace 2-versus-3 anchor boundary, and adds a carve "
        "out to the stop-contact gate for a single clarifying question that is immediately followed "
        "by compliance. v3 then tightens the evidence bar for a gate violation (an unverifiable "
        "allegation is downgraded to review rather than treated as a failure), makes explicit in the "
        "compliance dimension that borrower rudeness is never the agent's fault and that a coerced "
        "payment is a problem rather than a mitigant, and restates in the top resolution anchor that "
        "correct non-payment outcomes deserve full marks. Because the generator and the heuristic "
        "baseline share vocabulary, the offline demo cannot itself demonstrate calibration gains; "
        "that comparison is meaningful only against independent human labels, which is precisely why "
        "the pipeline refuses to report it until those labels exist.",
        "",
        "## 10. Threshold-sensitivity results",
        f"Mean recomputed score on the current ({prov}) run is {_num(mean_score, 1)}/100. Sweeping "
        "the threshold over 50–90 moves pass and review rates while critical overrides stay active; "
        "the per-cutoff table, the calls that change classification, and (when labels exist) false "
        "passes versus false fails are written to `results/analysis/`.",
        "",
        "## 11. Illustrative operational implications",
        "A transparent cost model estimates monthly review workload and cost from configurable, "
        "explicitly hypothetical assumptions, assigning each call to exactly one review bucket to "
        "avoid double counting: review-required calls first, then fails, then borderline passes, "
        "then a random audit slice of the remaining passes. Review hours and expense follow from "
        "those volumes; false-pass exposure and false-fail opportunity cost are added only when the "
        "human-labelled subset supplies the error rates, and the model is explicitly flagged as "
        "partial otherwise rather than filling the gap with a guess. Every monetary input is "
        "surfaced in the dashboard with its unit and marked hypothetical. The lowest-cost threshold "
        "is never presented as a recommendation: compliance and risk tolerance take precedence over "
        "this illustrative optimisation, and a capacity-shortfall warning fires when the implied "
        "review hours exceed the configured reviewer capacity so that a cheap-looking threshold that "
        "is operationally infeasible is not mistaken for a good one.",
        "",
        "## 12. Limitations",
        *[f"- {d}" for d in DISCLAIMERS],
        "",
        "## 13. Reproducibility",
        "```bash",
        "uv sync",
        "uv run voice-eval generate-dataset   # frozen; verify with --verify",
        "uv run voice-eval validate-dataset",
        "uv run voice-eval demo   # offline heuristic baseline + analysis + reports",
        "uv run voice-eval evaluate --provider anthropic --rubric v1   # live LLM (needs ANTHROPIC_API_KEY)",
        "uv run pytest",
        "```",
        "",
        "## 14. Conclusion",
        "The deliverable is an honest measurement instrument. Where human labels are complete it "
        "reports agreement with calibrated uncertainty; where they are not, it says PENDING rather "
        "than inventing a result. That discipline — recomputing every decision, grounding every "
        "claim in cited evidence, separating synthetic expectations from human judgement, and "
        "refusing to fabricate — is the point of the project.",
        "",
    ]
    text = "\n".join(L)
    return text + f"\n_Word count (prose, excluding tables/headings/code): ~{_n_words(text)}._\n"


def business_md() -> str:
    a = BusinessAssumptions.defaults()
    return "\n".join(
        [
            "# Illustrative business-impact assumptions",
            "",
            "All values are hypothetical and illustrative; the model claims no realised savings.",
            "",
            assumptions_table(a).to_markdown(index=False),
            "",
            "## Formulas",
            "```",
            FORMULAS.strip(),
            "```",
            "",
        ]
    )


def build_all(out_dir: Path = REPORTS_DIR) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    bundles = _bundles()
    written = []
    for name, text in (
        ("methodology.md", methodology_md(bundles)),
        ("disagreement_analysis.md", disagreement_md(bundles)),
        ("threshold_sensitivity.md", threshold_md(bundles)),
        ("business_impact_assumptions.md", business_md()),
        ("final_writeup.md", final_writeup_md(bundles)),
    ):
        p = out_dir / name
        p.write_text(
            text.rstrip() + f"\n\n---\n_Built {utc_now()} from committed artifacts._\n",
            encoding="utf-8",
        )
        written.append(str(p.relative_to(out_dir.parent)))
    _ = (GATE_IDS,)
    return written
