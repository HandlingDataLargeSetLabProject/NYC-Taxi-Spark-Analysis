"""Run query Q4 on the six months and write its results to results/q4_*.csv.

Run: python scripts/query_congestion.py
"""

import csv
import sys
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hlds.cleaning import clean_trips
from hlds.congestion import charge_summary, charge_window, zone_charge_summary
from hlds.loading import load_trips, load_zones
from hlds.paths import RESULTS_DIR
from hlds.places import add_zone_names, quarter_days
from hlds.results import write_csv
from hlds.session import get_spark


def main():
    spark = get_spark("q4-congestion")
    spark.sparkContext.setLogLevel("ERROR")
    trips = charge_window(clean_trips(load_trips(spark)))
    # Counted once here, so the queries below do not read the six months again only for the number of days.
    days = spark.createDataFrame(quarter_days(trips).collect())
    named = add_zone_names(trips, load_zones(spark))

    write_csv(charge_summary(trips, days, []), RESULTS_DIR / "q4_overview.csv")
    write_csv(charge_summary(trips, days, ["hour"]), RESULTS_DIR / "q4_by_hour.csv")
    write_csv(zone_charge_summary(named, days, "pickup"), RESULTS_DIR / "q4_by_pickup_zone.csv")
    write_csv(zone_charge_summary(named, days, "dropoff"), RESULTS_DIR / "q4_by_dropoff_zone.csv")

    for row in days.orderBy("year").collect():
        print(f"{row['year']}: {row['days']} days from 5 January")
    # Printed from the written file, because asking Spark again would read the six months again.
    with open(RESULTS_DIR / "q4_overview.csv", newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            print(f"{row['year']} {row['charge_group']:<16} {row['trips_per_day']:>10} per day, share {row['share']}, "
                  f"median total {row['median_total_amount']} $, median distance {row['median_trip_distance']} mi")
    spark.stop()


if __name__ == "__main__":
    main()
