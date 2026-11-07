# Project plan

Week 1 (W1) starts on Monday, 26 October 2026. Statuses: `todo`, `doing`, `review`, `done`.

## Deadlines
| Report | Deadline | Our target |
|---|---|---|
| Report 1 | 18 Nov 2026, 23:59 | 17 Nov |
| Report 2 | 23 Dec 2026, 23:59 | 22 Dec |
| Report 3 | 14 Jan 2027, 23:59 | 13 Jan |

Report 3 has only about three weeks including the holidays, so the aggregated outputs and first chart drafts are prepared during Report 2.

## Tasks
| ID | Week | Owner | Task | Status |
|---|---|---|---|---|
| S-01 | W0 (21–25 Oct) | Alican | Repository skeleton and project documents | done |
| S-02 | W0 (21–25 Oct) | Berke | Local setup: Git, Python, Java, PySpark; clone and switch to `berke` | done |
| S-03 | W0 (21–25 Oct) | Alican | Add our project choice to the Teams group file | done |
| R1-01 | W1 (26 Oct–1 Nov) | Alican | Shared helpers: `session.py`, `paths.py`, `timing.py` | done |
| R1-02 | W1 (26 Oct–1 Nov) | Berke | `docs/environment.md` with setup steps and screenshots; pinned `requirements.txt` | done |
| R1-03 | W1 (26 Oct–1 Nov) | Both | Choose the dataset and the analytical problem (dataset: NYC yellow taxi trips, Jan–Mar 2024 and Jan–Mar 2025; problem in `docs/analysis-plan.md`) | done |
| R1-04 | W2 (2–8 Nov) | Alican | `scripts/download_data.py` for the monthly Parquet files and the zone lookup table | done |
| R1-05 | W2 (2–8 Nov) | Alican | Cleaning: missing values and type conversions | done |
| R1-06 | W2 (2–8 Nov) | Berke | Load the data into Spark; document the schema in `data-dictionary.md` | done |
| R1-07 | W2 (2–8 Nov) | Berke | Cleaning: duplicates and invalid rows | done |
| R1-08 | W3 (9–15 Nov) | Alican | Analytical objectives for Reports 2 and 3 | done |
| R1-09 | W3 (9–15 Nov) | Berke | Descriptive statistics and the summary table | done |
| R1-10 | W3 (9–15 Nov) | Alican | Report 1 sections: dataset, problem, cleaning | done |
| R1-11 | W3 (9–15 Nov) | Berke | Report 1 sections: environment, statistics, problems and solutions | done |
| R1-12 | W4 (16–18 Nov) | Alican | Final edit and submission of Report 1 | done |
| R1-13 | W4 (16–18 Nov) | Berke | Report 1 code excerpts, screenshots, contribution section | done |
| R2-01 | W4–W5 (19–29 Nov) | Alican | Query Q1 (filtering, grouping, aggregation) | todo |
| R2-02 | W5 (23–29 Nov) | Alican | Query Q2 | todo |
| R2-03 | W4–W5 (19–29 Nov) | Berke | Query Q3 with a join | todo |
| R2-04 | W5 (23–29 Nov) | Berke | Query Q4 (time-based or category analysis) | todo |
| R2-05 | W6 (30 Nov–6 Dec) | Alican | `scripts/run_benchmarks.py` | todo |
| R2-06 | W6 (30 Nov–6 Dec) | Alican | Optimization O1: caching / persistence | todo |
| R2-07 | W6 (30 Nov–6 Dec) | Berke | Optimization O2: broadcast join | todo |
| R2-08 | W6 (30 Nov–6 Dec) | Berke | Optimization O3: partitioning or columnar storage | todo |
| R2-09 | W7 (7–13 Dec) | Alican | Before/after measurements on own machine; timing table | todo |
| R2-10 | W7 (7–13 Dec) | Berke | Before/after measurements on own machine; aggregated outputs in `results/` | todo |
| R2-11 | W8 (14–20 Dec) | Alican | Report 2 sections: queries and optimizations; first chart drafts | todo |
| R2-12 | W8 (14–20 Dec) | Berke | Report 2 sections: interpretation, problems and solutions; choose the dashboard tool | todo |
| R2-13 | W9 (21–23 Dec) | Alican | Final edit and submission of Report 2 | todo |
| R2-14 | W9 (21–23 Dec) | Berke | Report 2 code excerpts and contribution section | todo |
| R3-01 | W10 (28 Dec–3 Jan) | Alican | Charts for Q1, Q2 and the performance results | todo |
| R3-02 | W10 (28 Dec–3 Jan) | Berke | Charts for Q3, Q4; dashboard draft | todo |
| R3-03 | W11 (4–10 Jan) | Alican | Chart interpretation; limitations and possible improvements | todo |
| R3-04 | W11 (4–10 Jan) | Berke | Dashboard; key findings and their practical meaning | todo |
| R3-05 | W12 (11–14 Jan) | Alican | Final edit and submission of Report 3 | todo |
| R3-06 | W12 (11–14 Jan) | Berke | Dashboard screenshots and contribution section | todo |

## Notes
- Each member commits on at least three different days per week.
- MLlib is optional; we decide during W8 whether to add it.
