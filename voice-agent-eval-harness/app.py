"""Voice Agent Evaluation Harness — Streamlit dashboard.

Offline-safe: no API calls or model calls at startup or on any page. The dashboard reads
only committed artifacts (dataset, rubrics, saved experiments, analysis outputs, annotations).
Live LLM evaluation is run from the CLI, never from here.
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd
import streamlit as st

from voice_eval.config import DecisionPolicy, load_experiment_defaults, load_settings
from voice_eval.dataset_loader import load_transcripts_cached
from voice_eval.schemas import DIMENSIONS, GATE_IDS
from voice_eval.ui import data_access as da
from voice_eval.ui import theme
from voice_eval.ui.theme import badge, decision_color, provenance_badge

st.set_page_config(
    page_title="Voice Agent Eval Harness", layout="wide", initial_sidebar_state="expanded"
)
theme.inject()

PAGES = [
    "Executive overview",
    "Transcript explorer",
    "Human annotation studio",
    "Judge calibration",
    "Threshold lab",
    "Experiment registry",
]


def _pct(x) -> str:
    try:
        return "—" if x is None or pd.isna(x) else f"{x * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def _num(x, nd=1) -> str:
    try:
        return "—" if x is None or pd.isna(x) else f"{x:.{nd}f}"
    except (TypeError, ValueError):
        return "—"


try:
    TRANSCRIPTS = load_transcripts_cached()
except Exception as exc:  # noqa: BLE001
    st.error(f"Dataset not available: {exc}\n\nRun `uv run voice-eval generate-dataset`.")
    st.stop()

RUBRICS = da.get_rubrics()
DEFAULTS = load_experiment_defaults()

st.sidebar.title("Voice Agent Eval Harness")
st.sidebar.caption("BFSI Collections Benchmark — synthetic data, fictional policy")
page = st.sidebar.radio("Page", PAGES)
rubric_version = st.sidebar.selectbox("Rubric version", list(RUBRICS), index=0)
base_policy = DecisionPolicy.from_settings()
threshold = st.sidebar.slider("Pass threshold", 50, 90, int(base_policy.pass_threshold), 5)
review_map = st.sidebar.selectbox(
    "REVIEW_REQUIRED → binary",
    ["as_fail", "as_pass", "exclude"],
    index=["as_fail", "as_pass", "exclude"].index(base_policy.review_required_binary_mapping),
    help="How REVIEW_REQUIRED maps onto the PASS/FAIL benchmark comparison.",
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<span class='prov'>Offline-safe: no API calls are made from the dashboard. "
    "Run live LLM evaluations with the CLI.</span>",
    unsafe_allow_html=True,
)

overrides = (("pass_threshold", float(threshold)), ("review_required_binary_mapping", review_map))
bundle = da.get_bundle(rubric_version, overrides)
exp = bundle.experiment
prov_key = exp.manifest.get("provenance") if exp else "none"


def provenance_line() -> None:
    bits = [provenance_badge("synthetic")]
    if exp:
        bits.append(provenance_badge(prov_key))
        bits.append(
            f"<span class='prov'>experiment <code>{exp.id}</code>; served model "
            f"<code>{exp.manifest.get('judge_model')}</code></span>"
        )
    else:
        bits.append(provenance_badge("none"))
    if bundle.human_status == "complete":
        bits.append(provenance_badge("human"))
    st.markdown(" ".join(bits), unsafe_allow_html=True)


# ====================================================================== Executive overview
def page_overview() -> None:
    st.header("Executive overview")
    provenance_line()
    tdf = da.get_transcripts_frame()
    c = st.columns(4)
    c[0].metric("Synthetic transcripts", len(tdf))
    c[1].metric("Scenario categories", tdf["scenario_category"].nunique())
    c[2].metric("Dataset version", load_settings()["dataset"]["version"])
    c[3].metric("Rubric", f"{rubric_version} ({RUBRICS[rubric_version].status})")

    if exp is None:
        st.markdown(
            "<div class='warn'>No evaluation found for this rubric. Run "
            "<code>uv run voice-eval demo</code> (offline) or <code>uv run voice-eval evaluate "
            "--provider anthropic</code> (live).</div>",
            unsafe_allow_html=True,
        )
    else:
        evals = bundle.evals
        scores = [e.overall_score for e in evals if e.overall_score is not None]
        from voice_eval.analysis.agreement import judge_decision_at

        decs = [judge_decision_at(e, bundle.policy, float(threshold)).value for e in evals]
        m = st.columns(5)
        m[0].metric("Evaluated", len(evals))
        m[1].metric("Mean score", _num(sum(scores) / len(scores) if scores else None))
        m[2].metric(
            f"Pass rate @ {threshold}", _pct(decs.count("PASS") / len(decs) if decs else None)
        )
        m[3].metric("Review required", decs.count("REVIEW_REQUIRED"))
        gate_over = sum(
            1
            for e in evals
            if any(
                g.adjudication_status.value in ("CONFIRMED_VIOLATION", "JUDGE_ALLEGED_UNCONFIRMED")
                for g in e.critical_gate_results
            )
        )
        m[4].metric("Critical gate flags", gate_over)
        from voice_eval.reporting.charts import score_distribution

        st.plotly_chart(score_distribution(scores), width="stretch")
        st.subheader("Scenario distribution")
        st.bar_chart(tdf["scenario_category"].value_counts())

    st.subheader("Human annotation progress")
    lab = bundle.labels
    if not lab.sample_ids:
        st.info("Annotation sample not frozen yet. Run `voice-eval create-annotation-sample`.")
    else:
        st.progress(len(lab.annotations) / lab.n_required if lab.n_required else 0.0)
        st.caption(
            f"{len(lab.annotations)}/{lab.n_required} frozen labels — status: **{bundle.human_status}**"
            + ("" if lab.complete else ". Agreement metrics are disabled until complete.")
        )
    with st.expander("Data provenance & disclaimers"):
        st.markdown(
            "All conversations, people, institutions and the compliance policy are **fictional**. "
            "The heuristic baseline is **not an LLM**. The synthetic specification is **not** human "
            "ground truth. See `reports/methodology.md`."
        )


# ===================================================================== Transcript explorer
def page_explorer() -> None:
    st.header("Transcript explorer")
    provenance_line()
    tdf = da.get_transcripts_frame()
    idx = da.get_index()
    evmap = {e.transcript_id: e for e in bundle.evals}
    hmap = {h.transcript_id: h for h in bundle.labels.annotations}

    f = st.columns(4)
    cats = f[0].multiselect("Category", sorted(tdf["scenario_category"].unique()))
    diffs = f[1].multiselect("Difficulty", sorted(tdf["difficulty_level"].unique()))
    tiers = f[2].multiselect("Designed quality tier", sorted(tdf["agent_quality_tier"].unique()))
    search = f[3].text_input("Search id / subtype")
    view = tdf.copy()
    if cats:
        view = view[view["scenario_category"].isin(cats)]
    if diffs:
        view = view[view["difficulty_level"].isin(diffs)]
    if tiers:
        view = view[view["agent_quality_tier"].isin(tiers)]
    if search:
        s = search.lower()
        view = view[
            view["transcript_id"].str.lower().str.contains(s)
            | view["scenario_subtype"].str.lower().str.contains(s)
        ]
    if evmap:
        from voice_eval.analysis.agreement import judge_decision_at

        view = view.assign(
            judge_score=view["transcript_id"].map(
                lambda t: evmap[t].overall_score if t in evmap else None
            ),
            judge_decision=view["transcript_id"].map(
                lambda t: (
                    judge_decision_at(evmap[t], bundle.policy, float(threshold)).value
                    if t in evmap
                    else None
                )
            ),
        )
        decisions = sorted(x for x in view["judge_decision"].dropna().unique())
        chosen = st.multiselect("Judge decision", decisions)
        if chosen:
            view = view[view["judge_decision"].isin(chosen)]
        rng = st.slider("Judge score range", 0, 100, (0, 100))
        view = view[view["judge_score"].isna() | view["judge_score"].between(*rng)]

    st.caption(f"{len(view)} transcripts")
    st.dataframe(view, width="stretch", height=260, hide_index=True)
    if view.empty:
        return
    tid = st.selectbox("Inspect transcript", view["transcript_id"].tolist())
    t = idx[tid]
    left, right = st.columns([3, 2])
    with left:
        st.subheader(f"{tid} — {t.scenario_subtype}")
        st.caption(
            f"{t.scenario_description}  \nDesigned tier: **{t.agent_quality_tier}**, "
            f"expected band **{t.expected_outcome_band}**, modifiers: {', '.join(t.modifiers) or 'none'}"
        )
        for turn in t.conversation_turns:
            cls = "turn-agent" if turn.speaker.value == "agent" else "turn-contact"
            st.markdown(
                f"<div class='{cls}'><b>[{turn.turn_id}] {turn.speaker.value.upper()}:</b> {turn.text}</div>",
                unsafe_allow_html=True,
            )
    with right:
        e = evmap.get(tid)
        if e is None:
            st.info("No judge evaluation for this transcript in the selected experiment.")
        else:
            st.subheader("Judge evaluation")
            st.markdown(provenance_badge(prov_key), unsafe_allow_html=True)
            h = hmap.get(tid)
            rows = []
            for d in DIMENSIONS:
                rows.append(
                    {
                        "dimension": d,
                        "judge": e.dimension_scores[d],
                        "applicable": e.dimension_applicability[d],
                        "human": (h.dimension_scores[d] if h else None),
                    }
                )
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            st.markdown(
                f"**Recomputed score:** {_num(e.overall_score)} → "
                f"{badge(e.decision.value, decision_color(e.decision.value))}",
                unsafe_allow_html=True,
            )
            st.caption(" / ".join(e.decision_reasons))
            with st.expander("Evidence & rationales"):
                for d in DIMENSIONS:
                    st.markdown(f"**{d}** — {e.dimension_rationales[d]}")
                    for ev in e.evidence_by_dimension[d]:
                        st.caption(f"  [{ev.turn_id}] “{ev.quote}” ({ev.evidence_type.value})")
            with st.expander("Critical gates"):
                for g in e.critical_gate_results:
                    st.markdown(
                        f"**{g.gate_id}**: judge={g.judge_assessment.value}, "
                        f"status={g.adjudication_status.value}"
                        + (f", human={g.human_assessment}" if g.human_assessment else "")
                    )
                    if g.notes:
                        st.caption("; ".join(g.notes))
            if e.grounding_issues:
                st.markdown(
                    "<div class='warn'>Grounding issues: "
                    + "; ".join(e.grounding_issues[:5])
                    + "</div>",
                    unsafe_allow_html=True,
                )


# ================================================================ Human annotation studio
def page_annotation() -> None:
    from voice_eval.annotation.annotation_service import AnnotationStore, load_sample, sample_ids
    from voice_eval.schemas import (
        AnnotationStatus,
        Decision,
        HumanAnnotation,
        HumanGateStatus,
    )

    st.header("Human annotation studio")
    st.caption(
        "Annotations are stored locally and independently of judge outputs. Judge scores are "
        "hidden here until you choose to reveal them, to keep labels independent."
    )
    sample = load_sample()
    if not sample:
        st.info(
            "No frozen annotation sample. Create one with `uv run voice-eval create-annotation-sample`."
        )
        return
    ids = sample_ids()
    store = AnnotationStore()
    annotator = st.text_input("Annotator id", DEFAULTS["annotation"]["annotator_id_default"])
    status = store.completion(ids, annotator, rubric_version)
    st.progress(status.fraction)
    st.caption(
        f"{status.n_completed}/{status.total} completed, {len(status.drafts)} drafts, "
        f"{len(status.missing)} not started. Sampling seed {sample['sampling_seed']}."
    )

    idx = da.get_index()
    tid = st.selectbox(
        "Transcript", ids, format_func=lambda t: f"{t}  ({idx[t].scenario_category.value})"
    )
    t = idx[tid]
    existing = store.get_for(tid, annotator, rubric_version)
    rub = RUBRICS[rubric_version]

    left, right = st.columns([3, 2])
    with left:
        for turn in t.conversation_turns:
            cls = "turn-agent" if turn.speaker.value == "agent" else "turn-contact"
            st.markdown(
                f"<div class='{cls}'><b>[{turn.turn_id}] {turn.speaker.value.upper()}:</b> {turn.text}</div>",
                unsafe_allow_html=True,
            )
    with right:
        with st.form("annotation_form"):
            scores, applic, rats, evid = {}, {}, {}, {}
            turn_ids = [x.turn_id for x in t.conversation_turns]
            for d in DIMENSIONS:
                dim = rub.dimension(d)
                st.markdown(f"**{dim.name}** ({dim.weight:.0%})")
                na = False
                if not dim.applicability.always_applicable:
                    na = st.checkbox(
                        "Not applicable",
                        key=f"na_{d}",
                        value=(existing and not existing.dimension_applicability.get(d, True))
                        or False,
                    )
                applic[d] = not na
                default = existing.dimension_scores.get(d) if existing else None
                scores[d] = (
                    None
                    if na
                    else st.radio(
                        f"Score — {d}",
                        [0, 1, 2, 3, 4],
                        horizontal=True,
                        key=f"sc_{d}",
                        index=(default if isinstance(default, int) else 3),
                    )
                )
                with st.expander(f"anchors — {d}"):
                    for sc, a in sorted(dim.anchors.items()):
                        st.caption(f"{sc}: {a.label} — {a.observable_behavior}")
                rats[d] = st.text_input(
                    f"Rationale — {d}",
                    (existing.dimension_rationales.get(d, "") if existing else ""),
                    key=f"rat_{d}",
                )
                evid[d] = st.multiselect(
                    f"Evidence turns — {d}",
                    turn_ids,
                    (existing.evidence_turns.get(d, []) if existing else []),
                    key=f"ev_{d}",
                )
            st.markdown("**Critical gates**")
            gates = {}
            for g in GATE_IDS:
                cur = existing.gate_assessments[g].value if existing else "NOT_PRESENT"
                gates[g] = st.selectbox(
                    g,
                    ["NOT_PRESENT", "CONFIRMED", "UNCERTAIN"],
                    index=["NOT_PRESENT", "CONFIRMED", "UNCERTAIN"].index(cur),
                    key=f"g_{g}",
                )
            dec_default = existing.overall_decision.value if existing else "FAIL"
            decision = st.selectbox(
                "Overall decision",
                ["PASS", "FAIL", "REVIEW_REQUIRED"],
                index=["PASS", "FAIL", "REVIEW_REQUIRED"].index(dec_default),
            )
            notes = st.text_area("Notes", existing.notes if existing else "")
            as_draft = st.checkbox("Save as draft", value=False)
            confirm = st.checkbox("Confirm overwrite of a completed label", value=False)
            submitted = st.form_submit_button("Save annotation")
        if submitted:
            try:
                ann = HumanAnnotation(
                    annotation_id=HumanAnnotation.make_id(tid, annotator, rubric_version),
                    transcript_id=tid,
                    annotator_id=annotator,
                    rubric_version=rubric_version,
                    dimension_scores=scores,
                    dimension_applicability=applic,
                    dimension_rationales=rats,
                    evidence_turns=evid,
                    gate_assessments={g: HumanGateStatus(v) for g, v in gates.items()},
                    overall_decision=Decision(decision),
                    notes=notes,
                    status=AnnotationStatus.DRAFT if as_draft else AnnotationStatus.COMPLETED,
                )
                store.save(ann, confirm_overwrite=confirm)
                st.success(f"Saved {ann.annotation_id} ({ann.status.value}).")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Not saved: {exc}")

    st.markdown("---")
    c = st.columns(3)
    if c[0].button("Export stored annotations (CSV)"):
        from voice_eval.annotation.import_export import export_csv
        from voice_eval.config import DATA_DIR

        p = DATA_DIR / f"annotations_export_{annotator}_{rubric_version}.csv"
        export_csv(store.list(annotator, rubric_version), p)
        st.success(f"Wrote {p}")
    if c[1].button("Freeze completed batch"):
        from voice_eval.annotation.annotation_service import BatchIncomplete

        try:
            info = store.freeze_batch(ids, annotator, rubric_version)
            st.success(f"Frozen: {info}")
        except BatchIncomplete as exc:
            st.error(str(exc))
    reveal = c[2].checkbox("Reveal judge score (after labelling)")
    if reveal:
        e = next((x for x in bundle.evals if x.transcript_id == tid), None)
        st.caption(
            f"Judge recomputed score: {_num(e.overall_score) if e else '—'}; decision "
            f"{e.decision.value if e else '—'}"
        )


# ====================================================================== Judge calibration
def page_calibration() -> None:
    st.header("Judge calibration")
    provenance_line()
    if exp is None:
        st.warning("No evaluation available. Run an evaluation first.")
        return
    a = bundle.agreement
    if a is None:
        lab = bundle.labels
        st.markdown(
            "<div class='warn'><b>Agreement metrics are PENDING.</b> They are intentionally "
            f"disabled until all {lab.n_required or 30} human labels exist "
            f"({len(lab.annotations)}/{lab.n_required or 30} present). No agreement numbers are "
            "fabricated. Complete and freeze the annotation batch to enable this page.</div>",
            unsafe_allow_html=True,
        )
        st.subheader("Spec-conformance (judge vs synthetic specification — NOT human agreement)")
        if bundle.spec_summary:
            st.dataframe(bundle.spec_summary["tiers"], hide_index=True, width="stretch")
            st.dataframe(bundle.spec_summary["gates"], hide_index=True, width="stretch")
        return
    bm = a.binary
    c = st.columns(4)
    c[0].metric("Pairs (n)", a.n_pairs)
    c[1].metric("Binary agreement", _pct(bm["raw_agreement"]["value"]))
    c[2].metric("Cohen's κ (binary)", _num(bm["kappa"]["value"], 2))
    c[3].metric("Human self-consistency", _pct(a.human_self_consistency["value"]))
    c2 = st.columns(4)
    c2[0].metric("False passes", bm["false_pass_count"])
    c2[1].metric("False fails", bm["false_fail_count"])
    c2[2].metric("PASS precision", _pct(bm["pass_precision"]["value"]))
    c2[3].metric("PASS recall", _pct(bm["pass_recall"]["value"]))
    st.caption(
        f"REVIEW_REQUIRED mapped as **{a.review_mapping}** ({a.excluded_review} excluded); "
        f"human PASS prevalence {_pct(bm['human_pass_prevalence']['value'])}. Small n ⇒ wide CIs."
    )
    from voice_eval.analysis.agreement import agreement_summary_rows
    from voice_eval.reporting.charts import confusion_heatmap, dimension_agreement_bar

    st.plotly_chart(dimension_agreement_bar(agreement_summary_rows(a)), width="stretch")
    cc = st.columns(2)
    cc[0].plotly_chart(
        confusion_heatmap(bm["confusion"], "Binary PASS/FAIL confusion"), width="stretch"
    )
    cc[1].plotly_chart(
        confusion_heatmap(a.three_way["confusion"], "Three-way decision confusion"), width="stretch"
    )
    st.subheader("Per-dimension agreement")
    st.dataframe(agreement_summary_rows(a), hide_index=True, width="stretch")
    st.subheader("Per-scenario agreement")
    st.dataframe(a.per_scenario, hide_index=True, width="stretch")
    st.subheader("Critical-gate agreement")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "gate": g,
                    "agreement": m["agreement"]["value"],
                    "human_confirmed": m["human_confirmed"],
                    "judge_alleged": m["judge_alleged"],
                    "judge_missed": m["judge_missed_confirmed"],
                    "judge_overcalled": m["judge_overcalled"],
                    "kappa": m["kappa"]["value"],
                }
                for g, m in a.gates.items()
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    st.subheader("REVIEW_REQUIRED mapping sensitivity")
    st.dataframe(a.mapping_sensitivity, hide_index=True, width="stretch")
    st.subheader("Rubric-version comparison")
    rows = []
    for v in RUBRICS:
        b = da.get_bundle(v, overrides)
        if b.agreement:
            m = b.agreement.binary
            rows.append(
                {
                    "rubric": v,
                    "n": m["n"],
                    "binary_agreement": m["raw_agreement"]["value"],
                    "kappa": m["kappa"]["value"],
                    "false_pass": m["false_pass_count"],
                    "false_fail": m["false_fail_count"],
                }
            )
        else:
            rows.append(
                {
                    "rubric": v,
                    "n": 0,
                    "binary_agreement": None,
                    "kappa": None,
                    "false_pass": None,
                    "false_fail": None,
                }
            )
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption(
        "Rubric-development results, not independent validation. A held-out sample is reserved; "
        "comparing v1→v2→v3 on the same 30 labels risks overfitting."
    )
    st.subheader("Disagreement register (judge vs human)")
    st.dataframe(bundle.human_register, width="stretch", height=300)


# ========================================================================== Threshold lab
def page_threshold() -> None:
    st.header("Threshold lab")
    provenance_line()
    if exp is None:
        st.warning("No evaluation available.")
        return
    th = bundle.thresholds
    from voice_eval.reporting.charts import cost_curve, false_pass_fail_curve, pass_rate_curve

    st.plotly_chart(pass_rate_curve(th), width="stretch")
    full = th[th["population"] == "full_synthetic"]
    row = full[full["cutoff"] == float(threshold)]
    if not row.empty:
        r = row.iloc[0]
        c = st.columns(5)
        c[0].metric(f"Pass @ {threshold}", int(r["n_pass"]))
        c[1].metric("Fail", int(r["n_fail"]))
        c[2].metric("Review required", int(r["n_review_required"]))
        c[3].metric("Gate overrides", int(r["critical_gate_overrides"]))
        c[4].metric("Est. reviews/month", _num(r["est_reviewed_calls_per_month"], 0))
    fpf = false_pass_fail_curve(th)
    if fpf is not None:
        st.plotly_chart(fpf, width="stretch")
    else:
        st.info(
            "False-pass / false-fail curves need the human-labelled subset (annotations pending)."
        )
    st.subheader("Full sweep (critical overrides active at every cutoff)")
    st.dataframe(th.drop(columns=["population"]), hide_index=True, width="stretch")
    st.subheader("Calls that change classification between cutoffs")
    st.dataframe(bundle.changes, hide_index=True, width="stretch", height=240)

    st.markdown("---")
    st.subheader("Illustrative business impact (hypothetical assumptions)")
    from voice_eval.analysis.agreement import judge_decision_at
    from voice_eval.analysis.business_impact import (
        BusinessAssumptions,
        assumptions_table,
        bucket_shares,
        compute_impact,
    )

    a0 = BusinessAssumptions.defaults()
    cc = st.columns(3)
    a = BusinessAssumptions(
        calls_per_month=cc[0].number_input(
            "Calls/month", 1000, 10_000_000, int(a0.calls_per_month), 1000
        ),
        review_cost_per_call=cc[1].number_input(
            "Review cost/call", 0.0, 1000.0, float(a0.review_cost_per_call)
        ),
        review_minutes_per_call=cc[2].number_input(
            "Minutes/review", 0.0, 120.0, float(a0.review_minutes_per_call)
        ),
        share_failed_reviewed=cc[0].slider(
            "Share of FAIL reviewed", 0.0, 1.0, float(a0.share_failed_reviewed)
        ),
        share_borderline_reviewed=cc[1].slider(
            "Share borderline reviewed", 0.0, 1.0, float(a0.share_borderline_reviewed)
        ),
        share_review_required_reviewed=cc[2].slider(
            "Share REVIEW_REQUIRED reviewed", 0.0, 1.0, float(a0.share_review_required_reviewed)
        ),
        additional_random_audit_share=cc[0].slider(
            "Random audit of other PASS", 0.0, 1.0, float(a0.additional_random_audit_share)
        ),
        false_pass_cost=cc[1].number_input(
            "False-pass cost", 0.0, 100000.0, float(a0.false_pass_cost)
        ),
        false_fail_cost=cc[2].number_input(
            "False-fail cost", 0.0, 100000.0, float(a0.false_fail_cost)
        ),
        reviewer_hours_capacity_per_month=cc[0].number_input(
            "Reviewer hours capacity", 0.0, 1e6, float(a0.reviewer_hours_capacity_per_month)
        ),
        fixed_monthly_platform_cost=cc[1].number_input(
            "Fixed platform cost", 0.0, 1e6, float(a0.fixed_monthly_platform_cost)
        ),
    )
    band = float(DEFAULTS["threshold_sweep"]["borderline_band"])
    fp = ff = None
    if bundle.agreement:
        from voice_eval.analysis.threshold_sensitivity import human_error_rates_by_cutoff

        rates = human_error_rates_by_cutoff(
            bundle.evals,
            bundle.labels.annotations,
            bundle.transcripts,
            [float(threshold)],
            bundle.policy,
        )
        fp, ff = rates[float(threshold)]
    decs = [judge_decision_at(e, bundle.policy, float(threshold)) for e in bundle.evals]
    shares = bucket_shares(decs, [e.overall_score for e in bundle.evals], float(threshold), band)
    impact = compute_impact(shares, a, fp, ff)
    m = st.columns(4)
    m[0].metric("Calls sent to review", _num(impact["calls_sent_for_review"], 0))
    m[1].metric("Review hours", _num(impact["review_hours"], 0))
    m[2].metric("Review expense", _num(impact["review_expense"], 0))
    m[3].metric("Total (illustrative)", _num(impact["total_operational_cost"], 0))
    if impact["total_is_partial"]:
        st.caption(
            "Error-driven costs omitted (no human-labelled error rates yet); total is partial."
        )
    if impact["capacity_shortfall_hours"] > 0:
        st.markdown(
            f"<div class='warn'>Capacity shortfall: {impact['capacity_shortfall_hours']:.0f} review hours "
            "over capacity at this threshold.</div>",
            unsafe_allow_html=True,
        )
    cc2 = cost_curve(bundle.impact)
    if cc2 is not None:
        st.plotly_chart(cc2, width="stretch")
    st.caption(
        "The lowest-cost threshold is **not** a recommendation: compliance and risk tolerance take "
        "precedence over this illustrative optimisation."
    )
    with st.expander("Assumptions & formulas"):
        st.dataframe(assumptions_table(a), hide_index=True, width="stretch")


# ===================================================================== Experiment registry
def page_registry() -> None:
    from voice_eval.reporting.experiment_registry import list_experiments

    st.header("Experiment registry")
    records = list_experiments()
    if not records:
        st.info("No experiments yet. Run `uv run voice-eval demo` or an LLM evaluation.")
        return
    rows = []
    for r in records:
        m = r.manifest
        rows.append(
            {
                "experiment_id": m["experiment_id"],
                "timestamp": m.get("timestamp"),
                "provenance": m.get("provenance"),
                "rubric": m.get("rubric_version"),
                "judge_model": m.get("judge_model"),
                "config_hash": m.get("evaluation_config_hash"),
                "n_ok": m.get("n_successful"),
                "n_failed": m.get("n_failed"),
                "status": m.get("status"),
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    chosen = st.selectbox("Inspect experiment", [r.id for r in records])
    rec = next(r for r in records if r.id == chosen)
    st.json(rec.manifest)
    fails = rec.failures()
    if fails:
        st.subheader("Recorded failures (never scored)")
        st.dataframe(
            pd.DataFrame([f.model_dump() for f in fails]), hide_index=True, width="stretch"
        )


PAGE_FUNCS = {
    "Executive overview": page_overview,
    "Transcript explorer": page_explorer,
    "Human annotation studio": page_annotation,
    "Judge calibration": page_calibration,
    "Threshold lab": page_threshold,
    "Experiment registry": page_registry,
}
PAGE_FUNCS[page]()
