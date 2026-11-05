# Contributing

How the two of us work in this repository.

## Branches
- Each member works on their own branch: `alican` or `berke`.
- `main` holds the merged, working state of the project.
- A finished task goes into `main` through a pull request from the owner's branch. The other member takes a look before it is merged.
- Before starting new work, merge the latest `main` into your own branch.

## Taking turns
- We push one after the other. Before pushing, run `git fetch`; if `main` has moved, merge it into your branch first and fix any conflicts on your side.
- Tasks are split by owner in [docs/PLAN.md](docs/PLAN.md). If you need to change a file that belongs to the other member's task, ask first.
- If one of us finds a bug, we tell each other and both fix it on our own branches where it applies.

## Commits
- Small commits, one logical change each, made on the day the work is done.
- Short English message in the imperative, at most 72 characters, for example `Add duplicate row check to cleaning step`.
- No force pushes and no rewriting of history that is already on GitHub.

## Code
- Python 3 with PySpark and Spark SQL.
- Use the shared helpers in `src/hlds/` (`session.py`, `paths.py`, `timing.py`, `loading.py`, `cleaning.py`) so that all scripts create Spark, load and clean the data, and measure time the same way.
- Keep functions short and names clear. Add a comment when the reason for a step is not obvious.
- New packages go into `requirements.txt` with a fixed version, after both of us agree.
- Run the tests from the repository root with `python -m unittest discover -s tests -t .` (the Spark session tests take about a minute).

## Data
- Data files stay in `data/` and are never committed. `scripts/download_data.py` recreates them.
- Column names and types are documented in [docs/data-dictionary.md](docs/data-dictionary.md). Update it when the schema changes.

## Performance measurements
- Each before/after comparison is run on one computer, with the same dataset and the same Spark configuration.
- Use `src/hlds/timing.py`, repeat each run several times and report the median.
- Write the machine details (CPU, RAM, Spark settings) next to every result. Timings from different computers are not compared with each other.

## Tracking work
- When a task is finished, set its status to `done` in [docs/PLAN.md](docs/PLAN.md).
- Add one line to [docs/contributions.md](docs/contributions.md) under the right report. Each report has a contribution section built from this file.
