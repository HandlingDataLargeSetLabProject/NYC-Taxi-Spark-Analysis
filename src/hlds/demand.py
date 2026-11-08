"""Query Q1 (objective O1): when people take taxis and how daily demand moves, 2024 against 2025.

All rows of the cleaned table count, including `has_negative_part`, because they are real trips.
The years are compared by trips per day, because the first quarter has 91 days in 2024 and 90 in 2025.
"""

from pyspark.sql import functions as F

HOUR_WEEKDAY_SQL = """
WITH slots AS (
    SELECT year, weekday, hour, COUNT(*) AS trips
    FROM q1_trips
    GROUP BY year, weekday, hour
),
weekdays AS (
    -- Every day of a weekday counts, also one without a trip in a given hour.
    SELECT year, weekday, COUNT(DISTINCT pickup_date) AS days
    FROM q1_trips
    GROUP BY year, weekday
)
SELECT s.year, s.weekday, s.hour, s.trips, w.days, ROUND(s.trips / w.days, 2) AS trips_per_day
FROM slots s
JOIN weekdays w ON s.year = w.year AND s.weekday = w.weekday
ORDER BY s.year, s.weekday, s.hour
"""


def add_pickup_parts(trips):
    # The pickup times are New York clock times without a zone, so hour and date need no conversion.
    pickup = F.col("tpep_pickup_datetime")
    return (trips
            .withColumn("year", F.year(pickup))
            .withColumn("pickup_date", F.to_date(pickup))
            .withColumn("hour", F.hour(pickup))
            .withColumn("weekday", F.weekday(pickup)))  # 0 is Monday, 6 is Sunday


def daily_trips(trips):
    return trips.groupBy("year", "pickup_date").agg(F.count("*").alias("trips")).orderBy("pickup_date")


def daily_average_by_year(daily):
    return (daily.groupBy("year")
            .agg(F.count("*").alias("days"), F.sum("trips").alias("trips"))
            .withColumn("trips_per_day", F.round(F.col("trips") / F.col("days"), 1))
            .orderBy("year"))


def hour_weekday_trips(trips):
    trips.createOrReplaceTempView("q1_trips")
    return trips.sparkSession.sql(HOUR_WEEKDAY_SQL)
