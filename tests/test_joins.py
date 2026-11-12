import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from hlds.benchmarks import save_plan
from hlds.joins import AUTO_BROADCAST, automatic_broadcast_off, zone_pair_counts
from hlds.session import get_spark

ZONE_COLUMNS = "LocationID int, Borough string, Zone string, service_zone string"
ZONES = [
    (132, "Queens", "JFK Airport", "Airports"),
    (161, "Manhattan", "Midtown Center", "Yellow Zone"),
    (236, "Manhattan", "Upper East Side North", "Yellow Zone"),
]
TRIP_COLUMNS = "tpep_pickup_datetime timestamp_ntz, PULocationID int, DOLocationID int"
TRIPS = [
    (datetime(2024, 1, 2, 8, 0), 161, 236),
    (datetime(2024, 1, 2, 9, 0), 161, 236),
    (datetime(2025, 1, 6, 8, 0), 132, 161),
]


def plan_text(frame):
    with tempfile.TemporaryDirectory() as folder:
        return save_plan(frame, Path(folder), "O2", "test").read_text(encoding="utf-8")


class ZoneJoinsTest(unittest.TestCase):
    """The saved plan has to show which join really ran, so the before and after cases can be told apart."""

    @classmethod
    def setUpClass(cls):
        cls.spark = get_spark("hlds-test")
        # Kept in memory as one partition, so each run does not read the rows again from Python in many tasks.
        trips = cls.spark.createDataFrame(TRIPS, TRIP_COLUMNS).coalesce(1).cache()
        zones = cls.spark.createDataFrame(ZONES, ZONE_COLUMNS).coalesce(1).cache()
        cls.setting_before = cls.spark.conf.get(AUTO_BROADCAST)
        with automatic_broadcast_off(cls.spark):
            cls.setting_inside = cls.spark.conf.get(AUTO_BROADCAST)
            cls.shuffle = zone_pair_counts(trips, zones, broadcast_zones=False)
            cls.broadcast = zone_pair_counts(trips, zones, broadcast_zones=True)
        cls.setting_after = cls.spark.conf.get(AUTO_BROADCAST)
        cls.shuffle_plan = plan_text(cls.shuffle)
        cls.broadcast_plan = plan_text(cls.broadcast)

    @classmethod
    def tearDownClass(cls):
        cls.spark.catalog.clearCache()
        cls.spark.stop()

    def test_setting_is_off_inside_and_restored_after(self):
        self.assertEqual(self.setting_inside, "-1")
        self.assertEqual(self.setting_after, self.setting_before)

    def test_without_the_hint_the_join_stays_a_sort_merge_join(self):
        self.assertIn("SortMergeJoin", self.shuffle_plan)
        self.assertNotIn("BroadcastHashJoin", self.shuffle_plan)

    def test_with_the_hint_the_zone_table_is_broadcast(self):
        self.assertIn("BroadcastHashJoin", self.broadcast_plan)
        self.assertNotIn("SortMergeJoin", self.broadcast_plan)

    def test_saved_plans_are_final(self):
        self.assertIn("isFinalPlan=true", self.shuffle_plan)
        self.assertIn("isFinalPlan=true", self.broadcast_plan)

    def test_both_joins_give_the_same_counts(self):
        def rows(frame):
            return sorted(tuple(row) for row in frame.collect())

        self.assertEqual(rows(self.shuffle), rows(self.broadcast))
        self.assertIn((2024, "Manhattan", "Midtown Center", "Manhattan", "Upper East Side North", 2), rows(self.shuffle))


if __name__ == "__main__":
    unittest.main()
