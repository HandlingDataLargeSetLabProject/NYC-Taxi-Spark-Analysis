import unittest
from datetime import datetime

from hlds.prices import add_price_measures, price_summary
from hlds.session import get_spark

COLUMNS = (
    "tpep_pickup_datetime timestamp_ntz, tpep_dropoff_datetime timestamp_ntz, trip_distance double, "
    "total_amount double, tip_amount double, payment_type int, has_negative_part boolean"
)
ROWS = [
    # The New York clocks jumped from 02:00 to 03:00 on 10 March 2024: 75 minutes by the clock, 15 in reality.
    (datetime(2024, 3, 10, 1, 50), datetime(2024, 3, 10, 3, 5), 2.0, 20.0, 0.0, 2, False),
    (datetime(2024, 1, 2, 8, 0), datetime(2024, 1, 2, 8, 30), 2.0, 23.0, 3.0, 1, False),
    (datetime(2024, 1, 2, 8, 10), datetime(2024, 1, 2, 8, 40), 4.0, 20.0, 0.0, 1, False),
    (datetime(2024, 1, 2, 9, 0), datetime(2024, 1, 2, 9, 20), 3.0, 30.0, 0.0, 0, False),
    (datetime(2024, 1, 2, 9, 0), datetime(2024, 1, 2, 9, 20), 3.0, 5.0, 0.0, 0, True),
    (datetime(2025, 1, 6, 8, 0), datetime(2025, 1, 6, 8, 15), 1.0, 12.0, 0.0, 4, False),
]


class PricesTest(unittest.TestCase):
    """Uses a few hand-made rows, so the tests do not need the downloaded data."""

    @classmethod
    def setUpClass(cls):
        # Each collect is a Spark job of several seconds, so every result is collected once.
        cls.spark = get_spark("hlds-test")
        measures = add_price_measures(cls.spark.createDataFrame(ROWS, COLUMNS))
        cls.rows = measures.orderBy("tpep_pickup_datetime", "trip_distance").collect()
        cls.by_payment = {(row["year"], row["payment"]): row for row in price_summary(measures, ["year", "payment"]).collect()}
        cls.by_hour = {(row["year"], row["hour"], row["payment"]): row
                       for row in price_summary(measures, ["year", "hour", "payment"]).collect()}

    def row(self, pickup, distance):
        return next(row for row in self.rows if row["tpep_pickup_datetime"] == pickup and row["trip_distance"] == distance)

    def test_rows_with_a_negative_part_are_left_out(self):
        self.assertEqual(len(self.rows), 5)

    def test_duration_is_real_time_across_the_summer_time_change(self):
        self.assertEqual(self.row(datetime(2024, 3, 10, 1, 50), 2.0)["duration_minutes"], 15.0)

    def test_speed_is_miles_per_hour(self):
        self.assertEqual(self.row(datetime(2024, 1, 2, 8, 10), 4.0)["speed_mph"], 8.0)

    def test_price_per_mile_uses_the_total(self):
        self.assertEqual(self.row(datetime(2024, 1, 2, 8, 10), 4.0)["price_per_mile"], 5.0)

    def test_tip_percentage_is_tip_over_the_rest_of_the_total(self):
        self.assertEqual(self.row(datetime(2024, 1, 2, 8, 0), 2.0)["tip_pct"], 15.0)

    def test_tip_percentage_is_empty_for_cash(self):
        self.assertIsNone(self.row(datetime(2024, 3, 10, 1, 50), 2.0)["tip_pct"])

    def test_payment_groups_keep_flex_fare_apart(self):
        payments = {(row["payment_type"], row["payment"]) for row in self.rows}
        self.assertEqual(payments, {(0, "flex fare"), (1, "credit card"), (2, "cash"), (4, "other")})

    def test_summary_counts_trips_per_group(self):
        self.assertEqual(self.by_payment[(2024, "credit card")]["trips"], 2)
        self.assertEqual(self.by_payment[(2024, "flex fare")]["trips"], 1)

    def test_summary_averages_the_tip_of_card_trips(self):
        self.assertEqual(self.by_payment[(2024, "credit card")]["mean_tip_pct"], 7.5)
        self.assertIsNone(self.by_payment[(2024, "cash")]["mean_tip_pct"])

    def test_summary_has_medians(self):
        card = self.by_payment[(2024, "credit card")]
        self.assertEqual(card["median_duration_minutes"], 30.0)
        self.assertEqual(card["median_speed_mph"], 4.0)

    def test_summary_by_hour_uses_the_new_york_pickup_hour(self):
        self.assertEqual(set(self.by_hour), {(2024, 1, "cash"), (2024, 8, "credit card"), (2024, 9, "flex fare"),
                                             (2025, 8, "other")})


if __name__ == "__main__":
    unittest.main()
