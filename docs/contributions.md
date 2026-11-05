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

## Report 2
| Member | Work | Files |
|---|---|---|

## Report 3
| Member | Work | Files |
|---|---|---|
