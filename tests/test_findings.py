import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from dashboard import charts, findings
from dashboard.colors import PAYMENT_COLORS, PAYMENT_ORDER

APP_FILE = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"


def daily_average_rows():
    return pd.DataFrame([(2024, 10, 1000, 100.0), (2025, 10, 1300, 130.0)],
                        columns=["year", "days", "trips", "trips_per_day"])


def borough_payment_rows():
    # Trips per quarter of 10 days: flex fare grows by 200, card by 100, cash falls by 50 per quarter.
    trips = {"credit card": (600, 700), "flex fare": (100, 300), "cash": (250, 200), "other": (50, 100)}
    rows = []
    for payment, (in_2024, in_2025) in trips.items():
        rows.append((2024, "Manhattan", payment, in_2024, in_2024 / 10, 0.0))
        rows.append((2025, "Manhattan", payment, in_2025, in_2025 / 10, 0.0))
    return pd.DataFrame(rows, columns=["year", "pickup_borough", "payment", "trips", "trips_per_day",
                                       "share_in_borough"])


def zone_charge_rows():
    rows = []
    # zone id, 2024 per day, 2025 per day, share of 2025 trips that pay
    for zone_id, per_day_2024, per_day_2025, share in [(1, 100, 110, 0.95), (2, 50, 52, 0.6), (3, 20, 30, 0.2),
                                                        (4, 2, 6, None), (264, 9, 9, 0.5), (5, 0, 4, 0.0)]:
        if per_day_2024:
            rows.append((2024, zone_id, "all trips", per_day_2024, 1.0))
        rows.append((2025, zone_id, "all trips", per_day_2025, 1.0))
        if share:
            rows.append((2025, zone_id, "pays the charge", per_day_2025 * share, share))
    return pd.DataFrame(rows, columns=["year", "zone_id", "charge_group", "trips_per_day", "share"])


class FindingsDataTest(unittest.TestCase):
    def test_growth_by_payment_gives_the_part_of_the_extra_trips(self):
        growth = findings.growth_by_payment(borough_payment_rows(), daily_average_rows()).set_index("payment")
        self.assertEqual(list(growth.index.astype(str)), PAYMENT_ORDER)
        self.assertAlmostEqual(growth.loc["flex fare", "extra_per_day"], 20.0)
        self.assertAlmostEqual(growth.loc["flex fare", "part_of_growth"], 20 / 30)
        self.assertAlmostEqual(growth.loc["cash", "change"], -0.2)
        self.assertAlmostEqual(growth["share_2025"].sum(), 1.0)

    def test_zone_groups_follow_report_2_table_6_3(self):
        groups = findings.zone_groups_by_charge_share(zone_charge_rows()).set_index("share paying in 2025")
        self.assertEqual(list(groups.index), findings.CHARGE_SHARE_GROUPS + ["all zones"])
        # Zone 264 is not a place and zone 5 has no trips in 2024, so both are left out.
        self.assertEqual(groups.loc["all zones", "zones"], 4)
        self.assertEqual(groups.loc["90% or more", "zones"], 1)
        self.assertAlmostEqual(groups.loc["90% or more", "change"], 0.1)
        # A zone without paying trips belongs to the lowest group.
        self.assertAlmostEqual(groups.loc["below 10%", "per_day_2025"], 6)

    def test_extra_trips_outside_working_hours(self):
        rows = []
        for weekday, hour, extra in [(0, 9, 10.0), (5, 9, 20.0), (2, 23, 10.0)]:
            rows += [(2024, weekday, hour, 100.0), (2025, weekday, hour, 100.0 + extra)]
        cells = pd.DataFrame(rows, columns=["year", "weekday", "hour", "trips_per_day"])
        self.assertAlmostEqual(findings.extra_trips_outside_working_hours(cells), 0.75)

    def test_optimization_changes_compare_the_medians(self):
        runs = pd.DataFrame([("O1", "before", 200.0), ("O1", "after", 150.0)],
                            columns=["optimization", "variant", "median_s"])
        self.assertAlmostEqual(findings.optimization_changes(runs)["O1"], -0.25)


class FindingsChartTest(unittest.TestCase):
    def test_growth_bars_use_the_payment_colours(self):
        growth = findings.growth_by_payment(borough_payment_rows(), daily_average_rows())
        fig = charts.growth_by_payment_chart(growth)
        self.assertEqual(list(fig.data[0].marker.color), [PAYMENT_COLORS[name] for name in PAYMENT_ORDER])

    def test_zone_group_chart_marks_all_zones_as_the_reference(self):
        groups = findings.zone_groups_by_charge_share(zone_charge_rows())
        fig = charts.zone_group_change_chart(groups)
        colors = list(fig.data[0].marker.color)
        self.assertEqual(len(set(colors[:-1])), 1)
        self.assertNotEqual(colors[-1], colors[0])


class DashboardAppTest(unittest.TestCase):
    def test_the_whole_dashboard_runs_on_the_results(self):
        # Catches errors that only show when all tabs run together, such as two charts with the same ID.
        app = AppTest.from_file(str(APP_FILE), default_timeout=60).run()
        self.assertFalse(app.exception, [error.message for error in app.exception])
        self.assertEqual(len(app.tabs), 6)
