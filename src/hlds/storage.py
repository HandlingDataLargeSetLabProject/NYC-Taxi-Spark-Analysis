"""Optimization O3: the cleaned table stored as plain Parquet (before) and partitioned by pickup date (after).

Both copies hold the same rows and columns. A query that filters on the pickup date has to open every file of
the plain copy, because each file holds trips from all days. In the partitioned copy every day has its own
folder, so Spark only lists and reads the folders of the days the filter keeps (partition pruning).
"""

from pyspark.sql import functions as F

from hlds.paths import DATA_DIR

# Kept under data/, so the copies are never committed.
DERIVED_DIR = DATA_DIR / "derived"
PLAIN_TABLE = DERIVED_DIR / "clean_plain"
PARTITIONED_TABLE = DERIVED_DIR / "clean_by_pickup_date"
PARTITION_COLUMN = "pickup_date"
# March 2025 is one of the six months, so the filter keeps about a sixth of the trips.
FILTER_START = "2025-03-01"
FILTER_END = "2025-03-31"
MEDIAN = 0.5


def add_pickup_date(trips):
    # The pickup times are New York clock times, so the date needs no time zone conversion.
    return trips.withColumn(PARTITION_COLUMN, F.to_date("tpep_pickup_datetime"))


def write_plain(trips, path):
    add_pickup_date(trips).write.mode("overwrite").parquet(str(path))


def write_partitioned(trips, path):
    # Without the repartition every task would write its own small file into every day folder.
    dated = add_pickup_date(trips).repartition(PARTITION_COLUMN)
    dated.write.mode("overwrite").partitionBy(PARTITION_COLUMN).parquet(str(path))


def read_table(spark, path):
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing, run scripts/write_clean_tables.py first")
    return spark.read.parquet(str(path))


def daily_summary(trips, start=FILTER_START, end=FILTER_END):
    """Trips and median total per day between `start` and `end`, collected; returns the DataFrame that ran."""
    day = F.col(PARTITION_COLUMN)
    summary = (trips.filter((day >= F.lit(start).cast("date")) & (day <= F.lit(end).cast("date")))
               .groupBy(PARTITION_COLUMN)
               .agg(F.count("*").alias("trips"),
                    F.round(F.percentile_approx("total_amount", MEDIAN), 2).alias("median_total_amount"))
               .orderBy(PARTITION_COLUMN))
    summary.collect()
    return summary
