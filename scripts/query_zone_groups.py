"""Group the pickup zones by their weekly demand profile with Spark MLlib KMeans (optional extension, Report 3).

Reads the cleaned table partitioned by pickup date (scripts/write_clean_tables.py), so the raw files are not
cleaned again, and writes results/ml_zone_silhouette.csv, ml_zone_groups.csv and ml_group_profiles.csv.
Run: python scripts/query_zone_groups.py
"""

import sys
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyspark.sql import functions as F  # noqa: E402

from hlds.demand import add_pickup_parts  # noqa: E402
from hlds.loading import load_zones  # noqa: E402
from hlds.paths import RESULTS_DIR  # noqa: E402
from hlds.results import write_csv  # noqa: E402
from hlds.session import get_spark  # noqa: E402
from hlds.storage import PARTITIONED_TABLE, read_table  # noqa: E402
from hlds.zone_groups import (  # noqa: E402
    PROFILE_YEAR,
    add_features,
    assign_groups,
    best_k,
    group_profiles,
    silhouette_by_k,
    zone_profiles,
)


def main():
    spark = get_spark("ml-zone-groups")
    spark.sparkContext.setLogLevel("ERROR")
    trips = add_pickup_parts(read_table(spark, PARTITIONED_TABLE).select("tpep_pickup_datetime", "PULocationID"))

    profiles = zone_profiles(trips).cache()
    features = add_features(profiles).cache()
    print(f"{features.count()} pickup zones with at least 10 trips per day in {PROFILE_YEAR}")

    results = silhouette_by_k(features)
    for k, silhouette, _ in results:
        print(f"k={k}: silhouette {silhouette:.4f}")
    k, silhouette, model = best_k(results)
    print(f"chosen k={k} (silhouette {silhouette:.4f})")
    write_csv(spark.createDataFrame([(k_value, round(score, 4)) for k_value, score, _ in results],
                                    "k int, silhouette double"),
              RESULTS_DIR / "ml_zone_silhouette.csv")

    groups = assign_groups(features, model).cache()
    days = trips.groupBy("year").agg(F.countDistinct("pickup_date").alias("days"))
    per_year = (trips.groupBy("PULocationID", "year").agg(F.count("*").alias("trips"))
                .join(F.broadcast(days), "year")
                .withColumn("trips_per_day", F.round(F.col("trips") / F.col("days"), 1))
                .groupBy("PULocationID").pivot("year", [2024, 2025]).agg(F.first("trips_per_day")))
    zones = load_zones(spark)
    named = (groups.select("PULocationID", "group")
             .join(per_year, "PULocationID", "left")
             .join(F.broadcast(zones), F.col("PULocationID") == F.col("LocationID"))
             .select(F.col("PULocationID").alias("zone_id"), F.col("Borough").alias("borough"),
                     F.col("Zone").alias("zone"), "group",
                     F.coalesce(F.col("2024"), F.lit(0.0)).alias("trips_per_day_2024"),
                     F.col("2025").alias("trips_per_day_2025"))
             .orderBy("group", F.desc("trips_per_day_2025")))
    write_csv(named, RESULTS_DIR / "ml_zone_groups.csv")
    profile_rows = group_profiles(profiles, groups).withColumn("share", F.round("share", 6))
    write_csv(profile_rows, RESULTS_DIR / "ml_group_profiles.csv")

    summary = (named.groupBy("group")
               .agg(F.count("*").alias("zones"), F.sum("trips_per_day_2024").alias("y2024"),
                    F.sum("trips_per_day_2025").alias("y2025"),
                    F.concat_ws(", ", F.slice(F.collect_list("zone"), 1, 4)).alias("examples"))
               .orderBy("group").collect())
    for row in summary:
        print(f"group {row['group']}: {row['zones']} zones, {row['y2024']:,.0f} -> {row['y2025']:,.0f} per day; "
              f"{row['examples']}")
    spark.stop()


if __name__ == "__main__":
    main()
