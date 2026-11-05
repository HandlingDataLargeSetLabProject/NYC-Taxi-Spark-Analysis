import tempfile
import unittest
from pathlib import Path

from hlds.loading import ZONE_COLUMNS, load_trips, load_zones
from hlds.session import get_spark


class LoadingTest(unittest.TestCase):
    """Uses small temporary files, so the tests do not need the downloaded data."""

    @classmethod
    def setUpClass(cls):
        cls.spark = get_spark("hlds-test")
        cls.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.root = Path(cls.folder.name)
        cls.old_file = cls.write_trips("old", [(1, 2.5)], "VendorID int, fare_amount double")
        cls.new_file = cls.write_trips(
            "new", [(2, 3.5, 0.75), (2, 4.5, 0.0)], "VendorID int, fare_amount double, cbd_congestion_fee double"
        )

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        cls.folder.cleanup()

    @classmethod
    def write_trips(cls, name, rows, schema):
        path = cls.root / name
        cls.spark.createDataFrame(rows, schema).write.parquet(str(path))
        return path

    def write_zones(self, name, text):
        path = self.root / name
        path.write_text(text)
        return path

    def test_trips_from_all_files_are_loaded(self):
        trips = load_trips(self.spark, [self.old_file, self.new_file])
        self.assertEqual(trips.count(), 3)

    def test_column_missing_in_one_file_is_null_there(self):
        trips = load_trips(self.spark, [self.old_file, self.new_file])
        fees = {row["VendorID"]: row["cbd_congestion_fee"] for row in trips.filter("fare_amount < 3").collect()}
        self.assertEqual(fees, {1: None})
        self.assertEqual(trips.filter("cbd_congestion_fee is not null").count(), 2)

    def test_files_with_different_types_are_rejected(self):
        other_type = self.write_trips("other_type", [("a", 2.5)], "VendorID string, fare_amount double")
        with self.assertRaises(Exception):
            load_trips(self.spark, [self.old_file, other_type]).count()

    def test_zones_keep_their_columns_and_get_an_integer_id(self):
        path = self.write_zones("zones.csv", '"LocationID","Borough","Zone","service_zone"\n1,"EWR","Newark Airport","EWR"\n')
        zones = load_zones(self.spark, path)
        self.assertEqual(zones.columns, ZONE_COLUMNS)
        self.assertEqual(dict(zones.dtypes)["LocationID"], "int")
        self.assertEqual(zones.first()["LocationID"], 1)

    def test_na_text_in_zones_stays_text(self):
        path = self.write_zones("na.csv", '"LocationID","Borough","Zone","service_zone"\n265,"N/A","Outside of NYC","N/A"\n')
        self.assertEqual(load_zones(self.spark, path).first()["Borough"], "N/A")

    def test_zones_with_other_columns_are_rejected(self):
        path = self.write_zones("bad.csv", '"id","Borough","Zone","service_zone"\n1,"EWR","Newark Airport","EWR"\n')
        with self.assertRaises(ValueError):
            load_zones(self.spark, path)


if __name__ == "__main__":
    unittest.main()
