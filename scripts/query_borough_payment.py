"""Count trips by year, pickup borough and payment group on the six months; writes results/q2_borough_payment.csv.

It links the flex fare growth of Q2 with the places of Q3 and Q4 (Report 2, Section 11).
Run: python scripts/query_borough_payment.py
"""

import sys
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hlds.cleaning import clean_trips
from hlds.loading import load_trips, load_zones
from hlds.paths import RESULTS_DIR
from hlds.prices import pickup_borough_by_payment
from hlds.results import write_csv
from hlds.session import get_spark


def main():
    spark = get_spark("q2-borough-payment")
    spark.sparkContext.setLogLevel("ERROR")
    counts = pickup_borough_by_payment(clean_trips(load_trips(spark)), load_zones(spark))
    write_csv(counts, RESULTS_DIR / "q2_borough_payment.csv")

    for row in counts.collect():
        print(f"{row['year']} {row['pickup_borough']:<14} {row['payment']:<12} {row['trips_per_day']:>10,} per day, "
              f"{row['share_in_borough']:.2%} of the borough")
    spark.stop()


if __name__ == "__main__":
    main()
