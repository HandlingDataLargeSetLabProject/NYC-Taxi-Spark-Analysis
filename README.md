# NYC Taxi Spark Analysis

Laboratory project for the *Handling Large Data Sets* course (Project 2, Apache Spark). We use PySpark, the DataFrame API and Spark SQL to study about 20 million NYC yellow taxi trips, and we measure how much a few common Spark optimizations change the run time.

**Question:** how do demand, prices and tipping of NYC yellow taxi trips change by time and place in the first quarter of 2025 compared with the first quarter of 2024, and how much of this traffic is affected by the new Manhattan congestion relief zone charge?

The charge started on 5 January 2025, so the first quarter of 2025 is the first one with it in the data, and the first quarter of 2024 is the same season one year earlier without it. The full problem, objectives and cleaning rules are in [docs/analysis-plan.md](docs/analysis-plan.md).

## Status
| Report | Topic | Status |
|---|---|---|
| Report 1 | Spark environment and data preparation | submitted on 7 Nov 2026 |
| Report 2 | Queries and optimizations | code done, report in progress |
| Report 3 | Visualization and project summary | not started |

The task list with owners is in [docs/PLAN.md](docs/PLAN.md).

## Dataset
- [NYC TLC Yellow Taxi Trip Records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), January to March of 2024 and 2025, one Parquet file per month, plus the zone lookup table (265 zones).
- 20,752,804 raw trips; 19,926,016 (96.0%) are left after cleaning.
- Columns, types, missing values and the effect of each cleaning rule are in [docs/data-dictionary.md](docs/data-dictionary.md).

## Queries
| Query | What it answers | Code |
|---|---|---|
| Q1 | Demand by day, hour and weekday, daily average per year | `src/hlds/demand.py` |
| Q2 | Duration, speed, price per mile and tips by hour and payment type | `src/hlds/prices.py` |
| Q3 | Busiest pickup and drop-off zones, borough flows, top routes, airport trips | `src/hlds/places.py` |
| Q4 | Trips that pay the congestion charge, by hour and zone, and their price | `src/hlds/congestion.py` |

Each query writes small aggregated CSV files to [results/](results/), so the charts for Report 3 can be drawn without running Spark again.

Some first results:
- The cleaned table has 101,401 trips per day in the first quarter of 2024 and 118,872 in 2025, 17.2% more.
- From 5 January to 31 March 2025, 74% of the trips in Q4 pay the congestion charge. Their median total price is 21.54 dollars, against 18.45 dollars for the trips that do not pay it.

## Optimizations
Each optimization was measured on its owner's laptop: one warm-up run and five measured runs, median shown. The two laptops are different, so the times should only be compared within a row.

| Optimization | Before | After | Median before | Median after | Change |
|---|---|---|---|---|---|
| O1 caching, Q1 and Q2 in a row | clean the raw files for every result | clean once and `cache()` | 281.5 s | 187.7 s | -33.3% |
| O2 broadcast join, zone joins of Q3 | sort merge join | `broadcast()` on the zone table | 24.5 s | 18.7 s | -23.6% |
| O3 storage, March 2025 daily summary | plain Parquet | Parquet partitioned by pickup date | 1.98 s | 1.15 s | -41.9% |

The times with the machine details are in `results/timings_alican.csv` and `results/timings_berke.csv`, and the final query plan of every run is in `results/plans/`.

## Running it
The setup of Python, Java 17 or newer and PySpark 4.2.0 on Windows is described step by step in [docs/environment.md](docs/environment.md). After that, from the repository root:

```
python scripts/download_data.py        # six monthly files and the zone table into data/raw/ (about 350 MB)
python scripts/query_demand.py         # Q1, and the same for query_prices.py, query_places.py, query_congestion.py
python scripts/write_clean_tables.py   # cleaned copies for O3 in data/derived/
python scripts/run_benchmarks.py --machine <label> [--case O1] [--repeats 5]
python -m unittest discover -s tests -t .
```

## Repository layout
```
docs/        plan, analysis plan, data dictionary, environment guide, contributions
src/hlds/    Spark session, loading, cleaning, queries, optimizations, timing
scripts/     download, query, benchmark and profiling scripts
results/     aggregated query outputs, timings and saved query plans
reports/     report sources, build scripts and screenshots
tests/       unit tests, most of them on a small local Spark session
data/        local data files (not tracked)
```

## Team
| Member | Branch |
|---|---|
| Alican Kaya | `alican` |
| Berke Arda Türk | `berke` |

Work rules are in [CONTRIBUTING.md](CONTRIBUTING.md), and who did what for each report is in [docs/contributions.md](docs/contributions.md).
