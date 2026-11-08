"""Run query Q2 on the six months and write its results to results/q2_*.csv.

Run: python scripts/query_prices.py
"""

import sys
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hlds.cleaning import clean_trips
from hlds.loading import load_trips
from hlds.paths import RESULTS_DIR
from hlds.prices import add_price_measures, price_summary
from hlds.results import write_csv
from hlds.session import get_spark


def main():
    spark = get_spark("q2-prices")
    spark.sparkContext.setLogLevel("ERROR")
    measures = add_price_measures(clean_trips(load_trips(spark)))

    by_payment = price_summary(measures, ["year", "payment"])
    write_csv(by_payment, RESULTS_DIR / "q2_by_payment.csv")
    write_csv(price_summary(measures, ["year", "hour", "payment"]), RESULTS_DIR / "q2_by_hour_payment.csv")

    for row in by_payment.collect():
        print(f"{row['year']} {row['payment']:<12} {row['trips']:>10,} trips, median {row['median_speed_mph']} mph, "
              f"{row['median_price_per_mile']} $/mile, tip {row['median_tip_pct']}%")
    spark.stop()


if __name__ == "__main__":
    main()
