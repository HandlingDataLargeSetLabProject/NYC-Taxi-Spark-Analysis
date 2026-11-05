"""Cleaning steps for the trip table. Each step takes a DataFrame and returns a new one."""

from pyspark.sql import functions as F

CODE_COLUMNS = ["passenger_count", "RatecodeID", "payment_type"]
UNKNOWN_RATE_CODE = 99
CHARGE_START = "2025-01-05 00:00:00"


def add_missing_value_flags(trips):
    # passenger_count, RatecodeID, store_and_fwd_flag, congestion_surcharge and Airport_fee are
    # missing on exactly the same rows (all of them flex fare trips), so one column is enough to find them.
    details_missing = F.col("store_and_fwd_flag").isNull()
    # 2024 has no cbd_congestion_fee at all, and 1 to 4 January 2025 has it as 0, so the date decides.
    charge_in_force = F.col("tpep_pickup_datetime") >= F.lit(CHARGE_START).cast("timestamp_ntz")
    return trips.withColumn("details_missing", details_missing).withColumn("charge_in_force", charge_in_force)


def convert_types(trips):
    # The files store these small codes as long; int is enough and halves their size in memory.
    for column in CODE_COLUMNS:
        trips = trips.withColumn(column, F.col(column).cast("int"))
    flag = F.col("store_and_fwd_flag")
    return trips.withColumn("store_and_fwd_flag", F.when(flag == "Y", True).when(flag == "N", False))


def mark_unknown_values_as_missing(trips):
    # The rate code 99 means "unknown". We also read 0 passengers as a count that was not entered; this is our
    # decision, the field description only says that the driver reports the number.
    known_passengers = F.when(F.col("passenger_count") != 0, F.col("passenger_count"))
    known_rate_code = F.when(F.col("RatecodeID") != UNKNOWN_RATE_CODE, F.col("RatecodeID"))
    return trips.withColumn("passenger_count", known_passengers).withColumn("RatecodeID", known_rate_code)


def clean_missing_values_and_types(trips):
    # The flags are added first, while the missing values still come only from the raw files.
    return mark_unknown_values_as_missing(convert_types(add_missing_value_flags(trips)))
