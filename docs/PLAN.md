# Project plan

Week 1 (W1) starts on Monday, 26 October 2026. Statuses: `todo`, `doing`, `review`, `done`.

## Deadlines
| Report | Deadline | Our target |
|---|---|---|
| Report 1 | 18 Nov 2026, 23:59 | 17 Nov |
| Report 2 | 23 Dec 2026, 23:59 | 9 Dec |
| Report 3 | 14 Jan 2027, 23:59 | 6 Jan |

Report 1 was submitted on 7 November, so Reports 2 and 3 were moved earlier. Report 3 falls in the holidays, so every query saves its aggregated output in `results/` during Report 2 and the charts can start right after.

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
| R2-05 | W3 (9–15 Nov) | Alican | `scripts/run_benchmarks.py` skeleton on `timing.measure`: saves the `explain()` plan and writes times to `results/timings_<machine>.csv`; first trial run (clean + count) | done |
| R2-01 | W3–W4 (9–22 Nov) | Alican | Query Q1: daily trend, daily average per year, hour × weekday table; output in `results/` | done |
| R2-02 | W3–W4 (9–22 Nov) | Alican | Query Q2: durations from New York time converted to UTC, speed, price per mile, tip %; output in `results/` | done |
| R2-03 | W3–W4 (9–22 Nov) | Berke | Query Q3 with the zone joins; output in `results/`; first trial run on own machine | done |
| R2-04 | W3–W4 (9–22 Nov) | Berke | Query Q4: zone charge trips without `has_negative_part`, charge period by date; output in `results/` | done |
| R2-06 | W4–W5 (16–29 Nov) | Alican | Optimization O1: caching / persistence on the Q1 + Q2 sequence (after R2-01, R2-02, R2-05) | done |
| R2-07 | W4–W5 (16–29 Nov) | Berke | Optimization O2: broadcast join; check with `explain()` that the run before is a shuffle join (after R2-03, R2-04, R2-05) | done |
| R2-08 | W4–W5 (16–29 Nov) | Berke | Optimization O3: cleaned table as plain Parquet (before) and partitioned by pickup date (after) | todo |
| R2-09 | W5 (23–29 Nov) | Alican | O1 before/after measurements on own machine | done |
| R2-10 | W5 (23–29 Nov) | Berke | O2 and O3 before/after measurements on own machine | todo |
| R2-15 | W5 (23–29 Nov) | Alican | Adapt the report build script for Report 2 | todo |
| R2-11 | W6 (30 Nov–6 Dec) | Alican | Report 2 sections: introduction, measuring method, Q1, Q2, O1, own problems and solutions | todo |
| R2-12 | W6 (30 Nov–6 Dec) | Berke | Report 2 sections: Q3, Q4, O2, O3, own problems and solutions; choose the dashboard tool | todo |
| R2-14 | W6 (30 Nov–6 Dec) | Berke | Report 2 code excerpts and contribution lines | todo |
| R2-16 | W6–W7 (3–8 Dec) | Alican | Report 2 section: what the four queries show together (2025 against 2024, effect of the zone charge) | todo |
| R2-13 | W7 (7–9 Dec) | Alican | Final edit and submission of Report 2 (after R2-11 to R2-16) | todo |
| R3-01 | W7–W8 (10–20 Dec) | Alican | Charts for Q1, Q2 and the performance results | todo |
| R3-02 | W7–W8 (10–20 Dec) | Berke | Charts for Q3, Q4; dashboard draft | todo |
| R3-03 | W9–W10 (21 Dec–3 Jan) | Alican | Chart interpretation; limitations and possible improvements | todo |
| R3-04 | W9–W10 (21 Dec–3 Jan) | Berke | Dashboard; key findings and their practical meaning | todo |
| R3-06 | W11 (4–5 Jan) | Berke | Dashboard screenshots and contribution lines | todo |
| R3-05 | W11 (4–6 Jan) | Alican | Final edit and submission of Report 3 | todo |

## Notes
- Each member commits on at least three different days per week.
- MLlib is optional; we decide during W6 whether to add it.
- If on 29 November fewer than two optimizations have a working before/after run, O3 becomes optional. If on 2 December the timing table is not ready, we skip MLlib.
