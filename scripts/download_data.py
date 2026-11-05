"""Download NYC TLC yellow taxi trip records and the taxi zone lookup table into data/raw."""

import argparse
import re
import sys
import urllib.request
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hlds.paths import DEFAULT_MONTHS

BASE_URL = "https://d37ci6vzurychx.cloudfront.net"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def trip_url(month):
    return f"{BASE_URL}/trip-data/yellow_tripdata_{month}.parquet"


def zone_lookup_url():
    return f"{BASE_URL}/misc/taxi_zone_lookup.csv"


def download(url, target):
    if target.exists():
        print(f"skip {target.name}, already downloaded")
        return
    # Write to a temporary name first so an interrupted download is never mistaken for a full file.
    partial = target.with_name(target.name + ".part")
    print(f"downloading {url}")
    urllib.request.urlretrieve(url, partial)
    partial.replace(target)
    print(f"saved {target} ({target.stat().st_size / 1_000_000:.1f} MB)")


def parse_args():
    parser = argparse.ArgumentParser(description="Download NYC yellow taxi trip data.")
    parser.add_argument(
        "--months",
        nargs="+",
        default=DEFAULT_MONTHS,
        help="months to download as YYYY-MM (default: %(default)s)",
    )
    args = parser.parse_args()
    for month in args.months:
        if not MONTH_PATTERN.match(month):
            parser.error(f"month must look like YYYY-MM, got {month!r}")
    return args


def main():
    args = parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    download(zone_lookup_url(), RAW_DIR / "taxi_zone_lookup.csv")
    for month in args.months:
        download(trip_url(month), RAW_DIR / f"yellow_tripdata_{month}.parquet")


if __name__ == "__main__":
    main()
