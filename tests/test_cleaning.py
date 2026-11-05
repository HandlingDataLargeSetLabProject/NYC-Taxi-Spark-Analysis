import unittest
from datetime import datetime

from hlds.cleaning import clean_missing_values_and_types
from hlds.session import get_spark

RAW_SCHEMA = (
    "tpep_pickup_datetime timestamp_ntz, passenger_count long, RatecodeID long, "
    "store_and_fwd_flag string, payment_type long, cbd_congestion_fee double"
)
FULL_DETAILS = {
    "tpep_pickup_datetime": datetime(2025, 2, 10, 8, 30),
    "passenger_count": 1,
    "RatecodeID": 1,
    "store_and_fwd_flag": "N",
    "payment_type": 1,
    "cbd_congestion_fee": 0.75,
}
FLEX_FARE = {
    **FULL_DETAILS,
    "passenger_count": None,
    "RatecodeID": None,
    "store_and_fwd_flag": None,
    "payment_type": 0,
}


class CleanMissingValuesAndTypesTest(unittest.TestCase):
    """Runs the cleaning on a few hand-made rows, so the tests do not need the downloaded data."""

    @classmethod
    def setUpClass(cls):
        cls.spark = get_spark("hlds-test")

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def clean(self, *changes):
        rows = [{**FULL_DETAILS, **change} for change in changes]
        raw = self.spark.createDataFrame([tuple(row.values()) for row in rows], RAW_SCHEMA)
        return clean_missing_values_and_types(raw)

    def test_no_rows_are_dropped(self):
        self.assertEqual(self.clean({}, FLEX_FARE, {"passenger_count": 0}).count(), 3)

    def test_code_columns_become_integers(self):
        types = dict(self.clean({}).dtypes)
        for column in ["passenger_count", "RatecodeID", "payment_type"]:
            with self.subTest(column=column):
                self.assertEqual(types[column], "int")

    def test_store_and_forward_flag_becomes_boolean(self):
        flags = [row["store_and_fwd_flag"] for row in self.clean(
            {"store_and_fwd_flag": "Y"}, {"store_and_fwd_flag": "N"}, FLEX_FARE
        ).collect()]
        self.assertEqual(flags, [True, False, None])

    def test_zero_passengers_become_missing(self):
        counts = [row["passenger_count"] for row in self.clean({"passenger_count": 0}, {"passenger_count": 2}).collect()]
        self.assertEqual(counts, [None, 2])

    def test_unknown_rate_code_becomes_missing(self):
        codes = [row["RatecodeID"] for row in self.clean({"RatecodeID": 99}, {"RatecodeID": 2}).collect()]
        self.assertEqual(codes, [None, 2])

    def test_rows_without_trip_details_are_flagged(self):
        flags = [row["details_missing"] for row in self.clean({}, FLEX_FARE, {"passenger_count": 0}).collect()]
        self.assertEqual(flags, [False, True, False])

    def test_charge_flag_starts_on_5_january_2025(self):
        pickups = [datetime(2024, 3, 1, 12, 0), datetime(2025, 1, 4, 23, 59, 59), datetime(2025, 1, 5, 0, 0)]
        rows = self.clean(*[{"tpep_pickup_datetime": pickup} for pickup in pickups]).collect()
        self.assertEqual([row["charge_in_force"] for row in rows], [False, False, True])

    def test_missing_charge_in_2024_stays_missing(self):
        row = self.clean({"tpep_pickup_datetime": datetime(2024, 3, 1), "cbd_congestion_fee": None}).first()
        self.assertIsNone(row["cbd_congestion_fee"])


if __name__ == "__main__":
    unittest.main()
