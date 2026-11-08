"""Run query Q1 on the six months and write its results to results/q1_*.csv.

Run: python scripts/query_demand.py
"""

import sys
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hlds.cleaning import clean_trips
from hlds.demand import add_pickup_parts, daily_average_by_year, daily_trips, hour_weekday_trips
from hlds.loading import load_trips
from hlds.paths import RESULTS_DIR
from hlds.results import write_csv
from hlds.session import get_spark


def main():
    spark = get_spark("q1-demand")
    spark.sparkContext.setLogLevel("ERROR")
    trips = add_pickup_parts(clean_trips(load_trips(spark)))

    daily = daily_trips(trips)
    write_csv(daily, RESULTS_DIR / "q1_daily_trips.csv")
    averages = daily_average_by_year(daily)
    write_csv(averages, RESULTS_DIR / "q1_daily_average.csv")
    write_csv(hour_weekday_trips(trips), RESULTS_DIR / "q1_hour_weekday.csv")

    for row in averages.collect():
        print(f"{row['year']}: {row['trips']:,} trips on {row['days']} days, {row['trips_per_day']:,} per day")
    spark.stop()


if __name__ == "__main__":
    main()
