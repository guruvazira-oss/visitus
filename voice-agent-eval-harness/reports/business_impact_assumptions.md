# Illustrative business-impact assumptions

All values are hypothetical and illustrative; the model claims no realised savings.

| assumption                        |    value | unit                              | source                      |
|:----------------------------------|---------:|:----------------------------------|:----------------------------|
| calls_per_month                   | 50000    | calls / month                     | hypothetical (illustrative) |
| review_cost_per_call              |     6.5  | currency / reviewed call          | hypothetical (illustrative) |
| review_minutes_per_call           |     9    | minutes                           | hypothetical (illustrative) |
| share_failed_reviewed             |     0.5  | fraction of FAIL calls            | hypothetical (illustrative) |
| share_borderline_reviewed         |     0.25 | fraction of borderline PASS calls | hypothetical (illustrative) |
| share_review_required_reviewed    |     1    | fraction of REVIEW_REQUIRED calls | hypothetical (illustrative) |
| additional_random_audit_share     |     0.02 | fraction of other PASS calls      | hypothetical (illustrative) |
| false_pass_cost                   |   120    | currency / undetected false pass  | hypothetical (illustrative) |
| false_fail_cost                   |    15    | currency / unreviewed false fail  | hypothetical (illustrative) |
| reviewer_hours_capacity_per_month |  1600    | hours / month                     | hypothetical (illustrative) |
| fixed_monthly_platform_cost       |  2500    | currency / month                  | hypothetical (illustrative) |

## Formulas
```
Illustrative operational-cost model. All monetary inputs are hypothetical assumptions.

Every evaluated call is assigned to exactly ONE review bucket (no double counting), in
priority order: REVIEW_REQUIRED > FAIL > borderline PASS > other PASS.

Let N = calls per month and p_rr, p_fail, p_bpass, p_opass the shares of evaluated calls in
each bucket (sum = 1), with review shares s_rr, s_fail, s_b, s_audit.

    reviewed_calls   = N * (p_rr*s_rr + p_fail*s_fail + p_bpass*s_b + p_opass*s_audit)
    review_hours     = reviewed_calls * review_minutes_per_call / 60
    review_expense   = reviewed_calls * review_cost_per_call
    capacity_short   = max(0, review_hours - reviewer_hours_capacity)
    undetected_fp    = N * (p_bpass*(1-s_b) + p_opass*(1-s_audit)) * fp_rate
                       where fp_rate = P(human FAIL | judge PASS) = 1 - PASS precision
    fp_exposure      = undetected_fp * false_pass_cost
    unreviewed_ff    = N * (p_fail*(1-s_fail) + p_rr*(1-s_rr)) * ff_rate
                       where ff_rate = P(human PASS | judge FAIL or REVIEW_REQUIRED)
    ff_cost          = unreviewed_ff * false_fail_cost
    total            = review_expense + fp_exposure + ff_cost + fixed_monthly_platform_cost

Error rates come from the human-labelled subset when available; otherwise they are explicit,
user-supplied assumptions. The lowest-cost threshold is never presented as a recommendation:
compliance requirements and risk tolerance take precedence over this illustrative model.
```

---
_Built 2026-10-13T06:53:20+00:00 from committed artifacts._
