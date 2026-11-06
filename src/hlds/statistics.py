"""Descriptive statistics for the cleaned trip table."""

from pyspark.sql import functions as F

GENERAL_COLUMNS = ["trip_distance", "duration_minutes", "passenger_count"]
PRICE_COLUMNS = [
    "fare_amount", "tip_amount", "tolls_amount", "total_amount", "congestion_surcharge", "Airport_fee",
    "cbd_congestion_fee",
]
PERCENTILES = {"p25": 0.25, "median": 0.5, "p75": 0.75, "p99": 0.99}


def add_year_and_duration(trips):
    pickup = F.col("tpep_pickup_datetime")
    seconds = F.timestamp_diff("SECOND", pickup, F.col("tpep_dropoff_datetime"))
    return trips.withColumn("year", F.year(pickup)).withColumn("duration_minutes", seconds / 60)


def column_statistics(column, include):
    value = F.when(include, F.col(column))
    percentiles = F.percentile_approx(value, list(PERCENTILES.values())).alias(f"{column}|percentiles")
    return [
        F.count(value).alias(f"{column}|rows"),
        F.sum((include & F.col(column).isNull()).cast("long")).alias(f"{column}|missing"),
        F.avg(value).alias(f"{column}|mean"),
        F.stddev(value).alias(f"{column}|stddev"),
        F.min(value).alias(f"{column}|min"),
        F.max(value).alias(f"{column}|max"),
        percentiles,
    ]


def numeric_summary(trips, group_columns):
    # The amounts of the has_negative_part rows are not reliable, so they only count for the general columns.
    aggregates = []
    for column in GENERAL_COLUMNS:
        aggregates += column_statistics(column, F.lit(True))
    for column in PRICE_COLUMNS:
        aggregates += column_statistics(column, ~F.col("has_negative_part"))
    totals = trips.groupBy(*group_columns).agg(*aggregates).orderBy(*group_columns).collect()

    summary = []
    for row in totals:
        for column in GENERAL_COLUMNS + PRICE_COLUMNS:
            entry = {name: row[name] for name in group_columns}
            entry["column"] = column
            for name in ["rows", "missing", "mean", "stddev", "min", "max"]:
                entry[name] = row[f"{column}|{name}"]
            percentiles = row[f"{column}|percentiles"] or [None] * len(PERCENTILES)
            entry.update(zip(PERCENTILES, percentiles))
            summary.append(entry)
    return summary


def category_shares(trips, column):
    counts = trips.groupBy("year", column).count().orderBy("year", column).collect()
    totals = {}
    for row in counts:
        totals[row["year"]] = totals.get(row["year"], 0) + row["count"]
    return [
        {"year": row["year"], "value": row[column], "rows": row["count"], "share": row["count"] / totals[row["year"]]}
        for row in counts
    ]
