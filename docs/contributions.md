# Team contributions

One line per finished task. Each report's contribution section is built from this file.

## Report 1
| Member | Work | Files |
|---|---|---|
| Alican Kaya | Set up the repository, the project plan and the work rules | `README.md`, `CONTRIBUTING.md`, `docs/` |
| Alican Kaya | Found the dataset, documented its source and fields, wrote the download script | `docs/data-dictionary.md`, `scripts/download_data.py` |
| Alican Kaya | Registered our project choice in the course group file | — |
| Alican Kaya | Drafted the analytical problem, objectives, queries and optimizations | `docs/analysis-plan.md` |
| Berke Arda Türk | Set up the local environment (Git, Python, Java 17, PySpark), cloned the repository and reviewed the dataset pull request | — |
| Berke Arda Türk | Wrote the environment setup guide with screenshots and pinned the Python packages | `docs/environment.md`, `requirements.txt`, `reports/screenshots/` |
| Alican Kaya | Set up Spark on his own laptop and added it to the environment guide | `docs/environment.md` |
| Alican Kaya | Wrote the shared helpers for paths, the Spark session and timing, with tests | `src/hlds/`, `tests/` |
| Alican Kaya, Berke Arda Türk | Decided to add January to March 2024 for a before and after comparison; Berke checked the 2024 files, Alican updated the plan, the data dictionary and the default months | `docs/analysis-plan.md`, `docs/data-dictionary.md`, `src/hlds/paths.py`, `scripts/download_data.py` |
| Berke Arda Türk | Loaded the six months into Spark and documented the schema, types and missing values | `src/hlds/loading.py`, `scripts/profile_raw_data.py`, `tests/test_loading.py`, `docs/data-dictionary.md` |
| Alican Kaya | Cleaned missing values and converted types, keeping every row and marking flex fare trips and the zone charge period, with tests | `src/hlds/cleaning.py`, `tests/test_cleaning.py`, `docs/data-dictionary.md`, `docs/analysis-plan.md` |
| Berke Arda Türk | Dropped invalid and duplicate rows, marked trips with a negative price part and measured each rule, with tests; Alican checked the numbers on his laptop | `src/hlds/cleaning.py`, `tests/test_invalid_rows.py`, `scripts/profile_cleaning.py`, `docs/data-dictionary.md`, `docs/analysis-plan.md` |
| Berke Arda Türk | Wrote the descriptive statistics and the summary tables for the cleaned data, with tests | `src/hlds/statistics.py`, `tests/test_statistics.py`, `scripts/describe_trips.py`, `results/descriptive_statistics.md` |
| Alican Kaya, Berke Arda Türk | Fixed the Spark session time zone to UTC after Berke found negative durations, and raised the driver memory to 6g after the summary script ran out of memory on Alican's laptop, with tests | `src/hlds/session.py`, `tests/test_session.py` |
| Alican Kaya | Finalized the objectives and the measures of Q1 and Q2, including the New York summer time correction | `docs/analysis-plan.md` |
| Alican Kaya | Wrote the Report 1 sections on the dataset, the problem, the objectives and the cleaning | `reports/report1/alican-sections.md` |
| Alican Kaya | Wrote the script that joins the report sections and builds the Word and PDF files | `reports/report1/build_report.py`, `reports/report1/to_word.ps1` |
| Berke Arda Türk | Wrote the Report 1 sections on the Spark environment, loading the data, the descriptive statistics, the problems and solutions and the code excerpts, and took the screenshot of the loaded data | `reports/report1/berke-sections.md`, `reports/screenshots/loaded-data.png` |
| Alican Kaya | Built the final Word and PDF report and the source code package | `reports/report1/build_report.py`, `reports/report1/to_word.ps1` |
| Berke Arda Türk | Uploaded Report 1 and the source code package to Teams | — |

## Report 2
| Member | Work | Files |
|---|---|---|
| Alican Kaya | Wrote the measuring script for the optimizations, which saves the final query plan and the times with the machine details, with tests | `src/hlds/benchmarks.py`, `scripts/run_benchmarks.py`, `tests/test_benchmarks.py`, `src/hlds/paths.py` |
| Alican Kaya | Wrote query Q1 on demand by day, hour and weekday (DataFrame API and Spark SQL) and the shared CSV writer for the results, with tests | `src/hlds/demand.py`, `src/hlds/results.py`, `scripts/query_demand.py`, `tests/test_demand.py`, `results/q1_*.csv`, `docs/data-dictionary.md` |
| Alican Kaya | Wrote query Q2 on duration, speed, price per mile and tips by hour and payment type, with the New York summer time correction, with tests | `src/hlds/prices.py`, `scripts/query_prices.py`, `tests/test_prices.py`, `results/q2_*.csv`, `docs/data-dictionary.md` |
| Berke Arda Türk | Wrote query Q3 on pickup and drop-off zones, borough flows, the busiest routes (Spark SQL) and airport trips, with the zone table joined for both ends, with tests; first trial run of the measuring script on my laptop | `src/hlds/places.py`, `scripts/query_places.py`, `tests/test_places.py`, `results/q3_*.csv`, `results/timings_berke.csv`, `results/plans/berke/`, `docs/data-dictionary.md` |
| Berke Arda Türk | Wrote query Q4 on the congestion relief zone charge: both years from 5 January to 31 March, the share of trips paying the charge and their median price by hour and zone, with tests; fixed the local path in my pilot plan | `src/hlds/congestion.py`, `scripts/query_congestion.py`, `tests/test_congestion.py`, `results/q4_*.csv`, `results/plans/berke/pilot_clean_count.txt`, `docs/analysis-plan.md`, `docs/data-dictionary.md` |
| Alican Kaya | Wrote optimization O1, caching the cleaned table for the five results of Q1 and Q2, and measured it before and after on my laptop (median 281.5 s without the cache, 187.7 s with it), with tests | `src/hlds/caching.py`, `scripts/run_benchmarks.py`, `tests/test_caching.py`, `results/timings_alican.csv`, `results/plans/alican/O1_*.txt` |
| Berke Arda Türk | Wrote optimization O2, the zone joins of Q3 as a sort merge join (automatic broadcast off) and as a broadcast join, and measured it before and after on my laptop (median 24.5 s with the shuffle join, 18.7 s with the broadcast join), with tests that check the join type in the saved plan | `src/hlds/joins.py`, `scripts/run_benchmarks.py`, `tests/test_joins.py`, `results/timings_berke.csv`, `results/plans/berke/O2_*.txt` |
| Berke Arda Türk | Wrote optimization O3, the cleaned table written as plain Parquet and as Parquet partitioned by pickup date and read with the same date filter (March 2025), and measured it before and after on my laptop (median 1.98 s from the plain copy, 1.15 s from the partitioned copy), with tests | `src/hlds/storage.py`, `scripts/write_clean_tables.py`, `scripts/run_benchmarks.py`, `tests/test_storage.py`, `results/timings_berke.csv`, `results/plans/berke/O3_*.txt`, `docs/data-dictionary.md` |
| Alican Kaya | Adapted the report build script for Report 2: the agreed section order, placeholders that name the owner, and one shared section (problems and solutions) joined from both our files, with tests | `reports/report2/build_report.py`, `tests/test_report2_build.py`, `.gitignore` |

## Report 3
| Member | Work | Files |
|---|---|---|
