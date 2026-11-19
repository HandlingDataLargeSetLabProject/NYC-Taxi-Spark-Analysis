"""Plotly charts for Q1 (demand over time) and Q2 (prices, speed and tips).

Every function takes a table from dashboard/data_q1_q2.py and returns a figure, so the same chart
is shown in the dashboard and saved as PNG by scripts/export_charts.py. Payment and year colours
come from dashboard/colors.py; the two heat map scales are defined here.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.charts import _style
from dashboard.colors import PAYMENT_ORDER, payment_colors, year_colors
from dashboard.data_q1_q2 import NEW_YEAR_CELLS, WEEKDAY_NAMES

CHARGE_START = "2025-01-05"
CHANGE_LIMIT = 60  # percent; the colour scale stops here, the hover still shows the real change

# Sequential blue ramp (steps 100 to 700) and a blue-grey-red diverging scale of the same palette.
SEQUENTIAL_BLUE = ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIVERGING = [[0.0, "#2a78d6"], [0.5, "#f0efec"], [1.0, "#e34948"]]
DIVERGING_DARK = [[0.0, "#3987e5"], [0.5, "#383835"], [1.0, "#e66767"]]
MARK_COLOR, MARK_COLOR_DARK = "#0b0b0b", "#f0efec"
YEAR_DASH = {2024: "dash", 2025: "solid"}


def legend_below(fig):
    """Put the legend under the chart, so it does not cover the titles of the panels."""
    fig.update_layout(legend={"y": -0.22, "yanchor": "top"}, margin={"b": 120})
    return fig


def daily_trips_chart(aligned, dark=False):
    """Trips per day from January to March, 2024 lined up by weekday under 2025."""
    colors = year_colors(dark)
    dates = pd.to_datetime(aligned["date_2025"])
    fig = go.Figure()
    for year in (2024, 2025):
        fig.add_trace(go.Scatter(
            x=dates, y=aligned[f"trips_{year}"], name=f"{year}, each day", mode="lines",
            line={"color": colors[year], "width": 1}, opacity=0.35,
            customdata=aligned[f"date_{year}"],
            hovertemplate="%{customdata}: %{y:,.0f} trips<extra></extra>",
        ))
    for year in (2024, 2025):
        fig.add_trace(go.Scatter(
            x=dates, y=aligned[f"week_mean_{year}"], name=f"{year}, 7-day mean", mode="lines",
            line={"color": colors[year], "width": 3},
            customdata=aligned[f"date_{year}"],
            hovertemplate="7 days around %{customdata}: %{y:,.0f} trips per day<extra></extra>",
        ))
    fig.add_vline(x=pd.Timestamp(CHARGE_START).timestamp() * 1000, line={"dash": "dot", "width": 1},
                  annotation_text="zone charge starts (2025)", annotation_position="top right")
    fig.update_xaxes(title="Date in 2025; each 2024 day is the one with the same weekday", tickformat="%d %b",
                     showgrid=False)
    fig.update_yaxes(title="Trips per day", tickformat=",", rangemode="tozero")
    return _style(fig, "Taxi trips per day, January to March, 2024 and 2025", dark, height=460)


def _weekday_heatmap(grid, **settings):
    return go.Heatmap(
        z=grid.values, x=WEEKDAY_NAMES, y=list(grid.index), xgap=2, ygap=2,
        **settings,
    )


def hour_weekday_heatmaps(cells_2024, cells_2025, dark=False):
    """Trips per day in each hour of each weekday, one panel per year on the same colour scale."""
    top = max(cells_2024.values.max(), cells_2025.values.max())
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, subplot_titles=["2024", "2025"],
                        horizontal_spacing=0.04)
    for column, grid in enumerate((cells_2024, cells_2025), start=1):
        fig.add_trace(_weekday_heatmap(
            grid, zmin=0, zmax=top, colorscale=SEQUENTIAL_BLUE, showscale=column == 2,
            colorbar={"title": "Trips per day"},
            hovertemplate="%{x} %{y}:00<br>%{z:,.0f} trips per day<extra></extra>",
        ), row=1, col=column)
    fig.update_yaxes(autorange="reversed", dtick=2, showgrid=False)
    fig.update_yaxes(title="Pickup hour", row=1, col=1)
    fig.update_xaxes(showgrid=False)
    return _style(fig, "Trips per day by pickup hour and weekday", dark, height=620)


def _mark_new_year(fig, dark):
    color = MARK_COLOR_DARK if dark else MARK_COLOR
    for year, (weekday, hours) in NEW_YEAR_CELLS.items():
        fig.add_shape(type="rect", x0=weekday - 0.5, x1=weekday + 0.5, y0=hours[0] - 0.5, y1=hours[-1] + 0.5,
                      line={"color": color, "width": 2, "dash": "dot"})
        fig.add_annotation(x=weekday, y=hours[-1] + 0.5, yanchor="top", showarrow=False,
                           text=f"1 Jan {year}", font={"size": 11, "color": color})


def hour_weekday_change_chart(change, dark=False):
    """Change of trips per day from 2024 to 2025 in each hour and weekday."""
    percent = change * 100
    fig = go.Figure(_weekday_heatmap(
        percent, zmin=-CHANGE_LIMIT, zmid=0, zmax=CHANGE_LIMIT,
        colorscale=DIVERGING_DARK if dark else DIVERGING,
        colorbar={"title": "Change", "ticksuffix": "%"},
        hovertemplate="%{x} %{y}:00<br>%{z:+.1f}% trips per day<extra></extra>",
    ))
    _mark_new_year(fig, dark)
    fig.update_yaxes(title="Pickup hour", autorange="reversed", dtick=2, showgrid=False)
    fig.update_xaxes(showgrid=False)
    title = f"Change of trips per day, 2025 against 2024 (colour scale stops at ±{CHANGE_LIMIT}%)"
    return _style(fig, title, dark, height=620)


def trips_by_hour_payment_chart(rows, dark=False):
    """Trips per day by pickup hour, one panel per payment group, 2024 dashed and 2025 solid."""
    colors = payment_colors(dark)
    # No shared axes: with linked axes Kaleido saved empty panels, and "other" would be a flat line anyway.
    fig = make_subplots(rows=2, cols=2, subplot_titles=PAYMENT_ORDER, vertical_spacing=0.14,
                        horizontal_spacing=0.08)
    for index, payment in enumerate(PAYMENT_ORDER):
        place = {"row": index // 2 + 1, "col": index % 2 + 1}
        for year in (2024, 2025):
            group = rows[(rows["payment"] == payment) & (rows["year"] == year)]
            fig.add_trace(go.Scatter(
                x=group["hour"], y=group["trips_per_day"], name=f"{payment} {year}", mode="lines",
                line={"color": colors[payment], "width": 2, "dash": YEAR_DASH[year]},
                showlegend=False,
                hovertemplate=f"{payment} {year}<br>%{{x}}:00: %{{y:,.0f}} trips per day<extra></extra>",
            ), **place)
    for year in (2024, 2025):
        # Legend entries for the line styles only; the panel titles name the payment groups.
        fig.add_trace(go.Scatter(x=[None], y=[None], name=str(year), mode="lines",
                                 line={"color": "#898781", "width": 2, "dash": YEAR_DASH[year]}))
    fig.update_xaxes(dtick=3, range=[0, 23], showgrid=False)
    fig.update_xaxes(title="Pickup hour", row=2)
    fig.update_yaxes(tickformat=",", rangemode="tozero")
    fig.update_yaxes(title="Trips per day", col=1)
    title = "Trips per day by pickup hour and payment group (2024 dashed, 2025 solid; each panel has its own scale)"
    return legend_below(_style(fig, title, dark, height=660))


def card_by_hour_chart(card, dark=False):
    """Credit card trips by pickup hour: median speed, median price per mile and mean tip, both years."""
    colors = year_colors(dark)
    measures = [("median_speed_mph", "Median speed (mph)", ".1f"),
                ("median_price_per_mile", "Median price per mile ($)", ".2f"),
                ("mean_tip_pct", "Mean tip (%)", ".2f")]
    fig = make_subplots(rows=1, cols=3, subplot_titles=[label for _, label, _ in measures],
                        horizontal_spacing=0.07)
    for column, (measure, label, number) in enumerate(measures, start=1):
        for year in (2024, 2025):
            group = card[card["year"] == year]
            fig.add_trace(go.Scatter(
                x=group["hour"], y=group[measure], name=str(year), mode="lines",
                line={"color": colors[year], "width": 2}, legendgroup=str(year), showlegend=column == 1,
                hovertemplate=f"{year}, %{{x}}:00<br>{label}: %{{y:{number}}}<extra></extra>",
            ), row=1, col=column)
    fig.update_xaxes(title="Pickup hour", dtick=3, range=[0, 23], showgrid=False)
    return legend_below(_style(fig, "Credit card trips by pickup hour, 2024 and 2025", dark, height=440))
