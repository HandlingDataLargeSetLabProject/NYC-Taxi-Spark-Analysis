"""Shape the Q1 (demand) and Q2 (prices) results in results/ for the charts.

Like dashboard/data.py, this works on the small CSV files with pandas; Spark does not run here.
"""

import pandas as pd

from dashboard.colors import PAYMENT_ORDER

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]  # 0 is Monday, as in hlds.demand
WEEK = 7

# New Year's night: from 00:00 to 04:59 on 1 January, which was a Monday in 2024 and a Wednesday in 2025.
# A check on the cleaned table showed that 28% to 64% of these cells' trips come from that one night.
NEW_YEAR_CELLS = {2024: (0, range(5)), 2025: (2, range(5))}


def _year_series(daily, year):
    rows = daily[daily["year"] == year].sort_values("pickup_date").reset_index(drop=True)
    rows["week_mean"] = rows["trips"].rolling(WEEK, center=True).mean()
    return rows


def aligned_daily_trips(daily):
    """Each day of 2025 next to the 2024 day with the same weekday, about the same date.

    Lining up the dates (1 January with 1 January) puts a 2024 Monday next to a 2025 Wednesday,
    and the weekly pattern is larger than the change between the years.
    """
    days_2024, days_2025 = _year_series(daily, 2024), _year_series(daily, 2025)
    weekday_2025 = pd.Timestamp(days_2025["pickup_date"][0]).weekday()
    weekday_2024 = pd.Timestamp(days_2024["pickup_date"][0]).weekday()
    shift = (weekday_2025 - weekday_2024) % WEEK
    pairs = min(len(days_2025), len(days_2024) - shift)
    earlier = days_2024.iloc[shift:shift + pairs].reset_index(drop=True)
    later = days_2025.iloc[:pairs]
    return pd.DataFrame({
        "date_2025": later["pickup_date"],
        "date_2024": earlier["pickup_date"],
        "trips_2025": later["trips"],
        "trips_2024": earlier["trips"],
        "week_mean_2025": later["week_mean"],
        "week_mean_2024": earlier["week_mean"],
    })


def hour_weekday_grid(cells, year):
    """Trips per day with the hours as rows and the weekdays (0 is Monday) as columns."""
    in_year = cells[cells["year"] == year]
    return in_year.pivot(index="hour", columns="weekday", values="trips_per_day").sort_index()


def hour_weekday_change(cells):
    """Change of trips per day from 2024 to 2025 in each hour and weekday, as a fraction."""
    return hour_weekday_grid(cells, 2025) / hour_weekday_grid(cells, 2024) - 1


def days_by_year(daily_average):
    """Days in the first quarter of each year (91 in 2024, 90 in 2025), from q1_daily_average.csv."""
    return dict(zip(daily_average["year"], daily_average["days"]))


def trips_per_day_by_hour(rows, days):
    """Trips per day for each year, hour and payment group; `days` maps a year to its days in the quarter."""
    rows = rows.copy()
    rows["trips_per_day"] = rows["trips"] / rows["year"].map(days)
    rows["payment"] = pd.Categorical(rows["payment"], categories=PAYMENT_ORDER, ordered=True)
    rows = rows.sort_values(["year", "hour", "payment"]).reset_index(drop=True)
    rows["payment"] = rows["payment"].astype(str)
    return rows


def card_by_hour(rows):
    """The credit card rows, the only group with tips, by year and hour."""
    card = rows[rows["payment"] == "credit card"]
    return card.sort_values(["year", "hour"]).reset_index(drop=True)
