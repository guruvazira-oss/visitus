"""Plotly figure builders. Figures take data frames; they never call an API or a model."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from voice_eval.config import ANALYSIS_DIR, RESULTS_DIR, rel

NAVY = "#0b1f3a"
BLUE = "#3b82f6"
LIGHT_BLUE = "#93c5fd"
AMBER = "#d97706"
GREEN = "#15803d"
GREY = "#64748b"
RED = "#b91c1c"

LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, Segoe UI, system-ui, sans-serif", size=13, color=NAVY),
    margin=dict(l=60, r=30, t=60, b=50),
    colorway=[BLUE, AMBER, GREEN, GREY, "#7c3aed", RED],
)
TITLE_FONT = dict(size=16)


def _style(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(**LAYOUT)
    fig.update_layout(title=dict(text=title, font=TITLE_FONT))
    return fig


def score_distribution(scores: list[float]) -> go.Figure:
    fig = go.Figure(go.Histogram(x=scores, xbins=dict(start=0, end=100, size=5), marker_color=BLUE))
    fig.update_xaxes(title="Recomputed overall score (0–100)", range=[0, 100])
    fig.update_yaxes(title="Transcripts")
    return _style(fig, "Score distribution")


def pass_rate_curve(df: pd.DataFrame) -> go.Figure:
    full = df[df["population"] == "full_synthetic"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=full["cutoff"],
            y=full["pass_rate"],
            name="Pass rate",
            mode="lines+markers",
            line=dict(color=BLUE),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=full["cutoff"],
            y=full["fail_rate"],
            name="Fail rate",
            mode="lines+markers",
            line=dict(color=AMBER),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=full["cutoff"],
            y=full["review_rate"],
            name="Review-required rate",
            mode="lines+markers",
            line=dict(color=GREY, dash="dot"),
        )
    )
    fig.update_xaxes(title="Score threshold")
    fig.update_yaxes(title="Share of evaluated calls", tickformat=".0%", range=[0, 1])
    return _style(fig, "Decision rates vs threshold (full synthetic dataset)")


def false_pass_fail_curve(df: pd.DataFrame) -> go.Figure | None:
    full = df[df["population"] == "full_synthetic"].dropna(subset=["false_pass_count"])
    if full.empty:
        return None
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=full["cutoff"],
            y=full["false_pass_count"],
            name="False passes",
            mode="lines+markers",
            line=dict(color=RED),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=full["cutoff"],
            y=full["false_fail_count"],
            name="False fails",
            mode="lines+markers",
            line=dict(color=AMBER),
        )
    )
    fig.update_xaxes(title="Score threshold")
    fig.update_yaxes(title="Count on human-labelled subset")
    return _style(fig, "False passes vs false fails (human-labelled subset)")


def dimension_agreement_bar(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=df["dimension"], y=df["exact_agreement"], name="Exact", marker_color=BLUE)
    )
    fig.add_trace(
        go.Bar(x=df["dimension"], y=df["within_one"], name="Within 1", marker_color=LIGHT_BLUE)
    )
    fig.update_yaxes(title="Agreement", tickformat=".0%", range=[0, 1])
    fig.update_layout(barmode="overlay")
    return _style(fig, "Per-dimension human–judge agreement")


def confusion_heatmap(df: pd.DataFrame, title: str) -> go.Figure:
    z = df.select_dtypes("number")
    fig = go.Figure(
        go.Heatmap(
            z=z.values,
            x=list(z.columns),
            y=list(df.index if df.index.name else df.iloc[:, 0]),
            colorscale="Blues",
            text=z.values,
            texttemplate="%{text}",
            showscale=False,
        )
    )
    return _style(fig, title)


def cost_curve(df: pd.DataFrame) -> go.Figure | None:
    if df.empty or df["total_operational_cost"].isna().all():
        return None
    fig = go.Figure(
        go.Scatter(
            x=df["cutoff"],
            y=df["total_operational_cost"],
            mode="lines+markers",
            line=dict(color=NAVY),
        )
    )
    fig.update_xaxes(title="Score threshold")
    fig.update_yaxes(title="Illustrative total monthly cost")
    return _style(fig, "Illustrative operational cost vs threshold (hypothetical assumptions)")


def spec_tier_bar(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col, color in (("PASS", GREEN), ("FAIL", RED), ("REVIEW_REQUIRED", GREY)):
        fig.add_trace(go.Bar(x=df["agent_quality_tier"], y=df[col], name=col, marker_color=color))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title="Transcripts")
    return _style(fig, "Judge decisions by designed agent-quality tier")


def write_html(fig: go.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pio.write_html(fig, path, include_plotlyjs="cdn", full_html=True)
    return path


def build_report_figures(out_dir: Path = RESULTS_DIR / "figures") -> list[str]:
    from voice_eval.pipeline import analyse
    from voice_eval.reporting.experiment_registry import list_experiments
    from voice_eval.rubric_loader import available_rubrics

    written: list[str] = []
    for v in available_rubrics():
        if not any(r.manifest.get("rubric_version") == v for r in list_experiments()):
            continue
        b = analyse(v)
        if not b.evals:
            continue
        written.append(
            rel(
                write_html(
                    score_distribution(
                        [e.overall_score for e in b.evals if e.overall_score is not None]
                    ),
                    out_dir / f"score_distribution_{v}.html",
                )
            )
        )
        if not b.thresholds.empty:
            written.append(
                rel(
                    write_html(pass_rate_curve(b.thresholds), out_dir / f"pass_rate_curve_{v}.html")
                )
            )
            fpf = false_pass_fail_curve(b.thresholds)
            if fpf:
                written.append(rel(write_html(fpf, out_dir / f"false_pass_fail_{v}.html")))
        if not b.impact.empty:
            cc = cost_curve(b.impact)
            if cc:
                written.append(rel(write_html(cc, out_dir / f"cost_curve_{v}.html")))
        if b.spec_summary:
            written.append(
                rel(
                    write_html(
                        spec_tier_bar(b.spec_summary["tiers"]), out_dir / f"spec_tiers_{v}.html"
                    )
                )
            )
        if b.agreement:
            from voice_eval.analysis.agreement import agreement_summary_rows

            written.append(
                rel(
                    write_html(
                        dimension_agreement_bar(agreement_summary_rows(b.agreement)),
                        out_dir / f"dimension_agreement_{v}.html",
                    )
                )
            )
    _ = ANALYSIS_DIR
    return written
