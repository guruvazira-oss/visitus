# Disagreement analysis

_Two references are reported separately: independent human labels (the research result) and the synthetic test specification (a sanity check, not ground truth)._

## Rubric v1
Experiment: `demo_heuristic_v1` [demo_heuristic]

**Judge vs synthetic spec — suggested root causes:**
| root_cause                             |   count |
|:---------------------------------------|--------:|
| OVERLY_STRICT_SCORING                  |       7 |
| OVERLY_LENIENT_SCORING                 |       3 |
| DATASET_AMBIGUITY                      |       3 |
| INCORRECT_CRITICAL_GATE_CLASSIFICATION |       1 |

Representative records (fictional excerpts):
| transcript_id   | dimension        | human_score   | judge_score     | root_cause_category   |
|:----------------|:-----------------|:--------------|:----------------|:----------------------|
| BFSI-A-001      | OVERALL_DECISION | PASS_EXPECTED | FAIL            | OVERLY_STRICT_SCORING |
| BFSI-B-001      | OVERALL_DECISION | PASS_EXPECTED | FAIL            | OVERLY_STRICT_SCORING |
| BFSI-B-005      | OVERALL_DECISION | PASS_EXPECTED | FAIL            | OVERLY_STRICT_SCORING |
| BFSI-B-017      | OVERALL_DECISION | PASS_EXPECTED | REVIEW_REQUIRED | OVERLY_STRICT_SCORING |

**Judge vs human labels:** PENDING — human annotations incomplete.

## Rubric v2
Experiment: `demo_heuristic_v2` [demo_heuristic]

**Judge vs synthetic spec — suggested root causes:**
| root_cause                             |   count |
|:---------------------------------------|--------:|
| OVERLY_STRICT_SCORING                  |       7 |
| OVERLY_LENIENT_SCORING                 |       3 |
| DATASET_AMBIGUITY                      |       3 |
| INCORRECT_CRITICAL_GATE_CLASSIFICATION |       1 |

Representative records (fictional excerpts):
| transcript_id   | dimension        | human_score   | judge_score     | root_cause_category   |
|:----------------|:-----------------|:--------------|:----------------|:----------------------|
| BFSI-A-001      | OVERALL_DECISION | PASS_EXPECTED | FAIL            | OVERLY_STRICT_SCORING |
| BFSI-B-001      | OVERALL_DECISION | PASS_EXPECTED | FAIL            | OVERLY_STRICT_SCORING |
| BFSI-B-005      | OVERALL_DECISION | PASS_EXPECTED | FAIL            | OVERLY_STRICT_SCORING |
| BFSI-B-017      | OVERALL_DECISION | PASS_EXPECTED | REVIEW_REQUIRED | OVERLY_STRICT_SCORING |

**Judge vs human labels:** PENDING — human annotations incomplete.

## Rubric v3
Experiment: `demo_heuristic_v3` [demo_heuristic]

**Judge vs synthetic spec — suggested root causes:**
| root_cause                             |   count |
|:---------------------------------------|--------:|
| OVERLY_STRICT_SCORING                  |       7 |
| OVERLY_LENIENT_SCORING                 |       3 |
| DATASET_AMBIGUITY                      |       3 |
| INCORRECT_CRITICAL_GATE_CLASSIFICATION |       1 |

Representative records (fictional excerpts):
| transcript_id   | dimension        | human_score   | judge_score     | root_cause_category   |
|:----------------|:-----------------|:--------------|:----------------|:----------------------|
| BFSI-A-001      | OVERALL_DECISION | PASS_EXPECTED | FAIL            | OVERLY_STRICT_SCORING |
| BFSI-B-001      | OVERALL_DECISION | PASS_EXPECTED | FAIL            | OVERLY_STRICT_SCORING |
| BFSI-B-005      | OVERALL_DECISION | PASS_EXPECTED | FAIL            | OVERLY_STRICT_SCORING |
| BFSI-B-017      | OVERALL_DECISION | PASS_EXPECTED | REVIEW_REQUIRED | OVERLY_STRICT_SCORING |

**Judge vs human labels:** PENDING — human annotations incomplete.

---
_Built 2026-10-13T06:53:20+00:00 from committed artifacts._
