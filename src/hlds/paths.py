"""File locations used by all scripts, relative to the repository root."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
ZONE_LOOKUP_FILE = RAW_DIR / "taxi_zone_lookup.csv"

# The zone charge started in January 2025, so the same months of 2024 are the comparison without it.
DEFAULT_MONTHS = ["2024-01", "2024-02", "2024-03", "2025-01", "2025-02", "2025-03"]
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def trip_file(month):
    if not MONTH_PATTERN.match(month):
        raise ValueError(f"month must look like YYYY-MM, got {month!r}")
    return RAW_DIR / f"yellow_tripdata_{month}.parquet"


def trip_files(months=DEFAULT_MONTHS):
    return [trip_file(month) for month in months]
