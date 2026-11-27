import unittest
from datetime import datetime

import pandas as pd

from dashboard import charts
from hlds.demand import add_pickup_parts
from hlds.session import get_spark
from hlds.zone_groups import (
    SLOT_COLUMNS,
    add_features,
    assign_groups,
    best_k,
    group_profiles,
    silhouette_by_k,
    zone_profiles,
)

COLUMNS = "tpep_pickup_datetime timestamp_ntz, PULocationID int"


def trips_at(zone, hour, count):
    # 6 January 2025 is a Monday and 7 January a Tuesday; the same trips on both days.
    return [(datetime(2025, 1, day, hour, minute % 60), zone) for day in (6, 7) for minute in range(count)]


# Zones 1 and 2 are busy at 08:00, zones 3 and 4 at 23:00. Zones 2 and 4 have a few trips in the next hour, so
# there are four different profiles: KMeans fails when k is larger than the number of different points.
# Zone 5 has 2 trips per day, zone 264 is not a place.
ROWS = (trips_at(1, 8, 30) + trips_at(2, 8, 30) + trips_at(2, 9, 3) + trips_at(3, 23, 30) + trips_at(4, 23, 25)
        + trips_at(4, 22, 3) + trips_at(5, 8, 2) + trips_at(264, 8, 50) + [(datetime(2024, 1, 8, 8, 0), 1)])


class ZoneGroupsTest(unittest.TestCase):
    """Uses a few hand-made rows, so the tests do not need the downloaded data."""

    @classmethod
    def setUpClass(cls):
        # Each collect is a Spark job of several seconds, so every result is collected once. The pivot and the
        # KMeans fits run many small jobs; with the default 200 shuffle partitions the class took about 14 minutes.
        spark = get_spark("hlds-test")
        cls.spark = spark
        cls.partitions = spark.conf.get("spark.sql.shuffle.partitions")
        spark.conf.set("spark.sql.shuffle.partitions", "4")
        trips = add_pickup_parts(spark.createDataFrame(ROWS, COLUMNS))
        cls.profiles = zone_profiles(trips, year=2025, min_trips_per_day=10).cache()
        cls.rows = {row["PULocationID"]: row for row in cls.profiles.collect()}
        features = add_features(cls.profiles)
        cls.results = silhouette_by_k(features, k_values=[2, 3])
        cls.groups = {row["PULocationID"]: row for row in assign_groups(features, best_k(cls.results)[2]).collect()}
        cls.means = group_profiles(cls.profiles, assign_groups(features, best_k(cls.results)[2])).toPandas()

    @classmethod
    def tearDownClass(cls):
        cls.profiles.unpersist()
        cls.spark.conf.set("spark.sql.shuffle.partitions", cls.partitions)

    def test_small_zones_and_zones_that_are_not_places_are_left_out(self):
        self.assertEqual(sorted(self.rows), [1, 2, 3, 4])

    def test_profile_is_the_share_of_the_week_in_each_hour(self):
        zone = self.rows[1]
        self.assertAlmostEqual(sum(zone[name] for name in SLOT_COLUMNS), 1.0)
        self.assertAlmostEqual(zone["slot_0_08"], 0.5)
        self.assertAlmostEqual(zone["slot_1_08"], 0.5)
        self.assertAlmostEqual(zone["trips_per_day"], 30.0)

    def test_silhouette_chooses_the_two_clear_groups(self):
        k, silhouette, _ = best_k(self.results)
        self.assertEqual(k, 2)
        self.assertGreater(silhouette, 0.9)

    def test_groups_are_numbered_by_their_trips(self):
        self.assertEqual(self.groups[1]["group"], self.groups[2]["group"])
        self.assertEqual(self.groups[3]["group"], self.groups[4]["group"])
        # The morning zones have 63 trips per day together, the night zones 58.
        self.assertEqual(self.groups[1]["group"], 1)
        self.assertEqual(self.groups[3]["group"], 2)

    def test_group_profiles_are_long_and_sum_to_one(self):
        self.assertEqual(len(self.means), 2 * 168)
        for _, group in self.means.groupby("group"):
            self.assertAlmostEqual(group["share"].sum(), 1.0)

    def test_best_k_takes_the_smaller_k_on_a_tie(self):
        self.assertEqual(best_k([(2, 0.5, None), (3, 0.5, None)])[0], 2)


class ZoneGroupChartTest(unittest.TestCase):
    def test_one_panel_per_group_on_the_same_scale(self):
        rows = [(group, day, hour, 1 / 168) for group in (1, 2) for day in range(7) for hour in range(24)]
        profiles = pd.DataFrame(rows, columns=["group", "weekday", "hour", "share"])
        fig = charts.zone_group_profiles_chart(profiles, {1: "a", 2: "b"})
        self.assertEqual(len(fig.data), 2)
        self.assertEqual(fig.layout.yaxis.range, fig.layout.yaxis2.range)
