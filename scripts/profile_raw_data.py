"""Print the numbers behind docs/data-dictionary.md: row counts, types and missing values."""

import sys
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyspark.sql import functions as F

from hlds.loading import load_trips, load_zones
from hlds.session import get_spark


SPARSE_COLUMNS = ["passenger_count", "RatecodeID", "store_and_fwd_flag", "congestion_surcharge", "Airport_fee"]


def year_of_file():
    return F.regexp_extract(F.col("_metadata.file_name"), r"(\d{4})-\d{2}", 1).alias("year")


def print_rows_per_file(trips):
    print("Rows per file")
    file_name = F.col("_metadata.file_name").alias("file")
    for row in trips.groupBy(file_name).count().orderBy("file").collect():
        print(f"  {row['file']}: {row['count']:,}")
    print(f"  all files: {trips.count():,}")


def print_columns(trips):
    print("Columns per year: type, missing values")
    missing = [F.sum(F.col(name).isNull().cast("long")).alias(name) for name in trips.columns]
    totals = trips.groupBy(year_of_file()).agg(F.count("*").alias("rows"), *missing).orderBy("year").collect()
    for field in trips.schema.fields:
        counts = [f"{row['year']}: {row[field.name]:,} ({row[field.name] / row['rows']:.2%})" for row in totals]
        print(f"  {field.name}: {field.dataType.typeName()}, {', '.join(counts)}")


def print_columns_missing_together(trips):
    print(f"Rows per year where all of {SPARSE_COLUMNS} are missing, and where any of them is")
    missing = [F.col(name).isNull().cast("int") for name in SPARSE_COLUMNS]
    totals = trips.groupBy(year_of_file()).agg(
        F.sum((F.least(*missing) == 1).cast("long")).alias("all_missing"),
        F.sum((F.greatest(*missing) == 1).cast("long")).alias("any_missing"),
    )
    for row in totals.orderBy("year").collect():
        print(f"  {row['year']}: all {row['all_missing']:,}, any {row['any_missing']:,}")


def print_zones(zones, trips):
    print("Zone lookup table")
    print(f"  rows: {zones.count():,}, distinct LocationID: {zones.select('LocationID').distinct().count():,}")
    print(f"  types: {[(field.name, field.dataType.typeName()) for field in zones.schema.fields]}")
    missing = zones.select([F.sum(F.col(name).isNull().cast("long")).alias(name) for name in zones.columns]).first()
    print(f"  missing values: {missing.asDict()}")
    print("  rows with the text N/A or Unknown:")
    placeholder = F.col("Borough").isin("N/A", "Unknown") | F.col("Zone").isin("N/A", "Unknown")
    for row in zones.filter(placeholder).orderBy("LocationID").collect():
        print(f"    {row.asDict()}")
    for column in ["PULocationID", "DOLocationID"]:
        unmatched = trips.join(zones, trips[column] == zones["LocationID"], "left_anti").count()
        print(f"  trips whose {column} is not in the table: {unmatched:,}")


def main():
    spark = get_spark("profile-raw-data")
    spark.sparkContext.setLogLevel("ERROR")
    trips = load_trips(spark)
    zones = load_zones(spark)
    print_rows_per_file(trips)
    print_columns(trips)
    print_columns_missing_together(trips)
    print_zones(zones, trips)
    spark.stop()


if __name__ == "__main__":
    main()
