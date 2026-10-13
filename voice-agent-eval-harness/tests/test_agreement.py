import math

import pytest

from voice_eval.analysis.agreement import binary_metrics, ordinal_metrics, safe_kappa
from voice_eval.analysis.confidence_intervals import bootstrap_ci, wilson_interval
from voice_eval.analysis.confusion import BINARY_LABELS, confusion_frame


def test_perfect_ordinal_agreement():
    m = ordinal_metrics([0, 1, 2, 3, 4], [0, 1, 2, 3, 4])
    assert m["exact_agreement"]["value"] == 1.0
    assert m["mae"]["value"] == 0.0
    assert m["kappa_quadratic"]["value"] == 1.0


def test_within_one():
    m = ordinal_metrics([2, 2, 2, 2], [3, 1, 4, 2])
    assert m["exact_agreement"]["value"] == 0.25
    assert m["within_one_agreement"]["value"] == 0.75
    assert m["mae"]["value"] == 1.0


def test_binary_confusion_counts():
    human = ["PASS", "PASS", "FAIL", "FAIL", "FAIL"]
    judge = ["PASS", "FAIL", "PASS", "FAIL", "FAIL"]
    m = binary_metrics(human, judge)
    assert m["tp"] == 1 and m["fn_false_fail"] == 1 and m["fp_false_pass"] == 1 and m["tn"] == 2
    assert m["false_pass_count"] == 1 and m["false_fail_count"] == 1
    assert m["false_pass_rate"]["value"] == 1 / 3  # FP/(FP+TN)


def test_pass_precision_recall():
    human = ["PASS", "PASS", "PASS", "FAIL"]
    judge = ["PASS", "PASS", "FAIL", "PASS"]
    m = binary_metrics(human, judge)
    assert m["pass_precision"]["value"] == 2 / 3
    assert m["pass_recall"]["value"] == 2 / 3


def test_wilson_bounds():
    lo, hi = wilson_interval(30, 30)
    assert 0 < lo < 1.0 and hi == pytest.approx(1.0)
    lo0, hi0 = wilson_interval(0, 30)
    assert lo0 == 0.0 and hi0 < 1.0
    assert wilson_interval(15, 30)[0] < 0.5 < wilson_interval(15, 30)[1]


def test_wilson_handles_zero_n():
    lo, hi = wilson_interval(0, 0)
    assert math.isnan(lo) and math.isnan(hi)


def test_bootstrap_reproducible():
    a = list(range(20))
    b = [x + (1 if x % 2 else -1) for x in a]
    ci1 = bootstrap_ci(lambda x, y: float((x - y).mean()), [a, b], 500, seed=5)
    ci2 = bootstrap_ci(lambda x, y: float((x - y).mean()), [a, b], 500, seed=5)
    assert ci1 == ci2


def test_kappa_undefined_single_label():
    assert math.isnan(safe_kappa([1, 1, 1], [1, 1, 1]))


def test_confusion_frame_shape():
    cf = confusion_frame(["PASS", "FAIL"], ["PASS", "PASS"], BINARY_LABELS)
    assert cf.shape == (2, 2)
    assert cf.loc["human=FAIL", "judge=PASS"] == 1
