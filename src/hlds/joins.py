"""Optimization O2: the zone joins of Q3 and Q4 as a shuffle join (before) and as a broadcast join (after).

The zone table has 265 rows and the cleaned trip table about 20 million. In a shuffle join (sort merge join)
both sides are shuffled by zone id and sorted before they are matched. In a broadcast join each task gets the
whole zone table and matches its own trips locally, so the trips are not shuffled or sorted for the join.
"""

from contextlib import contextmanager

from pyspark.sql import functions as F

from hlds.places import add_zone_names

AUTO_BROADCAST = "spark.sql.autoBroadcastJoinThreshold"


@contextmanager
def automatic_broadcast_off(spark):
    """Stop Spark from turning small joins into broadcast joins by itself, then restore the old setting.

    With the threshold at -1 adaptive query execution cannot switch to a broadcast join while the query runs
    either, so a join without `broadcast()` stays a sort merge join.
    """
    old_value = spark.conf.get(AUTO_BROADCAST)
    spark.conf.set(AUTO_BROADCAST, "-1")
    try:
        yield
    finally:
        spark.conf.set(AUTO_BROADCAST, old_value)


def zone_pair_counts(trips, zones, broadcast_zones):
    """Join the zone table for both ends and count trips per year and zone pair, as the Q3 routes do.

    Returns the counted DataFrame after it has run, so its saved plan is the final one.
    """
    named = add_zone_names(trips, zones, broadcast_zones=broadcast_zones)
    counts = (named.groupBy("year", "pickup_borough", "pickup_zone", "dropoff_borough", "dropoff_zone")
              .agg(F.count("*").alias("trips")))
    counts.collect()
    return counts
