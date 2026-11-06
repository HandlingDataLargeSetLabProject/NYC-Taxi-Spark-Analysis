import os
import sys
import unittest

from hlds.session import get_spark


class GetSparkTest(unittest.TestCase):
    """Starts one real local Spark session for all tests (takes about 20 seconds)."""

    @classmethod
    def setUpClass(cls):
        cls.spark = get_spark("hlds-test")

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_runs_in_local_mode_on_all_cores(self):
        self.assertEqual(self.spark.sparkContext.master, "local[*]")

    def test_uses_the_given_app_name(self):
        self.assertEqual(self.spark.sparkContext.appName, "hlds-test")

    def test_python_workers_use_this_interpreter(self):
        self.assertEqual(os.environ["PYSPARK_PYTHON"], sys.executable)

    def test_python_udf_runs(self):
        from pyspark.sql import functions as F

        plus_one = F.udf(lambda x: x + 1, "long")
        values = [row[0] for row in self.spark.range(3).select(plus_one("id")).collect()]
        self.assertEqual(values, [1, 2, 3])

    def test_driver_memory_is_fixed(self):
        self.assertEqual(self.spark.conf.get("spark.driver.memory"), "6g")

    def test_session_time_zone_is_utc(self):
        self.assertEqual(self.spark.conf.get("spark.sql.session.timeZone"), "UTC")

    def test_duration_does_not_depend_on_the_laptop_time_zone(self):
        from pyspark.sql import functions as F

        # 02:00 to 03:00 did not exist in Poland on this night (summer time), but the taxi times are New York times.
        trip = self.spark.sql(
            "SELECT TIMESTAMP_NTZ'2024-03-31 02:30:00' AS pickup, TIMESTAMP_NTZ'2024-03-31 03:10:00' AS dropoff"
        )
        seconds = trip.select(F.timestamp_diff("SECOND", "pickup", "dropoff")).first()[0]
        self.assertEqual(seconds, 40 * 60)

    def test_extra_settings_are_applied(self):
        spark = get_spark("hlds-test", extra_conf={"spark.sql.shuffle.partitions": "8"})
        self.assertEqual(spark.conf.get("spark.sql.shuffle.partitions"), "8")


if __name__ == "__main__":
    unittest.main()
