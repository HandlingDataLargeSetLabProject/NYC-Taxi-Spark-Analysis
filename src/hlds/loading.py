"""Load the raw trip files and the zone lookup table into Spark."""

from pyspark.sql import functions as F

from hlds.paths import ZONE_LOOKUP_FILE, trip_files

ZONE_COLUMNS = ["LocationID", "Borough", "Zone", "service_zone"]


def load_trips(spark, files=None):
    paths = [str(path) for path in (files or trip_files())]
    # The 2024 files have no cbd_congestion_fee. Merging keeps the column, null for 2024, and fails if a type differs.
    return spark.read.option("mergeSchema", "true").parquet(*paths)


def load_zones(spark, path=ZONE_LOOKUP_FILE):
    zones = spark.read.option("header", "true").csv(str(path))
    if zones.columns != ZONE_COLUMNS:
        raise ValueError(f"unexpected zone columns: {zones.columns}")
    return zones.withColumn("LocationID", F.col("LocationID").cast("int"))
