"""Run query Q3 on the six months and write its results to results/q3_*.csv.

Run: python scripts/query_places.py
"""

import csv
import sys
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hlds.cleaning import clean_trips
from hlds.loading import load_trips, load_zones
from hlds.paths import RESULTS_DIR
from hlds.places import add_zone_names, airport_trips, borough_flows, quarter_days, top_routes, zone_trips
from hlds.results import write_csv
from hlds.session import get_spark


def read_csv(name):
    with open(RESULTS_DIR / name, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main():
    spark = get_spark("q3-places")
    spark.sparkContext.setLogLevel("ERROR")
    trips = clean_trips(load_trips(spark))
    # Counted once here, so the queries below do not read the six months again only for the number of days.
    days = spark.createDataFrame(quarter_days(trips).collect())
    named = add_zone_names(trips, load_zones(spark))

    write_csv(zone_trips(named, days, "pickup"), RESULTS_DIR / "q3_pickup_zones.csv")
    write_csv(zone_trips(named, days, "dropoff"), RESULTS_DIR / "q3_dropoff_zones.csv")
    write_csv(borough_flows(named, days), RESULTS_DIR / "q3_borough_flows.csv")
    write_csv(top_routes(named, days), RESULTS_DIR / "q3_top_routes.csv")
    write_csv(airport_trips(named, days), RESULTS_DIR / "q3_airport_trips.csv")

    # Printed from the written files, because asking Spark again would read the six months again.
    for row in read_csv("q3_pickup_zones.csv"):
        if int(row["rank_in_year"]) <= 3:
            print(f"{row['year']} pickup #{row['rank_in_year']}: {row['zone']} ({row['borough']}), "
                  f"{row['trips_per_day']} per day")
    for row in read_csv("q3_top_routes.csv"):
        if row["rank_in_year"] == "1":
            print(f"{row['year']} busiest route: {row['pickup_zone']} -> {row['dropoff_zone']}, "
                  f"{row['trips_per_day']} per day")
    for row in read_csv("q3_airport_trips.csv"):
        print(f"{row['year']} {row['airport']} {row['direction']}: {row['trips_per_day']} per day")
    spark.stop()


if __name__ == "__main__":
    main()
