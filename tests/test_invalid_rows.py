import unittest
from datetime import datetime, timedelta

from hlds.cleaning import AMOUNT_COLUMNS, add_negative_part_flag, clean_trips, drop_duplicate_rows, drop_invalid_rows
from hlds.session import get_spark

SCHEMA = (
    "tpep_pickup_datetime timestamp_ntz, tpep_dropoff_datetime timestamp_ntz, trip_distance double, "
    "fare_amount double, extra double, mta_tax double, tip_amount double, tolls_amount double, "
    "improvement_surcharge double, total_amount double, congestion_surcharge double, Airport_fee double, "
    "cbd_congestion_fee double"
)
VALID = {
    "tpep_pickup_datetime": datetime(2025, 2, 10, 8, 30),
    "tpep_dropoff_datetime": datetime(2025, 2, 10, 8, 50),
    "trip_distance": 2.5,
    "fare_amount": 15.0,
    "extra": 1.0,
    "mta_tax": 0.5,
    "tip_amount": 3.0,
    "tolls_amount": 0.0,
    "improvement_surcharge": 1.0,
    "total_amount": 24.0,
    "congestion_surcharge": 2.5,
    "Airport_fee": 0.0,
    "cbd_congestion_fee": 0.75,
}


def trip_at(pickup):
    return {"tpep_pickup_datetime": pickup, "tpep_dropoff_datetime": pickup + timedelta(minutes=10)}


CASES = {
    "valid": {},
    "first second of 2024": trip_at(datetime(2024, 1, 1)),
    "last second of March 2024": trip_at(datetime(2024, 3, 31, 23, 59, 59)),
    "first second of 2025": trip_at(datetime(2025, 1, 1)),
    "last second of March 2025": trip_at(datetime(2025, 3, 31, 23, 59, 59)),
    "before 2024": trip_at(datetime(2023, 12, 31, 23, 59, 59)),
    "April 2024": trip_at(datetime(2024, 4, 1)),
    "December 2024": trip_at(datetime(2024, 12, 31)),
    "April 2025": trip_at(datetime(2025, 4, 1)),
    "year 2007": trip_at(datetime(2007, 12, 5)),
    "dropoff before pickup": {"tpep_dropoff_datetime": datetime(2025, 2, 10, 8, 29)},
    "zero seconds": {"tpep_dropoff_datetime": datetime(2025, 2, 10, 8, 30)},
    "one second": {"tpep_dropoff_datetime": datetime(2025, 2, 10, 8, 30, 1)},
    "exactly five hours": {"tpep_dropoff_datetime": datetime(2025, 2, 10, 13, 30)},
    "over five hours": {"tpep_dropoff_datetime": datetime(2025, 2, 10, 13, 30, 1)},
    "zero miles": {"trip_distance": 0.0},
    "negative miles": {"trip_distance": -1.5},
    "smallest distance": {"trip_distance": 0.01},
    "exactly the distance limit": {"trip_distance": 100.0},
    "over the distance limit": {"trip_distance": 100.01},
    "missing amounts": {"congestion_surcharge": None, "Airport_fee": None, "cbd_congestion_fee": None},
    "negative total": {"total_amount": -24.0},
    "negative fare with a positive total": {"fare_amount": -4.75},
}
DROPPED = {
    "before 2024", "April 2024", "December 2024", "April 2025", "year 2007", "dropoff before pickup",
    "zero seconds", "over five hours", "zero miles", "negative miles", "over the distance limit", "negative total",
}


class InvalidRowsTest(unittest.TestCase):
    """Uses hand-made rows, so the tests do not need the downloaded data. One Spark job checks all the cases."""

    @classmethod
    def setUpClass(cls):
        cls.spark = get_spark("hlds-test")
        rows = [(*{**VALID, **change}.values(), name) for name, change in CASES.items()]
        trips = cls.spark.createDataFrame(rows, SCHEMA + ", case_name string")
        cls.kept = {row["case_name"] for row in drop_invalid_rows(trips).select("case_name").collect()}

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_each_case_is_kept_or_dropped_as_expected(self):
        for name in CASES:
            with self.subTest(case=name):
                self.assertEqual(name in self.kept, name not in DROPPED)

    def test_flag_marks_a_negative_amount_in_any_column(self):
        rows = [(*{**VALID, column: -0.5}.values(), column) for column in AMOUNT_COLUMNS]
        rows.append((*VALID.values(), "valid"))
        rows.append((*{**VALID, "congestion_surcharge": None, "cbd_congestion_fee": None}.values(), "missing"))
        flagged = add_negative_part_flag(self.spark.createDataFrame(rows, SCHEMA + ", case_name string"))
        names = {row["case_name"] for row in flagged.filter("has_negative_part").collect()}
        self.assertEqual(names, set(AMOUNT_COLUMNS))

    def test_only_exact_duplicates_are_dropped(self):
        rows = [tuple(row.values()) for row in [VALID, VALID, {**VALID, "tip_amount": 4.0}]]
        self.assertEqual(drop_duplicate_rows(self.spark.createDataFrame(rows, SCHEMA)).count(), 2)

    def test_full_cleaning_runs_after_the_missing_value_step(self):
        codes = {"passenger_count": 0, "RatecodeID": 99, "store_and_fwd_flag": "N", "payment_type": 1}
        rows = [{**VALID, **codes}, {**VALID, **codes}, {**VALID, **codes, "trip_distance": 0.0}]
        rows.append({**VALID, **codes, "fare_amount": -4.75})
        schema = SCHEMA + ", passenger_count long, RatecodeID long, store_and_fwd_flag string, payment_type long"
        cleaned = clean_trips(self.spark.createDataFrame([tuple(row.values()) for row in rows], schema)).collect()
        self.assertEqual(sorted(row["has_negative_part"] for row in cleaned), [False, True])
        self.assertIsNone(cleaned[0]["passenger_count"])
        self.assertIsNone(cleaned[0]["RatecodeID"])


if __name__ == "__main__":
    unittest.main()
