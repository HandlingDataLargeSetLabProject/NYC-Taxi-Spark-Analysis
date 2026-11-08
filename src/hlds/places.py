"""Query Q3 (objective O3): where trips start and end, the busiest routes and the airport trips.

All rows of the cleaned table count, including `has_negative_part`, because they are real trips.
The years are compared by trips per day, because the first quarter has 91 days in 2024 and 90 in 2025.
"""

from pyspark.sql import Window
from pyspark.sql import functions as F

SIDES = {"pickup": "PULocationID", "dropoff": "DOLocationID"}
# 264 (Unknown) and 265 (Outside of NYC) hold placeholder text, not a place, so they are left out of the
# zone and route rankings. The borough flows keep them, so their share stays visible.
UNKNOWN_ZONES = [264, 265]
AIRPORT_ZONES = [1, 132, 138]  # Newark, JFK, LaGuardia
TOP_ROUTES = 20

TOP_ROUTES_SQL = """
WITH routes AS (
    SELECT year, PULocationID, pickup_borough, pickup_zone, DOLocationID, dropoff_borough, dropoff_zone,
           COUNT(*) AS trips
    FROM q3_trips
    WHERE PULocationID NOT IN ({unknown}) AND DOLocationID NOT IN ({unknown})
    GROUP BY year, PULocationID, pickup_borough, pickup_zone, DOLocationID, dropoff_borough, dropoff_zone
),
ranked AS (
    -- Zone ids break ties, so the order is the same on every run.
    SELECT *, ROW_NUMBER() OVER (PARTITION BY year ORDER BY trips DESC, PULocationID, DOLocationID) AS rank_in_year
    FROM routes
)
SELECT r.year, r.rank_in_year, r.PULocationID AS pickup_zone_id, r.pickup_borough, r.pickup_zone,
       r.DOLocationID AS dropoff_zone_id, r.dropoff_borough, r.dropoff_zone, r.trips,
       ROUND(r.trips / d.days, 1) AS trips_per_day
FROM ranked r
JOIN q3_days d ON r.year = d.year
WHERE r.rank_in_year <= {top}
ORDER BY r.year, r.rank_in_year
"""


def add_zone_names(trips, zones, broadcast_zones=False):
    """Join the zone table twice, for the pickup and the drop-off zone.

    With `broadcast_zones` the zone table is sent whole to every task (optimization O2); without it,
    Spark decides the join type itself.
    """
    named = trips.withColumn("year", F.year("tpep_pickup_datetime"))
    for side, id_column in SIDES.items():
        names = zones.select(F.col("LocationID").alias(id_column), F.col("Borough").alias(f"{side}_borough"),
                             F.col("Zone").alias(f"{side}_zone"))
        if broadcast_zones:
            names = F.broadcast(names)
        # A left join keeps a trip even if its zone id were missing from the table (none is in our six months).
        named = named.join(names, id_column, "left")
    return named


def quarter_days(trips):
    return (trips.groupBy(F.year("tpep_pickup_datetime").alias("year"))
            .agg(F.countDistinct(F.to_date("tpep_pickup_datetime")).alias("days")))


def per_day(counts, days):
    return (counts.join(days, "year")
            .withColumn("trips_per_day", F.round(F.col("trips") / F.col("days"), 1))
            .drop("days"))


def zone_trips(named, days, side):
    id_column = SIDES[side]
    counts = (named.filter(~F.col(id_column).isin(UNKNOWN_ZONES))
              .groupBy("year", F.col(id_column).alias("zone_id"), F.col(f"{side}_borough").alias("borough"),
                       F.col(f"{side}_zone").alias("zone"))
              .agg(F.count("*").alias("trips")))
    order = Window.partitionBy("year").orderBy(F.desc("trips"), "zone_id")
    return (per_day(counts, days)
            .withColumn("rank_in_year", F.row_number().over(order))
            .orderBy("year", "rank_in_year"))


def borough_flows(named, days):
    counts = named.groupBy("year", "pickup_borough", "dropoff_borough").agg(F.count("*").alias("trips"))
    share = F.col("trips") / F.sum("trips").over(Window.partitionBy("year"))
    return (per_day(counts, days)
            .withColumn("share", F.round(share, 4))
            .orderBy("year", F.desc("trips"), "pickup_borough", "dropoff_borough"))


def top_routes(named, days, top=TOP_ROUTES):
    named.createOrReplaceTempView("q3_trips")
    days.createOrReplaceTempView("q3_days")
    unknown = ", ".join(str(zone) for zone in UNKNOWN_ZONES)
    return named.sparkSession.sql(TOP_ROUTES_SQL.format(unknown=unknown, top=int(top)))


def airport_trips(named, days):
    # A trip from one airport to another counts once as "from" and once as "to".
    parts = []
    for side, id_column in SIDES.items():
        parts.append(named.filter(F.col(id_column).isin(AIRPORT_ZONES))
                     .groupBy("year", F.col(f"{side}_zone").alias("airport"))
                     .agg(F.count("*").alias("trips"))
                     .withColumn("direction", F.lit("from" if side == "pickup" else "to")))
    counts = parts[0].unionByName(parts[1])
    return (per_day(counts, days)
            .select("year", "airport", "direction", "trips", "trips_per_day")
            .orderBy("year", "airport", "direction"))
