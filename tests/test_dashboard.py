import unittest

import pandas as pd

from dashboard import charts, data
from dashboard.colors import PAYMENT_COLORS, PAYMENT_COLORS_DARK, PAYMENT_ORDER, YEAR_COLORS


def zone_rows():
    return pd.DataFrame([
        (2024, 1, "Manhattan", "A", 300, 3.3, 1),
        (2024, 2, "Manhattan", "B", 200, 2.2, 2),
        (2024, 3, "Queens", "C", 100, 1.1, 3),
        (2025, 1, "Manhattan", "A", 250, 2.8, 2),
        (2025, 2, "Manhattan", "B", 400, 4.4, 1),
        (2025, 3, "Queens", "C", 50, 0.6, 3),
    ], columns=["year", "zone_id", "borough", "zone", "trips", "trips_per_day", "rank_in_year"])


def flow_rows():
    return pd.DataFrame([
        (2024, "Manhattan", "Manhattan", 900, 9.9, 0.8),
        (2024, "Queens", "Manhattan", 50, 0.5, 0.1),
        (2025, "Manhattan", "Manhattan", 950, 10.6, 0.8),
        (2025, "Queens", "Manhattan", 60, 0.7, 0.1),
        (2025, "Queens", "Queens", 40, 0.4, 0.05),
    ], columns=["year", "pickup_borough", "dropoff_borough", "trips", "trips_per_day", "share"])


def borough_payment_rows():
    rows = []
    for year in (2024, 2025):
        for borough in ("Brooklyn", "Manhattan", "EWR"):
            for payment in PAYMENT_ORDER:
                rows.append((year, borough, payment, 10, 1.0, 0.25))
    return pd.DataFrame(rows, columns=["year", "pickup_borough", "payment", "trips", "trips_per_day",
                                       "share_in_borough"])


def zone_charge_rows():
    return pd.DataFrame([
        (2025, 1, "Manhattan", "A", "all trips", 100, 10.0, 1.0),
        (2025, 1, "Manhattan", "A", "pays the charge", 90, 9.0, 0.9),
        (2025, 2, "Queens", "C", "all trips", 300, 30.0, 1.0),
        (2025, 3, "Bronx", "D", "all trips", 50, 5.0, 1.0),
        (2024, 2, "Queens", "C", "all trips", 999, 99.9, 1.0),
    ], columns=["year", "zone_id", "borough", "zone", "charge_group", "trips", "trips_per_day", "share"])


class DashboardDataTest(unittest.TestCase):
    def test_top_zones_keep_both_years_of_the_busiest_zones_of_2025(self):
        rows = data.top_zones(zone_rows(), count=2)
        self.assertEqual(list(rows["zone"].astype(str)), ["B", "B", "A", "A"])
        self.assertEqual(list(rows["year"]), [2024, 2025, 2024, 2025])

    def test_top_flows_leave_out_manhattan_to_manhattan(self):
        rows = data.top_flows(flow_rows(), count=5)
        self.assertNotIn("Manhattan → Manhattan", set(rows["flow"].astype(str)))
        self.assertEqual(list(rows["flow"].cat.categories), ["Queens → Manhattan", "Queens → Queens"])

    def test_manhattan_internal_gives_trips_per_day_by_year(self):
        self.assertEqual(data.manhattan_internal(flow_rows()), {2024: 9.9, 2025: 10.6})

    def test_borough_shares_keep_only_the_main_boroughs(self):
        rows = data.borough_payment_shares(borough_payment_rows())
        self.assertEqual(set(rows["pickup_borough"].astype(str)), {"Brooklyn", "Manhattan"})

    def test_zones_without_paying_trips_get_a_share_of_zero(self):
        rows = data.busiest_zone_charge_shares(zone_charge_rows(), count=3)
        self.assertEqual(list(rows["zone"]), ["C", "A", "D"])
        self.assertEqual(list(rows["share"]), [0.0, 0.9, 0.0])


class DashboardChartTest(unittest.TestCase):
    def test_flex_fare_is_its_own_trace_with_its_own_colour(self):
        fig = charts.borough_payment_chart(data.borough_payment_shares(borough_payment_rows()))
        colours = {trace.name: trace.marker.color for trace in fig.data}
        self.assertEqual(list(colours), PAYMENT_ORDER)
        self.assertEqual(colours["flex fare"], PAYMENT_COLORS["flex fare"])

    def test_dark_mode_uses_the_dark_payment_colours(self):
        fig = charts.borough_payment_chart(data.borough_payment_shares(borough_payment_rows()), dark=True)
        self.assertEqual(fig.data[1].marker.color, PAYMENT_COLORS_DARK["flex fare"])

    def test_year_bars_have_one_trace_per_year_in_the_year_colour(self):
        fig = charts.year_comparison_bars(data.top_zones(zone_rows(), count=2), "zone", "title")
        self.assertEqual([trace.name for trace in fig.data], ["2024", "2025"])
        self.assertEqual(fig.data[1].marker.color, YEAR_COLORS[2025])

    def test_payment_colours_are_all_different(self):
        self.assertEqual(len(set(PAYMENT_COLORS.values())), len(PAYMENT_ORDER))


if __name__ == "__main__":
    unittest.main()
