# Threshold-sensitivity results

_Critical-gate overrides remain active at every cutoff. The full-synthetic population has no human ground truth; the human-labelled columns are populated only when the 30-label batch is complete._

## Rubric v1
|   cutoff |   n_pass |   n_fail |   n_review_required |   pass_rate |   critical_gate_overrides |   est_reviewed_calls_per_month | human_agreement   | false_pass_count   | false_fail_count   |
|---------:|---------:|---------:|--------------------:|------------:|--------------------------:|-------------------------------:|:------------------|:-------------------|:-------------------|
|       50 |       49 |       20 |                  31 |        0.49 |                        29 |                          21795 |                   |                    |                    |
|       55 |       42 |       27 |                  31 |        0.42 |                        29 |                          22900 |                   |                    |                    |
|       60 |       40 |       29 |                  31 |        0.4  |                        29 |                          24070 |                   |                    |                    |
|       65 |       32 |       37 |                  31 |        0.32 |                        29 |                          25990 |                   |                    |                    |
|       70 |       24 |       45 |                  31 |        0.24 |                        29 |                          27220 |                   |                    |                    |
|       75 |       22 |       48 |                  30 |        0.22 |                        29 |                          28025 |                   |                    |                    |
|       80 |       15 |       55 |                  30 |        0.15 |                        29 |                          29015 |                   |                    |                    |
|       85 |       14 |       56 |                  30 |        0.14 |                        29 |                          29945 |                   |                    |                    |
|       90 |        7 |       63 |                  30 |        0.07 |                        29 |                          31050 |                   |                    |                    |

Calls that change classification between consecutive cutoffs:
|   from_cutoff |   to_cutoff | transcript_id   |   overall_score | decision_before   | decision_after   |
|--------------:|------------:|:----------------|----------------:|:------------------|:-----------------|
|            50 |          55 | BFSI-A-006      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-B-002      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-B-003      |          51.562 | PASS              | FAIL             |
|            50 |          55 | BFSI-B-018      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-C-006      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-C-015      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-E-018      |          52.5   | PASS              | FAIL             |
|            55 |          60 | BFSI-A-001      |          58.75  | PASS              | FAIL             |
|            55 |          60 | BFSI-D-014      |          57.5   | PASS              | FAIL             |
|            60 |          65 | BFSI-A-003      |          60     | PASS              | FAIL             |
|            60 |          65 | BFSI-A-007      |          60.938 | PASS              | FAIL             |
|            60 |          65 | BFSI-B-001      |          62.5   | PASS              | FAIL             |

## Rubric v2
|   cutoff |   n_pass |   n_fail |   n_review_required |   pass_rate |   critical_gate_overrides |   est_reviewed_calls_per_month | human_agreement   | false_pass_count   | false_fail_count   |
|---------:|---------:|---------:|--------------------:|------------:|--------------------------:|-------------------------------:|:------------------|:-------------------|:-------------------|
|       50 |       49 |       20 |                  31 |        0.49 |                        29 |                          21795 |                   |                    |                    |
|       55 |       42 |       27 |                  31 |        0.42 |                        29 |                          22900 |                   |                    |                    |
|       60 |       40 |       29 |                  31 |        0.4  |                        29 |                          24070 |                   |                    |                    |
|       65 |       32 |       37 |                  31 |        0.32 |                        29 |                          25990 |                   |                    |                    |
|       70 |       24 |       45 |                  31 |        0.24 |                        29 |                          27220 |                   |                    |                    |
|       75 |       22 |       48 |                  30 |        0.22 |                        29 |                          28025 |                   |                    |                    |
|       80 |       15 |       55 |                  30 |        0.15 |                        29 |                          29015 |                   |                    |                    |
|       85 |       14 |       56 |                  30 |        0.14 |                        29 |                          29945 |                   |                    |                    |
|       90 |        7 |       63 |                  30 |        0.07 |                        29 |                          31050 |                   |                    |                    |

Calls that change classification between consecutive cutoffs:
|   from_cutoff |   to_cutoff | transcript_id   |   overall_score | decision_before   | decision_after   |
|--------------:|------------:|:----------------|----------------:|:------------------|:-----------------|
|            50 |          55 | BFSI-A-006      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-B-002      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-B-003      |          51.562 | PASS              | FAIL             |
|            50 |          55 | BFSI-B-018      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-C-006      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-C-015      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-E-018      |          52.5   | PASS              | FAIL             |
|            55 |          60 | BFSI-A-001      |          58.75  | PASS              | FAIL             |
|            55 |          60 | BFSI-D-014      |          57.5   | PASS              | FAIL             |
|            60 |          65 | BFSI-A-003      |          60     | PASS              | FAIL             |
|            60 |          65 | BFSI-A-007      |          60.938 | PASS              | FAIL             |
|            60 |          65 | BFSI-B-001      |          62.5   | PASS              | FAIL             |

## Rubric v3
|   cutoff |   n_pass |   n_fail |   n_review_required |   pass_rate |   critical_gate_overrides |   est_reviewed_calls_per_month | human_agreement   | false_pass_count   | false_fail_count   |
|---------:|---------:|---------:|--------------------:|------------:|--------------------------:|-------------------------------:|:------------------|:-------------------|:-------------------|
|       50 |       49 |       20 |                  31 |        0.49 |                        29 |                          21795 |                   |                    |                    |
|       55 |       42 |       27 |                  31 |        0.42 |                        29 |                          22900 |                   |                    |                    |
|       60 |       40 |       29 |                  31 |        0.4  |                        29 |                          24070 |                   |                    |                    |
|       65 |       32 |       37 |                  31 |        0.32 |                        29 |                          25990 |                   |                    |                    |
|       70 |       24 |       45 |                  31 |        0.24 |                        29 |                          27220 |                   |                    |                    |
|       75 |       22 |       48 |                  30 |        0.22 |                        29 |                          28025 |                   |                    |                    |
|       80 |       15 |       55 |                  30 |        0.15 |                        29 |                          29015 |                   |                    |                    |
|       85 |       14 |       56 |                  30 |        0.14 |                        29 |                          29945 |                   |                    |                    |
|       90 |        7 |       63 |                  30 |        0.07 |                        29 |                          31050 |                   |                    |                    |

Calls that change classification between consecutive cutoffs:
|   from_cutoff |   to_cutoff | transcript_id   |   overall_score | decision_before   | decision_after   |
|--------------:|------------:|:----------------|----------------:|:------------------|:-----------------|
|            50 |          55 | BFSI-A-006      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-B-002      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-B-003      |          51.562 | PASS              | FAIL             |
|            50 |          55 | BFSI-B-018      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-C-006      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-C-015      |          52.5   | PASS              | FAIL             |
|            50 |          55 | BFSI-E-018      |          52.5   | PASS              | FAIL             |
|            55 |          60 | BFSI-A-001      |          58.75  | PASS              | FAIL             |
|            55 |          60 | BFSI-D-014      |          57.5   | PASS              | FAIL             |
|            60 |          65 | BFSI-A-003      |          60     | PASS              | FAIL             |
|            60 |          65 | BFSI-A-007      |          60.938 | PASS              | FAIL             |
|            60 |          65 | BFSI-B-001      |          62.5   | PASS              | FAIL             |

---
_Built 2026-10-13T06:53:20+00:00 from committed artifacts._
