# Voice Agent Evaluation Harness — BFSI Collections Benchmark

A reproducible, open-source harness for the question: **can an LLM reliably evaluate the
quality, compliance and resolution effectiveness of conversational-AI collections agents, and
can human feedback improve that evaluation?**

It ships 100 **fictional** banking-collections call transcripts, three versioned scoring
rubrics, a schema-validated **LLM-as-judge** whose score and decision are recomputed in
Python, an independent **human-annotation** workflow, agreement/disagreement analysis, rubric
calibration (v1→v2→v3), a **threshold-sensitivity** study, an illustrative operational-cost
model, and an enterprise-style **Streamlit dashboard** that runs fully offline.

> **This is a benchmark, not a product.** It is not a live debt-collection agent, dialer,
> payment processor, or compliance-certification tool. All conversations, people, institutions
> and the compliance policy are fictional. The bundled "judge" demo is a transparent heuristic
> baseline — **not an LLM** — so you can explore everything without an API key.

## Problem statement

Manual QA reviews a few percent of collections calls, yet a single non-compliant call carries
regulatory and human cost. An LLM judge could review every call — but only if we can show
where it agrees with trained humans and, crucially, where and how it fails. This harness is
built to surface those failures honestly: it recomputes every decision deterministically,
grounds every conclusion in cited transcript evidence, keeps synthetic expectations separate
from human judgement, and refuses to report an agreement number until the human labels that
back it actually exist.

## Architecture

```mermaid
flowchart TD
    subgraph Data["Frozen artifacts"]
        G[synthetic_generator.py<br/>deterministic, no LLM] --> T[(transcripts.jsonl<br/>100 fictional calls)]
        R[(rubrics v1/v2/v3<br/>immutable YAML)]
        S[(settings.yaml<br/>threshold + policy)]
    end
    subgraph Judge["LLM-as-judge"]
        T --> P[prompts.py<br/>untrusted-data envelope]
        R --> P
        P --> PR[provider.py<br/>anthropic | heuristic | mock]
        PR --> PA[response_parser.py<br/>strict schema + evidence grounding]
        PA --> EV[evaluator.py]
        S --> SC[scoring.py<br/>recompute score + decision]
        EV --> SC
        SC --> E[(evaluations.jsonl<br/>+ failures.jsonl)]
    end
    subgraph Human["Independent annotation"]
        T --> SA[frozen stratified sample]
        SA --> AN[annotation studio<br/>SQLite store]
        AN --> HL[(human_annotations.csv<br/>hashed batch)]
    end
    subgraph Analysis["Analysis & reporting"]
        E --> AG[agreement.py<br/>Wilson / bootstrap CIs]
        HL --> AG
        E --> DS[disagreement.py]
        E --> TH[threshold_sensitivity.py]
        E --> BI[business_impact.py]
        AG --> OUT[(results/analysis + figures)]
        DS --> OUT
        TH --> OUT
        BI --> OUT
        OUT --> RPT[reports/*.md]
        OUT --> UI[Streamlit dashboard]
    end
```

## Tech stack

Python 3.12+ · `uv` · Pydantic v2 · Pandas/NumPy · SciPy & scikit-learn (kappa, confusion
matrices, confidence intervals) · Plotly · Typer CLI · Streamlit · SQLite · the official
`anthropic` SDK (schema-constrained structured output, behind a provider adapter) · pytest ·
Ruff · GitHub Actions.

## Dataset design

100 transcripts, 20 in each of five scenario categories, generated deterministically from a
fixed seed (byte-reproducible; the committed file is the frozen experimental artifact):

| Code | Category | Covers |
|------|----------|--------|
| A | `FIRST_TIME_DEFAULTER` | confusion, apology, clarification, extension, supervisor requests |
| B | `REPEAT_DELINQUENT` | broken promises, date avoidance, repeated extensions, frustration, partial payment |
| C | `WRONG_NUMBER_OR_IDENTITY_MISMATCH` | third party, denial, reassigned number, failed verification, workplace |
| D | `PAYMENT_DISPUTE` | already-paid, amount, account status, written verification, contradictory |
| E | `HOSTILE_OR_DISTRESSED` | anger, complaint threat, refusal, distress, hostile-then-cooperative |

Each category crosses five sub-scenarios with four agent-quality tiers (exemplary / adequate /
deficient / critical), plus randomised fictional profiles, communication styles, variable
length, and modifiers: repeated questions, contradictions, agent uncertainty, and five classes
of **prompt-injection** aimed at the judge. `intended_agent_behavior` and
`expected_critical_violations` are *synthetic test specifications*, not independent ground truth.

## Rubric and scoring model

Five dimensions scored 0–4 on an anchored scale, each with per-score anchors, evidence
requirements, examples, applicability rules and common-mistake notes:

| Dimension | Weight |
|-----------|-------:|
| Intent capture | 20% |
| Objection handling | 20% |
| Compliance adherence | 30% |
| Fallback grace | 15% |
| Resolution quality | 15% |

`overall = 100 × Σ_applicable(wᵈ · scoreᵈ/4) / Σ_applicable(wᵈ)` — weights renormalise over
applicable dimensions. Four **critical gates** (pre-verification disclosure, third-party
disclosure, threats/coercion, stop-contact/escalation failure) sit outside the weighted score:
a *confirmed* violation forces FAIL; a judge-*alleged* but unconfirmed one yields
REVIEW_REQUIRED. The 75/100 threshold and the gate policy live in `configs/settings.yaml`,
separate from the rubric. Payment is **not** the only successful outcome.

## Judge architecture

The judge returns strict JSON (Pydantic). Its claimed total and decision are stored for audit
only — Python recomputes both. Evidence quotes are verified verbatim against the cited turn;
ungrounded gate allegations are downgraded to UNCERTAIN. Transcript text is untrusted data in a
JSON-escaped `<transcript_data>` envelope; injection attempts are detected and surfaced, never
obeyed (resistance is tested, not claimed perfect). API failures are recorded separately and
never become a passing score. Results are cached by transcript + rubric + model + prompt.

## Human annotation & calibration

A stratified 30-transcript sample is frozen **before** any judge output is inspected; humans
label independently in the dashboard (SQLite store, overwrite protection), the batch is frozen
with a SHA-256 hash, and only then is agreement computed. Agreement metrics — exact/within-one
agreement, MAE, Cohen's κ (unweighted & quadratic), PASS/FAIL precision/recall/F1, false-pass
and false-fail rates, per-gate agreement — carry explicit denominators and confidence intervals
(Wilson for proportions, seeded bootstrap otherwise). **With no human labels yet, the pipeline
reports PENDING and computes no agreement numbers.** A held-out sample is reserved for
validation; v1→v2→v3 are compared on the same frozen set, with overfitting flagged.

## Threshold analysis & business impact

A sweep over cutoffs 50–90 (critical overrides always active) reports pass/fail/review rates,
which calls change classification, and — on the labelled subset — false passes vs false fails.
A transparent cost model assigns each call to exactly one review bucket (no double counting)
from explicitly hypothetical, configurable assumptions. The lowest-cost threshold is **never**
presented as a recommendation.

## Installation

```bash
uv sync
```

Copy `.env.example` to `.env` and add `ANTHROPIC_API_KEY` **only** for live LLM runs. The demo,
dashboard and tests need no key.

## Quick start (offline, no API key)

```bash
uv run voice-eval generate-dataset        # frozen; verify with --verify
uv run voice-eval validate-dataset
uv run voice-eval demo                     # heuristic baseline + analysis + reports for v1/v2/v3
uv run voice-eval dashboard                # open the Streamlit app
```

## Live LLM evaluation

```bash
uv run voice-eval evaluate --provider anthropic --rubric v1          # all 100
uv run voice-eval evaluate --provider anthropic --rubric v1 --ids BFSI-A-001,BFSI-C-004
uv run voice-eval agreement --rubric v1     # after human labels are frozen
uv run voice-eval thresholds --rubric v1
```

## CLI commands

`generate-dataset`, `validate-dataset`, `list-rubrics`, `evaluate`,
`create-annotation-sample`, `export-template`, `import-annotations`, `export-annotations`,
`annotation-status`, `freeze-annotations`, `agreement`, `disagreements`, `thresholds`,
`analyze-all`, `charts`, `report`, `demo`, `dashboard`, `test`. See `uv run voice-eval --help`.
Equivalent `scripts/*.py` wrappers exist (`uv run python scripts/validate_dataset.py`, etc.),
and a `Makefile` provides `make setup|dataset|demo|test|dashboard|lint|format`.

## Dashboard

Six pages — Executive overview, Transcript explorer, Human annotation studio, Judge
calibration, Threshold lab, Experiment registry. No API calls are made from the dashboard;
every dataset is labelled by provenance (synthetic / saved demo / LLM / human). Capture
screenshots with `uv run voice-eval dashboard` once running.

## Tests

```bash
uv run pytest        # 99 tests; no paid API calls (mock + heuristic providers)
uv run ruff check . && uv run ruff format --check .
```

CI (`.github/workflows/tests.yml`) runs lint, format-check, dataset reproducibility and the
full suite on every push and PR.

## Repository structure

```
app.py                  Streamlit dashboard (6 pages)
configs/                settings.yaml, experiment_defaults.yaml, rubrics/rubric_v{1,2,3}.yaml
data/                   transcripts.jsonl (frozen), manifest, annotation sample + template
src/voice_eval/         config, schemas, scoring, rubric/dataset loaders, database
  generation/           deterministic synthetic generator
  judge/                base, provider, prompts, evaluator, response_parser, screens, heuristic
  annotation/           annotation_service, import_export
  analysis/             agreement, confusion, disagreement, threshold_sensitivity,
                        business_impact, confidence_intervals
  reporting/            report_builder, charts, experiment_registry
  cli.py                Typer CLI          pipeline.py  shared orchestration
scripts/                thin CLI wrappers       tests/   pytest suite
results/                demo/, experiments/, analysis/, figures/, cache/
reports/                methodology, disagreement_analysis, threshold_sensitivity, final_writeup
```

## Limitations

- All data is synthetic; the compliance policy is fictional and certifies nothing.
- The initial human sample is 30 transcripts; a single annotator cannot establish
  inter-annotator reliability; held-out validation is pending.
- Synthetic expectations are not human ground truth; the heuristic baseline is not an LLM and,
  sharing vocabulary with the generator, is an optimistic upper bound.
- Results may not generalise to other models, languages, real calls or institutions.

## Future improvements

Multiple independent annotators with inter-annotator reliability; the held-out validation run;
additional judge providers behind the adapter; adversarial-robustness expansion; per-dimension
calibration curves; richer vulnerability handling.

## License

MIT — see [LICENSE](LICENSE).
