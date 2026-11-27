"""Optional extension of Report 3: group the pickup zones by their weekly demand profile with Spark MLlib.

Each zone gets a profile of 168 numbers, one for every hour of the week (Monday 00:00 to Sunday 23:00): the trips
per day that start in the zone in that hour, divided by the zone's whole week. So the profile describes when a
zone is busy, not how busy it is, and KMeans groups zones with the same rhythm, not zones of the same size.
The profiles come from one year, 2025 by default, and the number of groups k is chosen by the silhouette score.
"""

from functools import reduce
from operator import add

from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import functions as F

PROFILE_YEAR = 2025
# A zone with fewer trips has a noisy profile: at 10 trips per day most of the 168 hours hold less than one trip.
MIN_TRIPS_PER_DAY = 10
# 264 and 265 are "Unknown" and "Outside of NYC", not places.
NOT_PLACES = (264, 265)
K_VALUES = range(2, 9)
SEED = 42
SLOT_COLUMNS = [f"slot_{weekday}_{hour:02d}" for weekday in range(7) for hour in range(24)]


def _slot_name(weekday, hour):
    return F.format_string("slot_%d_%02d", weekday, hour)


def zone_profiles(trips, year=PROFILE_YEAR, min_trips_per_day=MIN_TRIPS_PER_DAY):
    """One row per pickup zone with its trips per day and its 168 hourly shares of the week.

    `trips` needs the columns of hlds.demand.add_pickup_parts and `PULocationID`. A weekday counts every one of
    its days, also those without a trip in the zone, as in Q1. Zones below `min_trips_per_day` are left out.
    """
    in_year = trips.filter((F.col("year") == year) & ~F.col("PULocationID").isin(*NOT_PLACES))
    days_by_weekday = in_year.groupBy("weekday").agg(F.countDistinct("pickup_date").alias("days"))
    days_in_year = in_year.agg(F.countDistinct("pickup_date").alias("year_days"))
    slots = (in_year.groupBy("PULocationID", "weekday", "hour").agg(F.count("*").alias("trips"))
             .join(F.broadcast(days_by_weekday), "weekday")
             .withColumn("per_day", F.col("trips") / F.col("days"))
             .withColumn("slot", _slot_name(F.col("weekday"), F.col("hour"))))
    wide = slots.groupBy("PULocationID").pivot("slot", SLOT_COLUMNS).agg(F.first("per_day")).fillna(0.0)
    totals = (slots.groupBy("PULocationID").agg(F.sum("trips").alias("trips"))
              .crossJoin(F.broadcast(days_in_year))
              .withColumn("trips_per_day", F.col("trips") / F.col("year_days"))
              .select("PULocationID", "trips_per_day"))
    week = reduce(add, [F.col(name) for name in SLOT_COLUMNS])
    shares = [(F.col(name) / F.col("week")).alias(name) for name in SLOT_COLUMNS]
    return (wide.join(totals, "PULocationID")
            .filter(F.col("trips_per_day") >= min_trips_per_day)
            .withColumn("week", week)
            .select("PULocationID", "trips_per_day", *shares))


def add_features(profiles):
    return VectorAssembler(inputCols=SLOT_COLUMNS, outputCol="features").transform(profiles)


def silhouette_by_k(features, k_values=K_VALUES, seed=SEED):
    """Fit KMeans for every k and return [(k, silhouette, model)]; a higher silhouette means clearer groups."""
    evaluator = ClusteringEvaluator(featuresCol="features", predictionCol="prediction")
    results = []
    for k in k_values:
        model = KMeans(k=k, seed=seed, featuresCol="features", predictionCol="prediction").fit(features)
        results.append((k, evaluator.evaluate(model.transform(features)), model))
    return results


def best_k(results):
    """The k with the highest silhouette; on a tie the smaller k, because fewer groups are easier to read."""
    return max(results, key=lambda result: (round(result[1], 6), -result[0]))


def assign_groups(features, model):
    """Zone, raw cluster id and trips per day, with the groups numbered from 1 by their trips (busiest first).

    KMeans numbers its clusters in no particular order; numbering them by size keeps the names stable between runs.
    """
    predicted = model.transform(features).select("PULocationID", "trips_per_day", "prediction")
    order = (predicted.groupBy("prediction").agg(F.sum("trips_per_day").alias("group_trips"))
             .orderBy(F.desc("group_trips")).collect())
    numbers = {row["prediction"]: number for number, row in enumerate(order, start=1)}
    mapping = F.create_map(*[item for pair in numbers.items() for item in (F.lit(pair[0]), F.lit(pair[1]))])
    return predicted.withColumn("group", mapping[F.col("prediction")]).drop("prediction")


def group_profiles(profiles, groups):
    """Mean hourly share of the week for each group, in long form: group, weekday, hour, share."""
    joined = profiles.join(groups.select("PULocationID", "group"), "PULocationID")
    means = joined.groupBy("group").agg(*[F.avg(name).alias(name) for name in SLOT_COLUMNS])
    stack = ", ".join(f"{weekday}, {hour}, `{SLOT_COLUMNS[weekday * 24 + hour]}`"
                      for weekday in range(7) for hour in range(24))
    return (means.selectExpr("group", f"stack({len(SLOT_COLUMNS)}, {stack}) AS (weekday, hour, share)")
            .orderBy("group", "weekday", "hour"))
