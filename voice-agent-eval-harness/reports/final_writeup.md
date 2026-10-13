# Can an LLM reliably evaluate conversational-AI collections calls?

_Status: judge provenance **demo_heuristic**, served model **heuristic-baseline-v1**. Human-agreement validation: **PENDING** (0/30 frozen labels)._

## 1. Executive summary
This project is a reproducible harness for the question of whether an LLM can reliably judge the quality, compliance and resolution effectiveness of collections-call agents, and whether human feedback improves that judge. It ships 100 fictional transcripts, three versioned rubrics, a schema-validated LLM-as-judge whose score and decision are recomputed in Python, an independent human-annotation workflow, agreement and disagreement analysis, rubric calibration, and a threshold-sensitivity and illustrative-cost study. It is a benchmark, not a production collections system, and it certifies no real compliance. The value of the harness is methodological: it demonstrates a defensible way to evaluate an evaluator, with every number traceable to a committed artifact and every absent number declared PENDING rather than invented. Where a reader expects a headline agreement figure they will instead find either a calibrated interval with its denominator and method stated, or an explicit statement that the labels needed to compute it do not yet exist.

## 2. Motivation
Voice agents in banking collections operate under conduct and privacy constraints where a single bad call carries regulatory and human cost. Manual QA samples a few percent of calls. An LLM judge could review every call — but only if we can show where it agrees with trained humans and, more importantly, where and how it fails. This harness is built to surface those failures honestly rather than to advertise a headline agreement number. The central design commitment is that the system never trusts the judge's own arithmetic or its self-reported verdict: those are stored only for audit. Instead the weighted score and the operational decision are recomputed deterministically in Python from the validated dimension scores, the rubric's applicability rules, and the adjudicated critical gates. This separation means a judge can be wrong about the total while still being useful about the evidence, and it makes the whole pipeline auditable: given the same validated judge output, two people will always obtain the same decision. It also means that measuring a judge is partly measuring the rubric, which is why rubric calibration is a first-class part of the workflow rather than an afterthought.

## 3. Dataset design
The 100 transcripts span five scenario categories — first-time defaulter, repeat delinquent, wrong-number/identity mismatch, payment dispute, and hostile/distressed — with 20 each. Five sub-scenarios per category are crossed with four agent-quality tiers, so the set exercises exemplary handling, borderline calls, non-critical failures and deliberate critical violations (threats, pre-verification or third-party disclosure, ignored stop-contact or escalation). Borrower profiles, communication styles, conversation length and modifiers vary; critical violations are sometimes embedded in otherwise-polite calls so that the gate override is genuinely tested. The generator is deterministic and the committed file is the frozen experimental artifact; `intended_agent_behavior` and `expected_critical_violations` are synthetic test specifications, not independent ground truth.

## 4. Rubric design
Each rubric scores intent capture (20%), objection handling (20%), compliance adherence (30%), fallback grace (15%) and resolution quality (15%) on an anchored 0–4 scale with a separate anchor, evidence requirement, positive/negative examples and applicability rule per dimension. Payment is explicitly not the only successful outcome: dispute referrals, escalations, safe terminations and appropriately routed unresolved calls can score full marks. Four configurable critical gates sit outside the weighted score.

## 5. LLM-as-judge methodology
The judge returns strict JSON with per-dimension scores, evidence (turn id plus verbatim quote), rationales, gate assessments and uncertainty notes. Python re-validates the schema, verifies each quote against the cited turn after Unicode normalisation, recomputes the weighted score and the PASS/FAIL/REVIEW_REQUIRED decision, and ignores the judge's own claimed total. A gate violation whose supporting quote cannot be found verbatim in the cited turn is downgraded to UNCERTAIN, which routes the call to REVIEW_REQUIRED rather than letting an ungrounded allegation fail it; a confirmed violation, by contrast, overrides the score outright. Responses are retried with exponential backoff on transient errors (rate limits, timeouts, overloaded servers) and fail fast on permanent ones (authentication, refusals); every failure is recorded in a separate failures file and is never silently converted into a passing score. Results are cached on a key combining the transcript content, dataset version, rubric version, model identifier and prompt version, so reruns are cheap and comparable. Transcript text is treated as untrusted input; tested prompt-injection classes are evaluated as borrower speech rather than obeyed. Injection resistance is tested, not claimed perfect.

## 6. Human annotation protocol
A stratified sample of 30 transcripts is frozen before any judge output is inspected; humans label independently, and the batch is hashed before agreement is computed. A held-out sample is reserved for a stronger generalisation claim.

## 7. Agreement results
**PENDING.** No agreement percentages are reported because the 30-label human batch is not yet complete. The pipeline refuses to compute or display agreement numbers without the underlying labels. Run the annotation workflow, freeze the batch, then `voice-eval agreement`.

## 8. Disagreement analysis
The harness builds a disagreement register (per transcript, dimension, both rationales, the relevant evidence, a suggested root cause and a change status) and a separate spec-conformance register against the synthetic specification. Root-cause categories cover ambiguous anchors, missing evidence, unsupported inference, over-strict/over-lenient scoring, incorrect applicability, tone/outcome confusion, gate misclassification and dataset ambiguity.

## 9. Rubric evolution
Three immutable rubric versions are maintained. v1 is the baseline; v2 clarifies ambiguous anchors and applicability; v3 makes targeted calibration changes. Each change records the previous and updated definitions, motivation, expected improvement and potential regressions, and versions are compared on the same frozen transcripts and labels. v3 is not assumed better: improvement is measured, and tuning against the same 30 labels is flagged as an overfitting risk pending the held-out sample. Concretely, v2 widens the objection handling applicability rule so that a third party denying their identity still counts as pushback (preventing judges from inflating agreement by marking hard wrong-number calls not-applicable), sharpens the fallback-grace 2-versus-3 anchor boundary, and adds a carve out to the stop-contact gate for a single clarifying question that is immediately followed by compliance. v3 then tightens the evidence bar for a gate violation (an unverifiable allegation is downgraded to review rather than treated as a failure), makes explicit in the compliance dimension that borrower rudeness is never the agent's fault and that a coerced payment is a problem rather than a mitigant, and restates in the top resolution anchor that correct non-payment outcomes deserve full marks. Because the generator and the heuristic baseline share vocabulary, the offline demo cannot itself demonstrate calibration gains; that comparison is meaningful only against independent human labels, which is precisely why the pipeline refuses to report it until those labels exist.

## 10. Threshold-sensitivity results
Mean recomputed score on the current (demo_heuristic) run is 51.9/100. Sweeping the threshold over 50–90 moves pass and review rates while critical overrides stay active; the per-cutoff table, the calls that change classification, and (when labels exist) false passes versus false fails are written to `results/analysis/`.

## 11. Illustrative operational implications
A transparent cost model estimates monthly review workload and cost from configurable, explicitly hypothetical assumptions, assigning each call to exactly one review bucket to avoid double counting: review-required calls first, then fails, then borderline passes, then a random audit slice of the remaining passes. Review hours and expense follow from those volumes; false-pass exposure and false-fail opportunity cost are added only when the human-labelled subset supplies the error rates, and the model is explicitly flagged as partial otherwise rather than filling the gap with a guess. Every monetary input is surfaced in the dashboard with its unit and marked hypothetical. The lowest-cost threshold is never presented as a recommendation: compliance and risk tolerance take precedence over this illustrative optimisation, and a capacity-shortfall warning fires when the implied review hours exceed the configured reviewer capacity so that a cheap-looking threshold that is operationally infeasible is not mistaken for a good one.

## 12. Limitations
- All conversations, people, institutions and policies are fictional and synthetic.
- The initial human-labelled sample is only 30 transcripts.
- A single annotator cannot establish inter-annotator reliability.
- Synthetic scenario expectations are test specifications, not independent human ground truth.
- Repeated tuning against the same 30 labels risks overfitting; a held-out sample is reserved but not yet labelled.
- Results may not generalise to other models, languages, real calls or financial institutions.
- The compliance gates implement a fictional benchmark policy and certify no legal or regulatory compliance.

## 13. Reproducibility
```bash
uv sync
uv run voice-eval generate-dataset   # frozen; verify with --verify
uv run voice-eval validate-dataset
uv run voice-eval demo   # offline heuristic baseline + analysis + reports
uv run voice-eval evaluate --provider anthropic --rubric v1   # live LLM (needs ANTHROPIC_API_KEY)
uv run pytest
```

## 14. Conclusion
The deliverable is an honest measurement instrument. Where human labels are complete it reports agreement with calibrated uncertainty; where they are not, it says PENDING rather than inventing a result. That discipline — recomputing every decision, grounding every claim in cited evidence, separating synthetic expectations from human judgement, and refusing to fabricate — is the point of the project.

_Word count (prose, excluding tables/headings/code): ~1452._

---
_Built 2026-10-13T06:53:20+00:00 from committed artifacts._
