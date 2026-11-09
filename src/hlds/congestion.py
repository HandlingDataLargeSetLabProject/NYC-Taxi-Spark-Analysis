"""Query Q4 (objective O4): the congestion relief zone charge, before (2024) and after (2025) it started.

Both years are compared from 5 January to 31 March, because the charge started on 5 January 2025, and by
trips per day, because these dates have 87 days in 2024 and 86 in 2025. Trips with `has_negative_part` are
left out, because their amounts do not show what the trip cost. Prices are compared by medians, because the
means are pulled up by a few very expensive trips.
"""

from pyspark.sql import Window
from pyspark.sql import functions as F

from hlds.places import SIDES, UNKNOWN_ZONES, per_day

CHARGE_START_DAY = 5  # 5 January is day 5 of the year in both years
MEDIAN = 0.5
ALL_TRIPS = "all trips"
PAYS = "pays the charge"
DOES_NOT_PAY = "does not pay"


def charge_window(trips):
    pickup = F.col("tpep_pickup_datetime")
    return (trips
            .filter(~F.col("has_negative_part"))
            .filter(F.dayofyear(pickup) >= CHARGE_START_DAY)
            .withColumn("year", F.year(pickup))
            .withColumn("hour", F.hour(pickup))
            # The 2024 files have no charge column, so a missing value means "does not pay", never 0 dollars paid.
            .withColumn("pays_charge", F.coalesce(F.col("cbd_congestion_fee") > 0, F.lit(False))))


def charge_summary(trips, days, group_columns):
    """Trips, trips per day and median price for all trips, and in the charge period also split by who pays.

    `share` is the part of all trips of the same year and group that falls in the row's charge group.
    """
    def summarise(frame, charge_group):
        return (frame.groupBy("year", *group_columns)
                .agg(F.count("*").alias("trips"),
                     F.round(F.percentile_approx("total_amount", MEDIAN), 2).alias("median_total_amount"),
                     F.round(F.percentile_approx("trip_distance", MEDIAN), 2).alias("median_trip_distance"))
                .withColumn("charge_group", F.lit(charge_group)))

    charged = trips.filter("charge_in_force")
    counts = (summarise(trips, ALL_TRIPS)
              .unionByName(summarise(charged.filter("pays_charge"), PAYS))
              .unionByName(summarise(charged.filter(~F.col("pays_charge")), DOES_NOT_PAY)))
    all_trips = F.max(F.when(F.col("charge_group") == ALL_TRIPS, F.col("trips")))
    share = F.col("trips") / all_trips.over(Window.partitionBy("year", *group_columns))
    columns = ["year", *group_columns, "charge_group", "trips", "trips_per_day", "share", "median_total_amount",
               "median_trip_distance"]
    return (per_day(counts, days)
            .withColumn("share", F.round(share, 4))
            .select(*columns)
            .orderBy("year", *group_columns, "charge_group"))


def zone_charge_summary(named, days, side):
    # Zones 264 and 265 are placeholders, as in Q3.
    id_column = SIDES[side]
    zones = (named.filter(~F.col(id_column).isin(UNKNOWN_ZONES))
             .withColumn("zone_id", F.col(id_column))
             .withColumn("borough", F.col(f"{side}_borough"))
             .withColumn("zone", F.col(f"{side}_zone")))
    return charge_summary(zones, days, ["zone_id", "borough", "zone"])
