"""Query Q2 (objective O2): duration, speed, price per mile and tips by hour and payment type.

Trips with `has_negative_part` are left out, because their amounts do not show what the trip cost.
Flex fare trips stay a group of their own: their share grows strongly in 2025 and their tips are much lower.
"""

from pyspark.sql import Window
from pyspark.sql import functions as F

from hlds.places import add_zone_names, per_day, quarter_days

NEW_YORK = "America/New_York"
CREDIT_CARD = 1
# Cash tips are not recorded, so the tip percentage is only measured for card payments.
PAYMENT_GROUPS = {0: "flex fare", 1: "credit card", 2: "cash"}
OTHER_PAYMENTS = "other"
MEDIAN = 0.5


def new_york_to_utc(column):
    # The times are New York clock times. Read as UTC (our session zone) and shifted, so that trips
    # across the summer time change on 10 March 2024 and 9 March 2025 are not one hour too long.
    return F.to_utc_timestamp(F.col(column).cast("timestamp"), NEW_YORK)


def payment_group():
    group = F.lit(OTHER_PAYMENTS)
    for code, name in PAYMENT_GROUPS.items():
        group = F.when(F.col("payment_type") == code, name).otherwise(group)
    return group


def add_price_measures(trips):
    seconds = F.timestamp_diff("SECOND", new_york_to_utc("tpep_pickup_datetime"),
                               new_york_to_utc("tpep_dropoff_datetime"))
    total, tip = F.col("total_amount"), F.col("tip_amount")
    tip_pct = F.try_divide(tip, total - tip) * 100
    return (trips
            .filter(~F.col("has_negative_part"))
            .withColumn("year", F.year("tpep_pickup_datetime"))
            .withColumn("hour", F.hour("tpep_pickup_datetime"))
            .withColumn("payment", payment_group())
            .withColumn("duration_minutes", seconds / 60)
            .withColumn("speed_mph", F.try_divide(F.col("trip_distance"), seconds / 3600))
            .withColumn("price_per_mile", F.try_divide(total, F.col("trip_distance")))
            .withColumn("tip_pct", F.when(F.col("payment_type") == CREDIT_CARD, tip_pct)))


def pickup_borough_by_payment(trips, zones):
    """Trips per day by year, pickup borough and payment group, and each group's share of its borough.

    This is a demand count like Q1 and Q3, so the rows with `has_negative_part` stay in.
    """
    counts = (add_zone_names(trips, zones)
              .withColumn("payment", payment_group())
              .groupBy("year", "pickup_borough", "payment")
              .agg(F.count("*").alias("trips")))
    share = F.col("trips") / F.sum("trips").over(Window.partitionBy("year", "pickup_borough"))
    return (per_day(counts, quarter_days(trips))
            .withColumn("share_in_borough", F.round(share, 4))
            .orderBy("year", "pickup_borough", "payment"))


def price_summary(measures, group_columns):
    def mean(column):
        return F.round(F.avg(column), 2).alias(f"mean_{column}")

    def median(column):
        return F.round(F.percentile_approx(column, MEDIAN), 2).alias(f"median_{column}")

    return (measures.groupBy(*group_columns)
            .agg(F.count("*").alias("trips"),
                 median("duration_minutes"),
                 mean("speed_mph"), median("speed_mph"),
                 mean("price_per_mile"), median("price_per_mile"),
                 mean("tip_pct"), median("tip_pct"))
            .orderBy(*group_columns))
