import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from hlds.benchmarks import save_plan
from hlds.caching import run_q1_and_q2
from hlds.session import get_spark

COLUMNS = (
    "tpep_pickup_datetime timestamp_ntz, tpep_dropoff_datetime timestamp_ntz, trip_distance double, "
    "total_amount double, tip_amount double, payment_type int, has_negative_part boolean"
)
ROWS = [
    (datetime(2024, 1, 2, 8, 0), datetime(2024, 1, 2, 8, 30), 2.0, 23.0, 3.0, 1, False),
    (datetime(2024, 1, 2, 9, 0), datetime(2024, 1, 2, 9, 20), 3.0, 30.0, 0.0, 0, True),
    (datetime(2025, 1, 6, 8, 0), datetime(2025, 1, 6, 8, 15), 1.0, 12.0, 0.0, 2, False),
]


def plan_text(frame):
    with tempfile.TemporaryDirectory() as folder:
        return save_plan(frame, Path(folder), "O1", "test").read_text(encoding="utf-8")


class RunQ1AndQ2Test(unittest.TestCase):
    """The plan of the last result shows whether the queries read the cached table."""

    @classmethod
    def setUpClass(cls):
        cls.spark = get_spark("hlds-test")

    @classmethod
    def tearDownClass(cls):
        cls.spark.catalog.clearCache()
        cls.spark.stop()

    def trips(self):
        return self.spark.createDataFrame(ROWS, COLUMNS)

    def test_returns_the_last_q2_result_after_it_has_run(self):
        frame = run_q1_and_q2(self.trips())
        self.assertEqual(frame.columns[:3], ["year", "hour", "payment"])
        self.assertIn("isFinalPlan=true", plan_text(frame))

    def test_reads_the_cached_table_when_the_input_is_cached(self):
        trips = self.trips().cache()
        self.assertIn("InMemoryTableScan", plan_text(run_q1_and_q2(trips)))
        trips.unpersist()

    def test_does_not_read_a_cache_when_the_input_is_not_cached(self):
        self.assertNotIn("InMemoryTableScan", plan_text(run_q1_and_q2(self.trips())))


if __name__ == "__main__":
    unittest.main()
