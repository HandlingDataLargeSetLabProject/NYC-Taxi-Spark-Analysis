import csv
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from hlds.demand import add_pickup_parts, daily_average_by_year, daily_trips, hour_weekday_trips
from hlds.results import write_csv
from hlds.session import get_spark

COLUMNS = "tpep_pickup_datetime timestamp_ntz, has_negative_part boolean"
# 1 and 8 January 2024 are Mondays, 5 January 2025 is a Sunday.
ROWS = [
    (datetime(2024, 1, 1, 8, 5), False),
    (datetime(2024, 1, 1, 8, 40), False),
    (datetime(2024, 1, 1, 9, 15), True),
    (datetime(2024, 1, 8, 8, 10), False),
    (datetime(2025, 1, 5, 23, 30), False),
]


class DemandTest(unittest.TestCase):
    """Uses a few hand-made rows, so the tests do not need the downloaded data."""

    @classmethod
    def setUpClass(cls):
        # Each collect is a Spark job of several seconds, so every result is collected once.
        cls.spark = get_spark("hlds-test")
        cls.trips = add_pickup_parts(cls.spark.createDataFrame(ROWS, COLUMNS))
        cls.parts = cls.trips.collect()
        cls.daily = daily_trips(cls.trips).collect()
        cls.averages = {row["year"]: row for row in daily_average_by_year(daily_trips(cls.trips)).collect()}
        cls.slots = {(row["year"], row["weekday"], row["hour"]): row
                     for row in hour_weekday_trips(cls.trips).collect()}

    def test_weekday_starts_with_monday_as_zero(self):
        weekdays = {row["pickup_date"].isoformat(): row["weekday"] for row in self.parts}
        self.assertEqual(weekdays["2024-01-01"], 0)
        self.assertEqual(weekdays["2025-01-05"], 6)

    def test_hour_is_the_new_york_clock_hour(self):
        late = [row for row in self.parts if row["year"] == 2025][0]
        self.assertEqual((late["hour"], late["pickup_date"].isoformat()), (23, "2025-01-05"))

    def test_daily_trips_count_flagged_rows_too(self):
        daily = {row["pickup_date"].isoformat(): row["trips"] for row in self.daily}
        self.assertEqual(daily, {"2024-01-01": 3, "2024-01-08": 1, "2025-01-05": 1})

    def test_daily_trips_are_sorted_by_date(self):
        dates = [row["pickup_date"] for row in self.daily]
        self.assertEqual(dates, sorted(dates))

    def test_daily_average_divides_by_the_days_of_the_year(self):
        self.assertEqual((self.averages[2024]["days"], self.averages[2024]["trips"]), (2, 4))
        self.assertEqual(self.averages[2024]["trips_per_day"], 2.0)

    def test_hour_weekday_divides_by_all_days_of_that_weekday(self):
        # Hour 9 has a trip on only one of the two Mondays, so its average is 1 / 2.
        self.assertEqual(self.slots[(2024, 0, 8)]["trips_per_day"], 1.5)
        self.assertEqual(self.slots[(2024, 0, 9)]["trips_per_day"], 0.5)

    def test_hour_weekday_keeps_the_years_apart(self):
        self.assertEqual(set(self.slots), {(2024, 0, 8), (2024, 0, 9), (2025, 6, 23)})

    def test_write_csv_writes_header_and_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "out" / "daily.csv"
            write_csv(daily_trips(self.trips), path)
            with open(path, newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))
        self.assertEqual(rows[0], {"year": "2024", "pickup_date": "2024-01-01", "trips": "3"})
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
