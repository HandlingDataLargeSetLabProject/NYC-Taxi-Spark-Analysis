import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from hlds.benchmarks import save_plan
from hlds.session import get_spark
from hlds.storage import PARTITION_COLUMN, daily_summary, read_table, write_partitioned, write_plain

COLUMNS = "tpep_pickup_datetime timestamp_ntz, total_amount double"
ROWS = [
    (datetime(2025, 2, 28, 23, 50), 30.0),
    (datetime(2025, 3, 1, 8, 0), 20.0),
    (datetime(2025, 3, 1, 9, 0), 40.0),
    (datetime(2025, 3, 31, 23, 59), 10.0),
    (datetime(2025, 4, 1, 0, 5), 50.0),
]


def plan_text(frame):
    with tempfile.TemporaryDirectory() as folder:
        return save_plan(frame, Path(folder), "O3", "test").read_text(encoding="utf-8")


class StorageTest(unittest.TestCase):
    """Writes both copies of a few hand-made rows to a temporary folder and reads them with the date filter."""

    @classmethod
    def setUpClass(cls):
        cls.spark = get_spark("hlds-test")
        cls.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        trips = cls.spark.createDataFrame(ROWS, COLUMNS).coalesce(1).cache()
        plain_path, partitioned_path = Path(cls.folder.name) / "plain", Path(cls.folder.name) / "partitioned"
        write_plain(trips, plain_path)
        write_partitioned(trips, partitioned_path)
        cls.partitioned_path = partitioned_path
        cls.plain = daily_summary(read_table(cls.spark, plain_path))
        cls.partitioned = daily_summary(read_table(cls.spark, partitioned_path))
        cls.plain_plan, cls.partitioned_plan = plan_text(cls.plain), plan_text(cls.partitioned)

    @classmethod
    def tearDownClass(cls):
        cls.spark.catalog.clearCache()
        cls.spark.stop()
        cls.folder.cleanup()

    def test_each_day_has_its_own_folder(self):
        folders = sorted(path.name for path in self.partitioned_path.iterdir() if path.is_dir())
        self.assertEqual(folders, [f"{PARTITION_COLUMN}=2025-02-28", f"{PARTITION_COLUMN}=2025-03-01",
                                   f"{PARTITION_COLUMN}=2025-03-31", f"{PARTITION_COLUMN}=2025-04-01"])

    def test_both_copies_give_the_same_days(self):
        rows = [tuple(row) for row in self.partitioned.collect()]
        self.assertEqual(rows, [tuple(row) for row in self.plain.collect()])
        self.assertEqual([(str(day), trips) for day, trips, _ in rows], [("2025-03-01", 2), ("2025-03-31", 1)])

    def test_only_the_partitioned_copy_skips_folders(self):
        self.assertIn(f"PartitionFilters: [isnotnull({PARTITION_COLUMN}", self.partitioned_plan)
        # The plain copy can only hand the filter to the Parquet reader, which still opens every file.
        self.assertNotIn("PartitionFilters", self.plain_plan)
        self.assertIn(f"PushedFilters: [IsNotNull({PARTITION_COLUMN})", self.plain_plan)

    def test_missing_copy_gives_a_clear_error(self):
        with self.assertRaises(FileNotFoundError):
            read_table(self.spark, Path(self.folder.name) / "missing")


if __name__ == "__main__":
    unittest.main()
