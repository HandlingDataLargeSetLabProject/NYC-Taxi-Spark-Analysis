import unittest
from datetime import datetime

from hlds.places import add_zone_names, airport_trips, borough_flows, quarter_days, top_routes, zone_trips
from hlds.session import get_spark

ZONE_COLUMNS = "LocationID int, Borough string, Zone string, service_zone string"
ZONES = [
    (1, "EWR", "Newark Airport", "EWR"),
    (132, "Queens", "JFK Airport", "Airports"),
    (161, "Manhattan", "Midtown Center", "Yellow Zone"),
    (236, "Manhattan", "Upper East Side North", "Yellow Zone"),
    (264, "Unknown", "N/A", "N/A"),
    (265, "N/A", "Outside of NYC", "N/A"),
]
TRIP_COLUMNS = "tpep_pickup_datetime timestamp_ntz, PULocationID int, DOLocationID int"
DAY_1, DAY_2 = datetime(2024, 1, 2, 8, 0), datetime(2024, 1, 3, 8, 0)
DAY_2025 = datetime(2025, 1, 6, 8, 0)
TRIPS = [
    # 2024 has two days and 2025 one, so trips per day differ from plain counts.
    (DAY_1, 161, 236), (DAY_1, 161, 236), (DAY_2, 236, 161), (DAY_2, 132, 161), (DAY_2, 161, 1),
    (DAY_2, 264, 161),
    (DAY_2025, 161, 132), (DAY_2025, 132, 161), (DAY_2025, 265, 265),
]


class PlacesTest(unittest.TestCase):
    """Uses a few hand-made rows and zones, so the tests do not need the downloaded data."""

    @classmethod
    def setUpClass(cls):
        # Each collect is a Spark job of several seconds, so every result is collected once.
        cls.spark = get_spark("hlds-test")
        # Kept in memory as one partition: otherwise every result reads the rows again from Python in 20 tasks,
        # and the eight tests took seven minutes.
        trips = cls.spark.createDataFrame(TRIPS, TRIP_COLUMNS).coalesce(1).cache()
        zones = cls.spark.createDataFrame(ZONES, ZONE_COLUMNS).coalesce(1).cache()
        days = quarter_days(trips)
        named = add_zone_names(trips, zones)
        cls.named = named.collect()
        cls.pickups = zone_trips(named, days, "pickup").collect()
        cls.dropoffs = zone_trips(named, days, "dropoff").collect()
        cls.flows = {(row["year"], row["pickup_borough"], row["dropoff_borough"]): row
                     for row in borough_flows(named, days).collect()}
        cls.routes = top_routes(named, days).collect()
        cls.first_routes = top_routes(named, days, top=1).collect()
        cls.airports = {(row["year"], row["airport"], row["direction"]): row["trips"]
                        for row in airport_trips(named, days).collect()}

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_zone_names_are_added_for_both_ends_without_losing_trips(self):
        self.assertEqual(len(self.named), len(TRIPS))
        trip = next(row for row in self.named if row["PULocationID"] == 161 and row["DOLocationID"] == 1)
        self.assertEqual((trip["pickup_zone"], trip["dropoff_borough"], trip["year"]), ("Midtown Center", "EWR", 2024))

    def test_zones_are_ranked_by_trips_and_counted_per_day(self):
        ranked = [(row["zone_id"], row["trips"], row["trips_per_day"], row["rank_in_year"])
                  for row in self.pickups if row["year"] == 2024]
        self.assertEqual(ranked, [(161, 3, 1.5, 1), (132, 1, 0.5, 2), (236, 1, 0.5, 3)])

    def test_unknown_zones_are_left_out_of_the_rankings(self):
        zones = {row["zone_id"] for row in self.pickups + self.dropoffs}
        self.assertNotIn(264, zones)
        self.assertNotIn(265, zones)

    def test_borough_flows_keep_unknown_zones_and_add_up_to_one(self):
        self.assertEqual(self.flows[(2024, "Manhattan", "Manhattan")]["trips"], 3)
        self.assertEqual(self.flows[(2024, "Manhattan", "Manhattan")]["share"], 0.5)
        self.assertEqual(self.flows[(2024, "Unknown", "Manhattan")]["trips"], 1)
        # Each share is rounded to four places, so the sum can be off in the fourth place.
        self.assertAlmostEqual(sum(row["share"] for key, row in self.flows.items() if key[0] == 2024), 1.0, places=3)

    def test_busiest_route_comes_first(self):
        first = self.routes[0]
        self.assertEqual((first["year"], first["pickup_zone"], first["dropoff_zone"], first["trips"],
                          first["trips_per_day"]), (2024, "Midtown Center", "Upper East Side North", 2, 1.0))

    def test_routes_leave_out_unknown_zones(self):
        self.assertEqual(sum(1 for row in self.routes if row["year"] == 2024), 4)
        self.assertEqual(sum(1 for row in self.routes if row["year"] == 2025), 2)

    def test_top_limits_the_routes_of_each_year(self):
        self.assertEqual([(row["year"], row["rank_in_year"]) for row in self.first_routes], [(2024, 1), (2025, 1)])

    def test_airport_trips_count_both_directions(self):
        self.assertEqual(self.airports, {
            (2024, "JFK Airport", "from"): 1, (2024, "Newark Airport", "to"): 1,
            (2025, "JFK Airport", "from"): 1, (2025, "JFK Airport", "to"): 1,
        })


if __name__ == "__main__":
    unittest.main()
