"""Print the numbers behind the "Cleaned table" part of docs/data-dictionary.md."""

import sys
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyspark.sql import functions as F

from hlds.cleaning import (
    add_negative_part_flag,
    clean_missing_values_and_types,
    drop_duplicate_rows,
    drop_invalid_rows,
    invalid_row_rules,
)
from hlds.loading import load_trips
from hlds.session import get_spark


def count_if(condition):
    return F.sum(condition.cast("long"))


def print_invalid_rows(trips):
    print("Rows matching each rule, per file year and flex fare (details_missing)")
    rules = invalid_row_rules()
    any_rule = F.lit(False)
    for condition in rules.values():
        any_rule = any_rule | condition
    counts = [count_if(condition).alias(name) for name, condition in rules.items()]
    year = F.regexp_extract(F.col("_metadata.file_name"), r"(\d{4})-\d{2}", 1).alias("year")
    totals = trips.groupBy(year, "details_missing").agg(
        F.count("*").alias("rows"), *counts, count_if(any_rule).alias("any_rule")
    )
    for row in totals.orderBy("year", "details_missing").collect():
        print(f"  {row.asDict()}")


def print_rows_after_cleaning(valid_rows):
    print("Rows after dropping invalid rows and after dropping duplicates, per pickup year and flex fare")
    year = F.year("tpep_pickup_datetime").alias("year")
    before = {(row["year"], row["details_missing"]): row["count"]
              for row in valid_rows.groupBy(year, "details_missing").count().collect()}
    after = drop_duplicate_rows(valid_rows).groupBy(year, "details_missing").count().collect()
    for row in sorted(after, key=lambda row: (row["year"], row["details_missing"])):
        key = (row["year"], row["details_missing"])
        print(f"  {key}: valid {before[key]:,}, without duplicates {row['count']:,}, duplicates {before[key] - row['count']:,}")


def print_negative_part_flag(valid_rows):
    print("Valid rows with has_negative_part, per pickup year and flex fare")
    year = F.year("tpep_pickup_datetime").alias("year")
    flagged = add_negative_part_flag(valid_rows).filter("has_negative_part").groupBy(year, "details_missing").agg(
        F.count("*").alias("rows"),
        count_if(F.col("fare_amount") < 0).alias("negative_fare"),
        F.round(F.sum("total_amount"), 2).alias("total_amount"),
    )
    for row in flagged.orderBy("year", "details_missing").collect():
        print(f"  {row.asDict()}")


def print_reversed_trips(trips, valid_rows):
    # A reversal has the same vendor, pickup and drop-off time and zones as a kept trip, and the opposite total_amount.
    print("Kept trips with a reversal among the dropped negative totals, per pickup year")
    keys = ["VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", "DOLocationID", "matched_total"]
    reversals = trips.filter(F.col("total_amount") < 0).withColumn("matched_total", -F.col("total_amount")).select(keys)
    matched = valid_rows.withColumn("matched_total", F.col("total_amount")).join(reversals, keys, "left_semi")
    year = F.year("tpep_pickup_datetime").alias("year")
    totals = valid_rows.groupBy(year).agg(F.count("*").alias("rows"), F.sum("total_amount").alias("amount")).collect()
    totals = {row["year"]: row for row in totals}
    counts = matched.groupBy(year, "details_missing").agg(F.count("*").alias("rows"), F.sum("total_amount").alias("amount"))
    for row in counts.orderBy("year", "details_missing").collect():
        total = totals[row["year"]]
        print(f"  {row['year']}, flex fare {row['details_missing']}: {row['rows']:,} rows ({row['rows'] / total['rows']:.2%}), "
              f"{row['amount']:,.2f} of total_amount ({row['amount'] / total['amount']:.2%})")


def main():
    spark = get_spark("profile-cleaning")
    spark.sparkContext.setLogLevel("ERROR")
    trips = clean_missing_values_and_types(load_trips(spark))
    print_invalid_rows(trips)
    valid_rows = drop_invalid_rows(trips)
    print_rows_after_cleaning(valid_rows)
    print_negative_part_flag(valid_rows)
    print_reversed_trips(trips, valid_rows)
    spark.stop()


if __name__ == "__main__":
    main()
