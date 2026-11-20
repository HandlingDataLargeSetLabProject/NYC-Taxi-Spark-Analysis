import unittest
from datetime import date, timedelta

import pandas as pd

from dashboard import charts_q1_q2, data_q1_q2, performance
from dashboard.colors import PAYMENT_COLORS, PAYMENT_ORDER


def daily_rows(start_2024, days_2024, start_2025, days_2025):
    rows = []
    for year, start, count in ((2024, start_2024, days_2024), (2025, start_2025, days_2025)):
        for i in range(count):
            day = start + timedelta(days=i)
            rows.append((year, day.isoformat(), 100 + i))
    return pd.DataFrame(rows, columns=["year", "pickup_date", "trips"])


def hour_weekday_rows():
    rows = []
    for year, trips_per_day in ((2024, 10.0), (2025, 15.0)):
        for weekday in range(7):
            for hour in range(24):
                rows.append((year, weekday, hour, 0, 13, trips_per_day))
    return pd.DataFrame(rows, columns=["year", "weekday", "hour", "trips", "days", "trips_per_day"])


def hour_payment_rows():
    rows = []
    for year in (2024, 2025):
        for hour in (1, 0):
            for payment in reversed(PAYMENT_ORDER):
                rows.append((year, hour, payment, 910 if year == 2024 else 900, 20.0, 12.0, 15.0))
    return pd.DataFrame(rows, columns=["year", "hour", "payment", "trips", "median_speed_mph",
                                       "median_price_per_mile", "mean_tip_pct"])


def timing_rows(optimizations):
    return pd.DataFrame([
        (name, variant, median, f"{median - 1};{median};{median + 1}")
        for name in optimizations
        for variant, median in (("before", 10.0), ("after", 5.0))
    ], columns=["optimization", "variant", "median_s", "runs_s"])


class AlignedDailyTripsTest(unittest.TestCase):
    def setUp(self):
        # 1 January 2024 is a Monday and 1 January 2025 a Wednesday.
        daily = daily_rows(date(2024, 1, 1), 21, date(2025, 1, 1), 19)
        self.aligned = data_q1_q2.aligned_daily_trips(daily)

    def test_pairs_the_same_weekday(self):
        weekdays_2024 = pd.to_datetime(self.aligned["date_2024"]).dt.weekday
        weekdays_2025 = pd.to_datetime(self.aligned["date_2025"]).dt.weekday
        self.assertTrue((weekdays_2024 == weekdays_2025).all())

    def test_first_2025_day_meets_the_first_2024_wednesday(self):
        first = self.aligned.iloc[0]
        self.assertEqual(first["date_2025"], "2025-01-01")
        self.assertEqual(first["date_2024"], "2024-01-03")
        self.assertEqual(first["trips_2024"], 102)

    def test_keeps_only_days_with_a_partner(self):
        self.assertEqual(len(self.aligned), 19)

    def test_weekly_mean_is_centred(self):
        # The trips grow by one per day, so a centred 7-day mean equals the middle day.
        row = self.aligned.iloc[3]
        self.assertAlmostEqual(row["week_mean_2025"], row["trips_2025"])
        self.assertTrue(pd.isna(self.aligned.iloc[0]["week_mean_2025"]))


class HourWeekdayTest(unittest.TestCase):
    def test_grid_has_hours_as_rows_and_weekdays_as_columns(self):
        grid = data_q1_q2.hour_weekday_grid(hour_weekday_rows(), 2025)
        self.assertEqual(grid.shape, (24, 7))
        self.assertEqual(grid.loc[5, 0], 15.0)

    def test_change_is_2025_against_2024(self):
        change = data_q1_q2.hour_weekday_change(hour_weekday_rows())
        self.assertEqual(change.shape, (24, 7))
        self.assertAlmostEqual(change.loc[0, 6], 0.5)


class HourPaymentTest(unittest.TestCase):
    def test_days_by_year_reads_the_quarter_length(self):
        average = pd.DataFrame([(2024, 91, 910, 10.0), (2025, 90, 900, 10.0)],
                               columns=["year", "days", "trips", "trips_per_day"])
        self.assertEqual(data_q1_q2.days_by_year(average), {2024: 91, 2025: 90})

    def test_trips_are_divided_by_the_days_of_their_year(self):
        rows = data_q1_q2.trips_per_day_by_hour(hour_payment_rows(), {2024: 91, 2025: 90})
        self.assertTrue((rows["trips_per_day"] == 10.0).all())

    def test_rows_are_sorted_by_year_hour_and_payment_order(self):
        rows = data_q1_q2.trips_per_day_by_hour(hour_payment_rows(), {2024: 91, 2025: 90})
        first_hour = rows[(rows["year"] == 2024) & (rows["hour"] == 0)]
        self.assertEqual(list(first_hour["payment"]), PAYMENT_ORDER)

    def test_card_rows_only_keep_credit_card(self):
        card = data_q1_q2.card_by_hour(hour_payment_rows())
        self.assertEqual(set(card["payment"]), {"credit card"})
        self.assertEqual(list(card["hour"]), [0, 1, 0, 1])


class PerformanceTest(unittest.TestCase):
    def setUp(self):
        alican = pd.concat([timing_rows(["pilot", "O1"]), timing_rows(["O2"])])
        berke = timing_rows(["pilot", "O2", "O3"])
        self.runs = performance.optimization_runs(alican, berke)

    def test_each_optimization_comes_from_its_owner(self):
        owners = dict(zip(self.runs["optimization"], self.runs["laptop"]))
        self.assertEqual(owners, {"O1": "Alican", "O2": "Berke", "O3": "Berke"})

    def test_pilot_rows_are_left_out(self):
        self.assertEqual(len(self.runs), 6)

    def test_runs_are_read_as_seconds(self):
        o1_before = self.runs[(self.runs["optimization"] == "O1") & (self.runs["variant"] == "before")].iloc[0]
        self.assertEqual(o1_before["runs"], [9.0, 10.0, 11.0])


class ChartsTest(unittest.TestCase):
    def daily_chart(self, dark=False):
        daily = daily_rows(date(2024, 1, 1), 21, date(2025, 1, 1), 19)
        return charts_q1_q2.daily_trips_chart(data_q1_q2.aligned_daily_trips(daily), dark)

    def test_charge_line_is_placed_by_date_text(self):
        # A number of milliseconds is drawn in the computer's time zone, so the line moved between laptops.
        line = self.daily_chart().layout.shapes[0]
        self.assertEqual((line.x0, line.x1), ("2025-01-05", "2025-01-05"))

    def test_charge_line_is_grey_in_both_themes(self):
        for dark in (False, True):
            self.assertEqual(self.daily_chart(dark).layout.shapes[0].line.color, "#898781")

    def test_dark_heat_map_puts_few_trips_on_the_dark_end(self):
        cells = hour_weekday_rows()
        grids = (data_q1_q2.hour_weekday_grid(cells, 2024), data_q1_q2.hour_weekday_grid(cells, 2025))
        light = charts_q1_q2.hour_weekday_heatmaps(*grids).data[0].colorscale
        dark = charts_q1_q2.hour_weekday_heatmaps(*grids, dark=True).data[0].colorscale
        self.assertEqual([color for _, color in dark], [color for _, color in reversed(light)])

    def test_payment_chart_gives_flex_fare_its_own_line(self):
        rows = data_q1_q2.trips_per_day_by_hour(hour_payment_rows(), {2024: 91, 2025: 90})
        fig = charts_q1_q2.trips_by_hour_payment_chart(rows)
        flex = [trace for trace in fig.data if trace.name.startswith("flex fare")]
        self.assertEqual(len(flex), 2)
        self.assertEqual({trace.line.color for trace in flex}, {PAYMENT_COLORS["flex fare"]})
        self.assertEqual({trace.xaxis for trace in flex}, {"x2"})

    def test_payment_panels_have_no_linked_axes(self):
        # Kaleido saved the panels empty when their axes were linked with "matches".
        rows = data_q1_q2.trips_per_day_by_hour(hour_payment_rows(), {2024: 91, 2025: 90})
        layout = charts_q1_q2.trips_by_hour_payment_chart(rows).to_plotly_json()["layout"]
        linked = [name for name, axis in layout.items() if name.startswith(("xaxis", "yaxis")) and "matches" in axis]
        self.assertEqual(linked, [])

    def test_change_map_is_clipped_and_centred_on_zero(self):
        fig = charts_q1_q2.hour_weekday_change_chart(data_q1_q2.hour_weekday_change(hour_weekday_rows()))
        heatmap = fig.data[0]
        self.assertEqual((heatmap.zmin, heatmap.zmid, heatmap.zmax), (-60, 0, 60))

    def test_before_after_chart_shows_every_run(self):
        alican = timing_rows(["O1"])
        berke = timing_rows(["O2", "O3"])
        fig = performance.before_after_chart(performance.optimization_runs(alican, berke))
        dots = [trace for trace in fig.data if trace.type == "scatter"]
        self.assertEqual(sum(len(trace.x) for trace in dots), 18)


if __name__ == "__main__":
    unittest.main()
