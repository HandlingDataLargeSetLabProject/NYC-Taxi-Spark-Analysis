import unittest

from hlds import paths


class ProjectRootTest(unittest.TestCase):
    def test_project_root_is_the_repository_folder(self):
        self.assertTrue((paths.PROJECT_ROOT / "README.md").is_file())

    def test_raw_data_folder_is_inside_data(self):
        self.assertEqual(paths.RAW_DIR, paths.PROJECT_ROOT / "data" / "raw")


class TripFileTest(unittest.TestCase):
    def test_builds_monthly_file_name(self):
        self.assertEqual(paths.trip_file("2025-01").name, "yellow_tripdata_2025-01.parquet")

    def test_monthly_file_is_in_raw_folder(self):
        self.assertEqual(paths.trip_file("2025-02").parent, paths.RAW_DIR)

    def test_rejects_month_in_wrong_format(self):
        for month in ["2025-1", "2025-13", "25-01", ""]:
            with self.subTest(month=month):
                with self.assertRaises(ValueError):
                    paths.trip_file(month)

    def test_default_months_are_first_quarter_2025(self):
        self.assertEqual(paths.DEFAULT_MONTHS, ["2025-01", "2025-02", "2025-03"])

    def test_trip_files_returns_one_path_per_month(self):
        files = paths.trip_files(["2025-01", "2025-03"])
        self.assertEqual([f.name for f in files],
                         ["yellow_tripdata_2025-01.parquet", "yellow_tripdata_2025-03.parquet"])


class ZoneLookupFileTest(unittest.TestCase):
    def test_zone_lookup_is_in_raw_folder(self):
        self.assertEqual(paths.ZONE_LOOKUP_FILE, paths.RAW_DIR / "taxi_zone_lookup.csv")


if __name__ == "__main__":
    unittest.main()
