"""Dashboard tabs for Q1, Q2 and the performance results.

`load` and `show` are the helpers of dashboard/app.py, so these tabs read and show the data
the same way as the Q3 and Q4 tabs.
"""

import streamlit as st

from dashboard import charts_q1_q2, data_q1_q2, performance


def demand_tab(load, show, dark):
    aligned = data_q1_q2.aligned_daily_trips(load("q1_daily_trips.csv"))
    show(charts_q1_q2.daily_trips_chart(aligned, dark), aligned, "q1_daily_trips.csv")
    st.info("Q1 counts every trip but has no payment type. The Q2 tab shows flex fare on its own.")

    cells = load("q1_hour_weekday.csv")
    grid_2024 = data_q1_q2.hour_weekday_grid(cells, 2024)
    grid_2025 = data_q1_q2.hour_weekday_grid(cells, 2025)
    show(charts_q1_q2.hour_weekday_heatmaps(grid_2024, grid_2025, dark), cells, "q1_hour_weekday.csv")

    change = data_q1_q2.hour_weekday_change(cells)
    table = (change * 100).round(1).rename(columns=dict(enumerate(data_q1_q2.WEEKDAY_NAMES)))
    show(charts_q1_q2.hour_weekday_change_chart(change, dark), table, "q1_hour_weekday.csv")
    st.caption("Dotted boxes: New Year's night (1 January, 00:00 to 04:59) fell on a Monday in 2024 and on a "
               "Wednesday in 2025; between 28% and 64% of the trips in these cells come from that one night.")


def prices_tab(load, show, dark):
    days = data_q1_q2.days_by_year(load("q1_daily_average.csv"))
    hourly = load("q2_by_hour_payment.csv")
    rows = data_q1_q2.trips_per_day_by_hour(hourly, days)
    show(charts_q1_q2.trips_by_hour_payment_chart(rows, dark), rows, "q2_by_hour_payment.csv")
    st.caption("Q2 leaves out the trips with a negative price part, so it has about 3% fewer trips in 2025 "
               "than Q1.")

    card = data_q1_q2.card_by_hour(hourly)
    show(charts_q1_q2.card_by_hour_chart(card, dark), card, "q2_by_hour_payment.csv")
    st.caption("Only card payments record tips. The median tip is 20% in almost every hour, so the chart shows "
               "the mean.")


def performance_tab(load, show, dark):
    runs = performance.optimization_runs(load("timings_alican.csv"), load("timings_berke.csv"))
    show(performance.before_after_chart(runs, dark), runs, "timings_alican.csv and timings_berke.csv")
    st.caption("Each optimization was measured on its owner's laptop. Compare before and after inside one panel, "
               "not the panels with each other.")
