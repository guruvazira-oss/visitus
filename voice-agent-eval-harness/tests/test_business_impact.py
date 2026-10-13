import math

import pytest

from voice_eval.analysis.business_impact import BucketShares, BusinessAssumptions, compute_impact


def test_no_double_counting_single_bucket():
    a = BusinessAssumptions(
        calls_per_month=1000,
        share_failed_reviewed=1.0,
        share_borderline_reviewed=1.0,
        share_review_required_reviewed=1.0,
        additional_random_audit_share=1.0,
        review_minutes_per_call=60,
        review_cost_per_call=1.0,
        fixed_monthly_platform_cost=0,
    )
    shares = BucketShares(0.25, 0.25, 0.25, 0.25, 1000)
    r = compute_impact(shares, a, None, None)
    assert r["calls_sent_for_review"] == pytest.approx(1000)  # every call once
    assert r["review_hours"] == pytest.approx(1000)


def test_partial_total_when_rates_missing():
    a = BusinessAssumptions(calls_per_month=1000)
    r = compute_impact(BucketShares(0.1, 0.2, 0.2, 0.5, 1000), a, None, None)
    assert r["total_is_partial"]
    assert math.isnan(r["false_pass_exposure"])


def test_false_pass_exposure():
    a = BusinessAssumptions(
        calls_per_month=1000,
        share_borderline_reviewed=0.0,
        additional_random_audit_share=0.0,
        false_pass_cost=100,
        review_cost_per_call=0,
        fixed_monthly_platform_cost=0,
        share_failed_reviewed=0,
        share_review_required_reviewed=0,
    )
    shares = BucketShares(0.0, 0.0, 0.0, 1.0, 1000)
    r = compute_impact(shares, a, fp_rate=0.1, ff_rate=0.0)
    assert r["false_pass_exposure"] == pytest.approx(1000 * 0.1 * 100)


def test_capacity_shortfall():
    a = BusinessAssumptions(
        calls_per_month=10000,
        review_minutes_per_call=60,
        reviewer_hours_capacity_per_month=10,
        share_failed_reviewed=1.0,
    )
    r = compute_impact(BucketShares(0, 1.0, 0, 0, 10000), a, None, None)
    assert r["capacity_shortfall_hours"] > 0


def test_invalid_share_rejected():
    with pytest.raises(ValueError):
        compute_impact(
            BucketShares(0, 0, 0, 1, 10), BusinessAssumptions(share_failed_reviewed=2.0), None, None
        )
