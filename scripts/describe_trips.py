"""Write the summary tables of the cleaned trip table to results/descriptive_statistics.md."""

import sys
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyspark.sql import functions as F

from hlds.cleaning import clean_trips
from hlds.loading import load_trips, load_zones
from hlds.paths import PROJECT_ROOT
from hlds.session import get_spark
from hlds.statistics import GENERAL_COLUMNS, PRICE_COLUMNS, add_year_and_duration, category_shares, numeric_summary

OUTPUT_FILE = PROJECT_ROOT / "results" / "descriptive_statistics.md"
PAYMENT_TYPES = {0: "flex fare", 1: "credit card", 2: "cash", 3: "no charge", 4: "dispute"}
RATE_CODES = {1: "standard", 2: "JFK", 3: "Newark", 4: "Nassau or Westchester", 5: "negotiated fare", 6: "group ride"}
STATISTICS = ["rows", "missing", "mean", "stddev", "min", "p25", "median", "p75", "p99", "max"]
AMOUNT_PARTS = ["fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge",
                "congestion_surcharge", "Airport_fee", "cbd_congestion_fee"]


def number(value):
    if value is None:
        return "-"
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:,.2f}"


def markdown_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return lines


def overview_table(trips):
    totals = trips.groupBy("year").agg(
        F.count("*").alias("rows"),
        F.countDistinct(F.to_date("tpep_pickup_datetime")).alias("days"),
        F.sum(F.col("details_missing").cast("long")).alias("flex_fare"),
        F.sum(F.col("has_negative_part").cast("long")).alias("flagged"),
    ).orderBy("year").collect()
    rows = [[str(row["year"]), number(row["rows"]), str(row["days"]), number(round(row["rows"] / row["days"])),
             f"{row['flex_fare'] / row['rows']:.2%}", f"{row['flagged'] / row['rows']:.2%}"] for row in totals]
    return markdown_table(["Year", "Trips", "Days", "Trips per day", "Flex fare", "`has_negative_part`"], rows)


def summary_table(trips, group_columns):
    headers = ["Column"] + [name.replace("details_missing", "Flex fare").capitalize() for name in group_columns] + STATISTICS
    column_order = GENERAL_COLUMNS + PRICE_COLUMNS
    entries = sorted(numeric_summary(trips, group_columns), key=lambda entry: column_order.index(entry["column"]))
    rows = [[f"`{entry['column']}`"] + [str(entry[name]) for name in group_columns]
            + [number(entry[name]) for name in STATISTICS] for entry in entries]
    return markdown_table(headers, rows)


def shares_table(trips, column, labels):
    rows = []
    for entry in category_shares(trips, column):
        name = labels.get(entry["value"], entry["value"]) if labels else entry["value"]
        rows.append([str(entry["year"]), "missing" if name is None else str(name), number(entry["rows"]), f"{entry['share']:.2%}"])
    return markdown_table(["Year", column, "Trips", "Share"], rows)


def zone_charge_table(trips):
    in_force = trips.filter("charge_in_force")
    totals = in_force.agg(
        F.count("*").alias("rows"),
        F.sum((F.col("cbd_congestion_fee") > 0).cast("long")).alias("paying"),
    ).first()
    rows = [[number(totals["rows"]), number(totals["paying"]), f"{totals['paying'] / totals['rows']:.2%}"]]
    return markdown_table(["Trips from 5 January 2025", "With `cbd_congestion_fee` above 0", "Share"], rows)


def total_versus_parts_table(trips):
    parts = sum(F.coalesce(F.col(column), F.lit(0.0)) for column in AMOUNT_PARTS)
    difference = F.round(F.col("total_amount") - parts, 2)
    totals = trips.groupBy("year", "VendorID", "details_missing").agg(
        F.count("*").alias("rows"),
        F.sum((F.abs(difference) > 0.01).cast("long")).alias("differs"),
        F.sum((difference == 2.5).cast("long")).alias("plus_2_50"),
        F.sum((difference == -2.5).cast("long")).alias("minus_2_50"),
        F.sum((difference == -3.25).cast("long")).alias("minus_3_25"),
    ).orderBy("year", "VendorID", "details_missing").collect()
    rows = [[str(row["year"]), str(row["VendorID"]), str(row["details_missing"]), number(row["rows"]),
             *[f"{row[name] / row['rows']:.2%}" for name in ["differs", "plus_2_50", "minus_2_50", "minus_3_25"]]]
            for row in totals]
    return markdown_table(["Year", "VendorID", "Flex fare", "Rows", "Differs", "+2.50", "-2.50", "-3.25"], rows)


def main():
    spark = get_spark("describe-trips")
    spark.sparkContext.setLogLevel("ERROR")
    trips = add_year_and_duration(clean_trips(load_trips(spark)))
    zones = load_zones(spark).select(F.col("LocationID").alias("PULocationID"), F.col("Borough").alias("pickup_borough"))

    lines = ["# Descriptive statistics", "",
             "Written by `scripts/describe_trips.py` from the output of `clean_trips`. Percentiles are approximate "
             "(`percentile_approx`). Price columns leave out the `has_negative_part` rows. Amounts are in US dollars, "
             "distance in miles. 2024 has no `cbd_congestion_fee`.", "",
             "## Overview", ""]
    lines += overview_table(trips)
    lines += ["", "## Numeric columns per year", ""]
    lines += summary_table(trips, ["year"])
    lines += ["", "## Numeric columns per year and flex fare", ""]
    lines += summary_table(trips, ["year", "details_missing"])
    lines += ["", "## Payment type", ""]
    lines += shares_table(trips, "payment_type", PAYMENT_TYPES)
    lines += ["", "## Rate code", ""]
    lines += shares_table(trips, "RatecodeID", RATE_CODES)
    lines += ["", "## Pickup borough", ""]
    lines += shares_table(trips.join(F.broadcast(zones), "PULocationID"), "pickup_borough", None)
    lines += ["", "## Zone charge", ""]
    lines += zone_charge_table(trips)
    lines += ["", "## `total_amount` minus the sum of its parts", "",
              "Share of the rows where `total_amount` differs from the sum of the amount columns, and the most common "
              "differences. A missing part counts as 0. We have not confirmed the cause with the data publisher, so "
              "the price queries use `total_amount` and do not rebuild it from the parts.", ""]
    lines += total_versus_parts_table(trips)

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT_FILE}")
    spark.stop()


if __name__ == "__main__":
    main()
