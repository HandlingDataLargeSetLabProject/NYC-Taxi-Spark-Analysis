import unittest
from datetime import datetime

from hlds.session import get_spark
from hlds.statistics import add_year_and_duration, category_shares, numeric_summary

COLUMNS = (
    "tpep_pickup_datetime timestamp_ntz, tpep_dropoff_datetime timestamp_ntz, trip_distance double, "
    "passenger_count int, fare_amount double, tip_amount double, tolls_amount double, total_amount double, "
    "congestion_surcharge double, Airport_fee double, cbd_congestion_fee double, has_negative_part boolean, "
    "payment_type int"
)
PRICES = (0.0, 0.0, 20.0, 2.5, 0.0)
ROWS = [
    (datetime(2024, 2, 1, 8, 0), datetime(2024, 2, 1, 8, 10), 1.0, 1, 10.0, *PRICES, None, False, 1),
    (datetime(2024, 2, 1, 9, 0), datetime(2024, 2, 1, 9, 30), 3.0, None, 30.0, *PRICES, None, False, 2),
    (datetime(2025, 2, 1, 8, 0), datetime(2025, 2, 1, 8, 20), 2.0, 2, 10.0, *PRICES, 0.75, False, 1),
    (datetime(2025, 2, 1, 9, 0), datetime(2025, 2, 1, 9, 20), 4.0, 1, -4.75, *PRICES, 0.75, True, 1),
]


class StatisticsTest(unittest.TestCase):
    """Uses a few hand-made rows, so the tests do not need the downloaded data."""

    @classmethod
    def setUpClass(cls):
        cls.spark = get_spark("hlds-test")
        cls.trips = add_year_and_duration(cls.spark.createDataFrame(ROWS, COLUMNS))
        summary = numeric_summary(cls.trips, ["year"])
        cls.summary = {(entry["year"], entry["column"]): entry for entry in summary}

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_duration_is_in_minutes(self):
        self.assertEqual(self.summary[(2024, "duration_minutes")]["max"], 30.0)
        self.assertEqual(self.summary[(2024, "duration_minutes")]["mean"], 20.0)

    def test_missing_values_are_counted_and_left_out_of_the_mean(self):
        passengers = self.summary[(2024, "passenger_count")]
        self.assertEqual((passengers["rows"], passengers["missing"], passengers["mean"]), (1, 1, 1.0))

    def test_flagged_rows_count_for_general_columns_only(self):
        self.assertEqual(self.summary[(2025, "trip_distance")]["rows"], 2)
        fare = self.summary[(2025, "fare_amount")]
        self.assertEqual((fare["rows"], fare["min"]), (1, 10.0))

    def test_column_missing_in_a_whole_year_has_no_statistics(self):
        charge = self.summary[(2024, "cbd_congestion_fee")]
        self.assertEqual((charge["rows"], charge["missing"], charge["mean"], charge["median"]), (0, 2, None, None))

    def test_category_shares_add_up_within_a_year(self):
        shares = {(row["year"], row["value"]): row["share"] for row in category_shares(self.trips, "payment_type")}
        self.assertEqual(shares, {(2024, 1): 0.5, (2024, 2): 0.5, (2025, 1): 1.0})


if __name__ == "__main__":
    unittest.main()
