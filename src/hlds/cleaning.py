"""Cleaning steps for the trip table. Each step takes a DataFrame and returns a new one."""

from functools import reduce
from operator import or_

from pyspark.sql import functions as F

CODE_COLUMNS = ["passenger_count", "RatecodeID", "payment_type"]
UNKNOWN_RATE_CODE = 99
CHARGE_START = "2025-01-05 00:00:00"
VALID_PERIODS = [("2024-01-01", "2024-04-01"), ("2025-01-01", "2025-04-01")]
MAX_TRIP_HOURS = 5
# 99.9% of the rows are under 30 miles, while the largest values reach 320,136 miles.
MAX_TRIP_MILES = 100
# After the other rules only two rows are above this (863,380 and 132,555 dollars); the next largest is 1,022.
MAX_TOTAL_AMOUNT = 2000
AMOUNT_COLUMNS = [
    "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge",
    "total_amount", "congestion_surcharge", "Airport_fee", "cbd_congestion_fee",
]


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


def invalid_row_rules():
    pickup = F.col("tpep_pickup_datetime")
    dropoff = F.col("tpep_dropoff_datetime")
    distance = F.col("trip_distance")
    in_period = reduce(or_, [
        (pickup >= F.lit(start).cast("timestamp_ntz")) & (pickup < F.lit(end).cast("timestamp_ntz"))
        for start, end in VALID_PERIODS
    ])
    return {
        "outside_period": ~in_period,
        "dropoff_before_pickup": dropoff < pickup,
        "zero_duration": dropoff == pickup,
        "over_time_limit": F.timestamp_diff("SECOND", pickup, dropoff) > MAX_TRIP_HOURS * 3600,
        "distance_zero_or_below": distance <= 0,
        "distance_over_limit": distance > MAX_TRIP_MILES,
        "negative_total": F.col("total_amount") < 0,
        "total_over_limit": F.col("total_amount") > MAX_TOTAL_AMOUNT,
    }


def drop_invalid_rows(trips):
    return trips.filter(~reduce(or_, invalid_row_rules().values()))


def add_negative_part_flag(trips):
    # On flex fare trips fare_amount can be negative while the total is positive. These are not refunds, so the
    # trips still count for demand, but price queries should leave them out. A missing amount is not a negative one.
    has_negative_part = reduce(or_, [F.coalesce(F.col(column) < 0, F.lit(False)) for column in AMOUNT_COLUMNS])
    return trips.withColumn("has_negative_part", has_negative_part)


def drop_duplicate_rows(trips):
    return trips.dropDuplicates()


def clean_trips(trips):
    valid_trips = drop_invalid_rows(clean_missing_values_and_types(trips))
    return drop_duplicate_rows(add_negative_part_flag(valid_trips))
