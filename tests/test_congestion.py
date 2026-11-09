import unittest
from datetime import datetime

from hlds.congestion import ALL_TRIPS, DOES_NOT_PAY, PAYS, charge_summary, charge_window, zone_charge_summary
from hlds.places import add_zone_names, quarter_days
from hlds.session import get_spark

ZONE_COLUMNS = "LocationID int, Borough string, Zone string, service_zone string"
ZONES = [
    (132, "Queens", "JFK Airport", "Airports"),
    (161, "Manhattan", "Midtown Center", "Yellow Zone"),
    (236, "Manhattan", "Upper East Side North", "Yellow Zone"),
    (264, "Unknown", "N/A", "N/A"),
]
TRIP_COLUMNS = (
    "tpep_pickup_datetime timestamp_ntz, PULocationID int, DOLocationID int, trip_distance double, "
    "total_amount double, cbd_congestion_fee double, has_negative_part boolean, charge_in_force boolean"
)
TRIPS = [
    # Before 5 January: left out in both years.
    (datetime(2024, 1, 3, 8, 0), 161, 236, 2.0, 20.0, None, False, False),
    (datetime(2025, 1, 4, 8, 0), 161, 236, 2.0, 20.0, 0.0, False, False),
    # 2024 has no charge column, so its rows only count as all trips.
    (datetime(2024, 1, 5, 8, 0), 161, 236, 2.0, 20.0, None, False, False),
    (datetime(2024, 1, 6, 9, 0), 236, 161, 4.0, 30.0, None, False, False),
    (datetime(2024, 1, 6, 9, 0), 236, 161, 4.0, -5.0, None, True, False),
    (datetime(2025, 1, 5, 8, 0), 161, 236, 1.0, 25.0, 0.75, False, True),
    (datetime(2025, 1, 5, 8, 0), 161, 132, 10.0, 70.0, 0.75, False, True),
    (datetime(2025, 1, 6, 9, 0), 132, 236, 12.0, 60.0, 0.0, False, True),
    (datetime(2025, 1, 6, 9, 0), 264, 161, 2.0, 15.0, 0.0, False, True),
    (datetime(2025, 1, 6, 9, 0), 236, 161, 2.0, 15.0, -0.75, True, True),
]


class CongestionTest(unittest.TestCase):
    """Uses a few hand-made rows and zones, so the tests do not need the downloaded data."""

    @classmethod
    def setUpClass(cls):
        # Kept in memory as one partition, so each result does not read the rows again from Python in many tasks.
        cls.spark = get_spark("hlds-test")
        raw = cls.spark.createDataFrame(TRIPS, TRIP_COLUMNS).coalesce(1).cache()
        zones = cls.spark.createDataFrame(ZONES, ZONE_COLUMNS).coalesce(1).cache()
        trips = charge_window(raw)
        days = quarter_days(trips)
        cls.trips = trips.collect()
        cls.days = {row["year"]: row["days"] for row in days.collect()}
        cls.overview = {(row["year"], row["charge_group"]): row for row in charge_summary(trips, days, []).collect()}
        cls.by_hour = {(row["year"], row["hour"], row["charge_group"]): row
                       for row in charge_summary(trips, days, ["hour"]).collect()}
        cls.pickups = {(row["year"], row["zone_id"], row["charge_group"]): row
                       for row in zone_charge_summary(add_zone_names(trips, zones), days, "pickup").collect()}

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_window_starts_on_5_january_and_leaves_out_negative_parts(self):
        self.assertEqual(len(self.trips), 6)
        self.assertEqual(self.days, {2024: 2, 2025: 2})

    def test_missing_charge_means_not_paying(self):
        self.assertEqual({row["pays_charge"] for row in self.trips if row["year"] == 2024}, {False})

    def test_2024_has_only_all_trips(self):
        self.assertEqual({group for year, group in self.overview if year == 2024}, {ALL_TRIPS})

    def test_charge_period_is_split_by_who_pays(self):
        paying, not_paying = self.overview[(2025, PAYS)], self.overview[(2025, DOES_NOT_PAY)]
        self.assertEqual((paying["trips"], paying["trips_per_day"], paying["share"]), (2, 1.0, 0.5))
        self.assertEqual((not_paying["trips"], not_paying["share"]), (2, 0.5))
        self.assertEqual(self.overview[(2025, ALL_TRIPS)]["trips_per_day"], 2.0)

    def test_median_price_and_distance_per_group(self):
        row = self.by_hour[(2024, 8, ALL_TRIPS)]
        self.assertEqual((row["median_total_amount"], row["median_trip_distance"]), (20.0, 2.0))

    def test_share_is_within_the_same_hour(self):
        self.assertEqual(self.by_hour[(2025, 8, PAYS)]["share"], 1.0)
        self.assertEqual(self.by_hour[(2025, 9, DOES_NOT_PAY)]["share"], 1.0)
        self.assertNotIn((2025, 9, PAYS), self.by_hour)

    def test_zones_leave_out_placeholders(self):
        self.assertEqual(self.pickups[(2025, 161, PAYS)]["trips"], 2)
        self.assertNotIn(264, {zone for _, zone, _ in self.pickups})


if __name__ == "__main__":
    unittest.main()
