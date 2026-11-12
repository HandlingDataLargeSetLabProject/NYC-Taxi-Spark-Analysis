"""Optimization O1: run Q1 and Q2 one after the other, with and without caching the cleaned table.

Spark keeps no results between actions, so without a cache each of the five results below reads the
six Parquet files and cleans them again. With `cache()` the first result fills the cache and the
other four read the cleaned rows from memory.
"""

from hlds.demand import add_pickup_parts, daily_average_by_year, daily_trips, hour_weekday_trips
from hlds.prices import add_price_measures, price_summary


def run_q1_and_q2(trips):
    """Collect every result of Q1 and Q2 and return the last one, which has run and so has a final plan."""
    parts = add_pickup_parts(trips)
    daily = daily_trips(parts)
    measures = add_price_measures(trips)
    results = [
        daily,
        daily_average_by_year(daily),
        hour_weekday_trips(parts),
        price_summary(measures, ["year", "payment"]),
        price_summary(measures, ["year", "hour", "payment"]),
    ]
    for result in results:
        result.collect()
    return results[-1]
