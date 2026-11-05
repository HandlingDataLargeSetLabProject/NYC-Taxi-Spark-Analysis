"""One place to create the Spark session, so every script runs with the same settings."""

import os
import sys

from pyspark.sql import SparkSession

MASTER = "local[*]"
# Fixed so that before/after measurements run with the same memory; fits on both our 16 GB and 32 GB laptops.
DRIVER_MEMORY = "4g"
# Spark reads the taxi times in this zone. With the laptop's own zone, trips that start in the hour skipped
# by European summer time get negative durations, and results would differ between our laptops.
SESSION_TIME_ZONE = "UTC"


def get_spark(app_name="hlds", extra_conf=None):
    """Return the local Spark session, creating it on the first call.

    Settings in `extra_conf` (for example `spark.sql.shuffle.partitions`) are applied even if the
    session already exists. Memory settings only take effect when the session is first created.
    """
    # On Windows Spark workers otherwise look for `python3`, which opens the Microsoft Store shortcut.
    os.environ["PYSPARK_PYTHON"] = sys.executable

    builder = (
        SparkSession.builder.master(MASTER)
        .appName(app_name)
        .config("spark.driver.memory", DRIVER_MEMORY)
        .config("spark.sql.session.timeZone", SESSION_TIME_ZONE)
    )
    for key, value in (extra_conf or {}).items():
        builder = builder.config(key, value)
    return builder.getOrCreate()
