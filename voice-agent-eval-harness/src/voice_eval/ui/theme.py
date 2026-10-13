"""Shared dashboard theme and small presentation helpers (no data access)."""

from __future__ import annotations

import streamlit as st

NAVY = "#0b1f3a"
PANEL = "#12294a"
BLUE = "#3b82f6"
AMBER = "#d97706"
GREEN = "#15803d"
RED = "#b91c1c"
GREY = "#94a3b8"

PROVENANCE_BADGE = {
    "synthetic": ("Synthetic benchmark data", GREY),
    "demo_heuristic": ("Saved demo evaluation — heuristic baseline (NOT an LLM)", AMBER),
    "llm": ("Actual LLM evaluation", GREEN),
    "human": ("Human-annotated data", BLUE),
    "test": ("Test fixture", RED),
    "none": ("No evaluation yet", RED),
}

CSS = f"""
<style>
.stApp {{ background: {NAVY}; }}
section[data-testid="stSidebar"] {{ background: #081628; }}
h1, h2, h3, h4, label, p, span, div, td, th {{ color: #e8eef7 !important; }}
[data-testid="stMetric"] {{ background: {PANEL}; border: 1px solid #1e3a60; border-radius: 10px;
    padding: 14px 16px; }}
[data-testid="stMetricValue"] {{ color: #ffffff !important; font-size: 1.6rem; }}
.badge {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:0.78rem;
    font-weight:600; color:#fff !important; margin:2px 4px 2px 0; }}
.prov {{ font-size:0.82rem; color:{GREY} !important; }}
.turn-agent {{ background:#13355f; border-left:3px solid {BLUE}; padding:7px 10px; margin:4px 0; border-radius:6px; }}
.turn-contact {{ background:#2a2140; border-left:3px solid {AMBER}; padding:7px 10px; margin:4px 0; border-radius:6px; }}
.warn {{ background:#3a2a10; border:1px solid {AMBER}; border-radius:8px; padding:10px 12px; }}
.stDataFrame {{ background:{PANEL}; }}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def badge(text: str, color: str) -> str:
    return f'<span class="badge" style="background:{color}">{text}</span>'


def provenance_badge(key: str) -> str:
    text, color = PROVENANCE_BADGE.get(key, PROVENANCE_BADGE["none"])
    return badge(text, color)


def decision_color(decision: str) -> str:
    return {"PASS": GREEN, "FAIL": RED, "REVIEW_REQUIRED": AMBER}.get(decision, GREY)
