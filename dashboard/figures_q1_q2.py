"""The Q1, Q2 and performance charts saved as PNG for Report 3 (used by scripts/export_charts.py)."""

from dashboard import charts_q1_q2, data, data_q1_q2, performance


def build_figures():
    cells = data.read_result("q1_hour_weekday.csv")
    hourly = data.read_result("q2_by_hour_payment.csv")
    days = data_q1_q2.days_by_year(data.read_result("q1_daily_average.csv"))
    runs = performance.optimization_runs(data.read_result("timings_alican.csv"),
                                         data.read_result("timings_berke.csv"))
    return {
        "q1_daily_trips": charts_q1_q2.daily_trips_chart(
            data_q1_q2.aligned_daily_trips(data.read_result("q1_daily_trips.csv"))),
        "q1_hour_weekday": charts_q1_q2.hour_weekday_heatmaps(
            data_q1_q2.hour_weekday_grid(cells, 2024), data_q1_q2.hour_weekday_grid(cells, 2025)),
        "q1_hour_weekday_change": charts_q1_q2.hour_weekday_change_chart(data_q1_q2.hour_weekday_change(cells)),
        "q2_trips_by_hour_payment": charts_q1_q2.trips_by_hour_payment_chart(
            data_q1_q2.trips_per_day_by_hour(hourly, days)),
        "q2_card_by_hour": charts_q1_q2.card_by_hour_chart(data_q1_q2.card_by_hour(hourly)),
        "performance_before_after": performance.before_after_chart(runs),
    }
