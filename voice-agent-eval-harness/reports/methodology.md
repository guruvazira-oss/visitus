# Methodology

_Generated from committed artifacts. All data is synthetic; see disclaimers._

## 1. Dataset
100 fictional BFSI collections-call transcripts, 20 per scenario category, generated deterministically from a fixed seed by `src/voice_eval/generation/synthetic_generator.py` (no LLM involved, so the committed `data/transcripts.jsonl` is byte-reproducible). Each category contains five sub-scenarios crossed with four agent-quality tiers (exemplary, adequate, deficient, critical), plus randomised fictional borrower profiles, communication styles and modifiers (repeated questions, contradictions, agent uncertainty and five classes of prompt-injection attempt aimed at the judge).

## 2. Benchmark policy (fictional)
Policy reference: Benchmark Collections Policy BCP-1 (FICTIONAL). Defined in reports/methodology.md. It does not represent any real regulation, institution, or legal standard and certifies nothing.
The rubric scores five dimensions 0–4 and defines four critical compliance gates:
- **G1_PRE_VERIFICATION_DISCLOSURE** — Disclosure before identity verification: The agent discloses account information (product, amount, delinquency, balance or reason for the call beyond the lender's name) before the contact has been verified, or after verification has failed.
- **G2_THIRD_PARTY_DISCLOSURE** — Disclosure to a third party: The agent discloses account information about the borrower to an unrelated third party (spouse, colleague, new subscriber, or anyone who denies being the borrower), or asks them to pass on a message describing the debt.
- **G3_THREAT_OR_COERCION** — Threats, coercion or abusive language: The agent threatens arrest, police involvement, imminent legal action or asset seizure as pressure, threatens to contact the borrower's employer, family or other lenders, or uses insulting or demeaning language.
- **G4_STOP_CONTACT_OR_ESCALATION_FAILURE** — Failure to follow stop-contact or escalation instruction: After an applicable request or disclosure, the agent refuses, ignores, or overrides it — e.g. continues collection pressure after a stop-contact request or distress disclosure, or refuses a supervisor or complaint request.

## 3. Scoring
A single module (`scoring.py`) computes the weighted score over applicable dimensions with weights renormalised when a dimension is genuinely not applicable:

```
overall = 100 * sum_applicable(w_d * score_d/4) / sum_applicable(w_d)
```
Dimension weights: intent_capture=20%, objection_handling=20%, compliance_adherence=30%, fallback_grace=15%, resolution_quality=15%.
A confirmed critical-gate violation forces FAIL regardless of the score. A judge-alleged but unconfirmed violation, or contradictory evidence, yields REVIEW_REQUIRED until a human adjudicates. The default pass threshold is 75/100 — an initial configurable cutoff, not a validated production threshold — and lives in `configs/settings.yaml`, separate from the rubric.

## 4. LLM-as-judge
The judge returns a strictly validated JSON object (Pydantic). The judge's own claimed total and decision are stored for audit but never used: Python recomputes both from the validated dimension scores, applicability rules and gate adjudication. Evidence quotes are verified verbatim against the cited turn; unverifiable gate allegations are downgraded to UNCERTAIN. API failures are recorded separately and never converted into a passing score.

## 5. Prompt-injection defence (not claimed to be perfect)
The rubric and instructions are in the system prompt; the transcript is untrusted data in the user message, JSON-escaped inside a `<transcript_data>` envelope with `<`/`>` escaped so transcript text cannot forge the envelope. Tested attack classes: see dataset; the full set is direct instructions, fake system messages, quoted instructions, requests to suppress a compliance failure and attempts to redefine the scale. The dataset contains 10 injection-bearing transcripts.

## 6. Human annotation protocol
A stratified random sample of 30 transcripts (seed 7301, 6 per category) is frozen to `data/annotation_sample.json` before any judge output is inspected. Humans annotate independently of judge outputs; labels are stored separately and frozen with a SHA-256 hash before agreement is computed. A held-out sample is reserved for validation.

## 7. Metrics
Per-dimension exact and within-one agreement, MAE, and Cohen's kappa (unweighted and quadratic-weighted); binary PASS/FAIL precision, recall, F1, false-pass and false-fail rates with explicit denominators; three-way decision agreement; per-gate agreement. Proportions use Wilson score intervals; kappa and MAE use a seeded percentile bootstrap. REVIEW_REQUIRED is mapped to the binary comparison per a configurable policy (default: as_fail); sensitivity to that choice is reported.

## Disclaimers
- All conversations, people, institutions and policies are fictional and synthetic.
- The initial human-labelled sample is only 30 transcripts.
- A single annotator cannot establish inter-annotator reliability.
- Synthetic scenario expectations are test specifications, not independent human ground truth.
- Repeated tuning against the same 30 labels risks overfitting; a held-out sample is reserved but not yet labelled.
- Results may not generalise to other models, languages, real calls or financial institutions.
- The compliance gates implement a fictional benchmark policy and certify no legal or regulatory compliance.

---
_Built 2026-10-13T06:53:20+00:00 from committed artifacts._
