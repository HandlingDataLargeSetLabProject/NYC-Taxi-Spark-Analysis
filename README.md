# HLDS Lab Project: Data Processing and Analysis with Apache Spark

Laboratory project for the *Handling Large Data Sets* course (Project 2, Apache Spark).

We build one analytical workflow over the semester: environment setup, data preparation, distributed processing with PySpark and Spark SQL, performance optimization, and visualization. The same dataset and topic are used in all three reports.

> The dataset and the analytical problem are not chosen yet. The repository name will change once the topic is fixed.

## Team
| Member | Branch |
|---|---|
| Alican Kaya | `alican` |
| Berke Arda Türk | `berke` |

## Reports
| Report | Topic | Deadline |
|---|---|---|
| Report 1 | Data preparation and Spark environment setup | 18 Nov 2026, 23:59 |
| Report 2 | Data processing, analysis and optimization | 23 Dec 2026, 23:59 |
| Report 3 | Visualization and project summary | 14 Jan 2027, 23:59 |

## Repository layout
```
docs/        plan, requirements summary, data dictionary, contributions
src/hlds/    shared Spark helpers, cleaning, queries, optimizations
scripts/     data download and benchmark scripts
results/     small aggregated outputs and charts
reports/     report sources and screenshots
data/        local data files (not tracked)
```

## Getting started
Environment setup (Python, Java, PySpark) is described in `docs/environment.md` once it is written. Work rules are in [CONTRIBUTING.md](CONTRIBUTING.md) and the task list is in [docs/PLAN.md](docs/PLAN.md).
