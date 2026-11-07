"""Print the numbers behind the summer time decision in docs/analysis-plan.md."""

import sys
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyspark.sql import functions as F

from hlds.cleaning import clean_trips
from hlds.loading import load_trips
from hlds.session import get_spark

# The nights when the clocks in New York jumped from 02:00 to 03:00.
SUMMER_TIME_DAYS = ["2024-03-10", "2025-03-09"]
NEW_YORK = "America/New_York"


def at(day, time):
    return F.lit(f"{day} {time}").cast("timestamp_ntz")


def new_york_to_utc(column):
    return F.to_utc_timestamp(F.col(column).cast("timestamp"), NEW_YORK)


def print_skipped_hour(trips):
    pickup, dropoff = F.col("tpep_pickup_datetime"), F.col("tpep_dropoff_datetime")
    for day in SUMMER_TIME_DAYS:
        start, end = at(day, "02:00:00"), at(day, "03:00:00")
        in_hour = ((pickup >= start) & (pickup < end)) | ((dropoff >= start) & (dropoff < end))
        print(f"{day}: rows with a time between 02:00 and 03:00: {trips.filter(in_hour).count():,}")


def print_duration_change(trips):
    clock = F.timestamp_diff("SECOND", F.col("tpep_pickup_datetime"), F.col("tpep_dropoff_datetime"))
    real = F.timestamp_diff("SECOND", new_york_to_utc("tpep_pickup_datetime"), new_york_to_utc("tpep_dropoff_datetime"))
    changed = trips.filter(clock != real).agg(
        F.count("*").alias("rows"),
        F.min(clock - real).alias("smallest_change"),
        F.max(clock - real).alias("largest_change"),
        F.percentile_approx(clock / 60, 0.5).alias("clock_median"),
        F.percentile_approx(real / 60, 0.5).alias("real_median"),
    ).first()
    print(f"Trips whose duration changes: {changed['rows']:,}")
    print(f"Change in seconds: {changed['smallest_change']} to {changed['largest_change']}")
    print(f"Median duration in minutes: {changed['clock_median']:.0f} by clock, {changed['real_median']:.0f} after the conversion")
    print(f"Durations of 0 seconds or less after the conversion: {trips.filter(real <= 0).count():,}")


def main():
    spark = get_spark("check-summer-time")
    spark.sparkContext.setLogLevel("ERROR")
    trips = clean_trips(load_trips(spark))
    print_skipped_hour(trips)
    print_duration_change(trips)
    spark.stop()


if __name__ == "__main__":
    main()
