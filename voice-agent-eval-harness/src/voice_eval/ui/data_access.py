"""Cached, read-only data access for the dashboard. NO network/API calls here."""

from __future__ import annotations

import streamlit as st

from voice_eval.config import DecisionPolicy
from voice_eval.dataset_loader import load_transcripts_cached, transcript_index, transcripts_frame
from voice_eval.pipeline import analyse
from voice_eval.rubric_loader import available_rubrics, load_rubric


@st.cache_data(show_spinner=False)
def get_transcripts_frame():
    return transcripts_frame(load_transcripts_cached())


@st.cache_data(show_spinner=False)
def get_rubrics():
    return {v: load_rubric(v) for v in available_rubrics()}


def get_index():
    return transcript_index(load_transcripts_cached())


@st.cache_data(show_spinner=False)
def get_bundle(rubric_version: str, policy_overrides: tuple):
    policy = (
        DecisionPolicy.from_settings(**dict(policy_overrides))
        if policy_overrides
        else DecisionPolicy.from_settings()
    )
    return analyse(rubric_version, policy=policy)
