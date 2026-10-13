"""Confusion matrices with fixed label orders (rows = reference/human, cols = judge)."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from sklearn.metrics import confusion_matrix

ORDINAL_LABELS = [0, 1, 2, 3, 4]
BINARY_LABELS = ["PASS", "FAIL"]
DECISION_LABELS = ["PASS", "FAIL", "REVIEW_REQUIRED"]
GATE_LABELS = ["CONFIRMED", "NOT_PRESENT", "UNCERTAIN"]


def confusion_frame(reference: Sequence, candidate: Sequence, labels: Sequence) -> pd.DataFrame:
    if len(reference) == 0:
        return pd.DataFrame(
            0, index=[f"human={x}" for x in labels], columns=[f"judge={x}" for x in labels]
        )
    m = confusion_matrix(list(reference), list(candidate), labels=list(labels))
    return pd.DataFrame(
        m, index=[f"human={x}" for x in labels], columns=[f"judge={x}" for x in labels]
    )
