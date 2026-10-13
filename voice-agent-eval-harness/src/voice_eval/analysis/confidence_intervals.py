"""Confidence intervals suited to small samples.

* Proportions (agreement rates, precision, recall, error rates): Wilson score interval —
  well-behaved near 0 and 1 and for n ~ 30, unlike the normal (Wald) approximation.
* Statistics without a simple closed form (Cohen's kappa, MAE): percentile bootstrap with
  paired resampling of transcripts and a fixed seed, so results are reproducible.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

import numpy as np
from scipy import stats


def wilson_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    if n <= 0:
        return (math.nan, math.nan)
    if not 0 <= k <= n:
        raise ValueError("k must be between 0 and n")
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def bootstrap_ci(
    statistic: Callable[..., float],
    arrays: Sequence[Sequence],
    n_resamples: int = 2000,
    seed: int = 11,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Paired percentile bootstrap. Resamples that yield NaN are dropped."""
    arrs = [np.asarray(a) for a in arrays]
    n = len(arrs[0])
    if n < 2:
        return (math.nan, math.nan)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_resamples):
        idx = rng.integers(0, n, n)
        v = statistic(*(a[idx] for a in arrs))
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            vals.append(v)
    if len(vals) < n_resamples * 0.5:
        return (math.nan, math.nan)
    alpha = (1 - confidence) / 2
    return (float(np.quantile(vals, alpha)), float(np.quantile(vals, 1 - alpha)))
