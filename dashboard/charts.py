"""Plotly charts for Q3 (places) and Q4 (zone charge).

Every function takes a table from dashboard/data.py and returns a Plotly
figure, so the same chart is shown in the dashboard and saved as PNG for the
report (scripts/export_charts.py).
"""

import plotly.graph_objects as go

from dashboard.colors import (
    BACKGROUND_COLOR,
    GRID_COLOR,
    MUTED_COLOR,
    PAYMENT_ORDER,
    TEXT_COLOR,
    payment_colors,
    year_colors,
)

DARK_TEXT_COLOR = "#f0efec"
DARK_MUTED_COLOR = "#c3c2b7"
DARK_GRID_COLOR = "#33332f"


def _style(fig, title, dark=False, height=None):
    text = DARK_TEXT_COLOR if dark else TEXT_COLOR
    muted = DARK_MUTED_COLOR if dark else MUTED_COLOR
    grid = DARK_GRID_COLOR if dark else GRID_COLOR
    fig.update_layout(
        title={"text": title, "x": 0, "xanchor": "left", "font": {"size": 17, "color": text}},
        font={"family": "Segoe UI, Arial, sans-serif", "size": 13, "color": muted},
        # Transparent in the dashboard, so the chart takes the page colour; the PNG export sets white.
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "x": 0, "y": 1.02, "yanchor": "bottom", "title": None},
        margin={"l": 10, "r": 20, "t": 80, "b": 40},
        bargap=0.25,
        bargroupgap=0.08,
        barcornerradius=4,
        hoverlabel={"font": {"size": 13}},
    )
    if height:
        fig.update_layout(height=height)
    fig.update_xaxes(gridcolor=grid, zeroline=False, linecolor=grid, tickfont={"color": muted}, automargin=True)
    fig.update_yaxes(gridcolor=grid, zeroline=False, linecolor=grid, tickfont={"color": muted}, automargin=True)
    return fig


def year_comparison_bars(rows, label_column, title, dark=False):
    """Horizontal bars of trips per day for 2024 and 2025, one row per zone or flow."""
    fig = go.Figure()
    colors = year_colors(dark)
    for year in (2024, 2025):
        in_year = rows[rows["year"] == year]
        fig.add_trace(go.Bar(
            name=str(year),
            y=in_year[label_column].astype(str),
            x=in_year["trips_per_day"],
            orientation="h",
            marker={"color": colors[year]},
            hovertemplate="%{y}<br>" + str(year) + ": %{x:,.0f} trips per day<extra></extra>",
        ))
    order = [str(label) for label in rows[label_column].cat.categories if label in set(rows[label_column])]
    fig.update_layout(barmode="group")
    fig.update_yaxes(categoryorder="array", categoryarray=order, autorange="reversed", showgrid=False)
    fig.update_xaxes(title="Trips per day", tickformat=",")
    return _style(fig, title, dark, height=120 + 46 * len(order))


def borough_payment_chart(shares, dark=False):
    """Share of each payment group among the pickups of each borough, 2024 and 2025 next to each other."""
    fig = go.Figure()
    colors = payment_colors(dark)
    shares = shares.copy()
    shares["label"] = shares["pickup_borough"].astype(str) + " " + shares["year"].astype(str)
    order = list(dict.fromkeys(shares.sort_values(["pickup_borough", "year"])["label"]))
    for payment in PAYMENT_ORDER:
        group = shares[shares["payment"] == payment]
        is_flex = payment == "flex fare"
        fig.add_trace(go.Bar(
            name=payment,
            y=group["label"],
            x=group["share_in_borough"] * 100,
            orientation="h",
            marker={"color": colors[payment], "line": {"color": BACKGROUND_COLOR if not dark else "#0e1117", "width": 2}},
            # Only flex fare gets a number on the bar: it is the group whose share changed most (Report 2, 11.4).
            text=[f"{value:.0f}%" for value in group["share_in_borough"] * 100] if is_flex else None,
            textposition="inside",
            insidetextanchor="middle",
            textfont={"color": "#ffffff"},
            customdata=group["trips_per_day"],
            hovertemplate="%{y}<br>" + payment + ": %{x:.1f}% of pickups (%{customdata:,.0f} per day)<extra></extra>",
        ))
    # Keep the legend in the payment order, and hide a bar number that does not fit flat inside its segment.
    fig.update_layout(barmode="stack", legend_traceorder="normal", uniformtext={"minsize": 12, "mode": "hide"})
    fig.update_traces(textangle=0)
    fig.update_yaxes(categoryorder="array", categoryarray=order, autorange="reversed", showgrid=False)
    fig.update_xaxes(title="Share of pickups in the borough (%)", range=[0, 100], ticksuffix="%")
    return _style(fig, "Pickups by borough and payment group, Q1 2024 and Q1 2025", dark, height=480)


def hourly_charge_share_chart(paying, dark=False):
    """Line of the share of trips that pay the zone charge, by hour of the day (2025 only)."""
    color = year_colors(dark)[2025]
    fig = go.Figure(go.Scatter(
        x=paying["hour"],
        y=paying["share"] * 100,
        mode="lines+markers",
        line={"color": color, "width": 2},
        marker={"color": color, "size": 8, "line": {"color": BACKGROUND_COLOR if not dark else "#0e1117", "width": 2}},
        customdata=paying["trips_per_day"],
        hovertemplate="%{x}:00<br>%{y:.1f}% pay the charge<br>%{customdata:,.0f} paying trips per day<extra></extra>",
    ))
    fig.update_xaxes(title="Pickup hour (New York time)", dtick=2, range=[-0.5, 23.5], showgrid=False)
    fig.update_yaxes(title="Trips that pay the charge (%)", range=[0, 100], ticksuffix="%")
    fig.update_layout(showlegend=False, hovermode="x")
    return _style(fig, "Share of trips that pay the zone charge by hour, 5 Jan to 31 Mar 2025", dark, height=420)


def zone_charge_share_chart(zone_shares, dark=False):
    """Horizontal bars of the share of paying trips in the busiest pickup zones (2025 only)."""
    color = year_colors(dark)[2025]
    fig = go.Figure(go.Bar(
        y=zone_shares["zone"],
        x=zone_shares["share"] * 100,
        orientation="h",
        marker={"color": color},
        text=[f"{value:.0f}%" for value in zone_shares["share"] * 100],
        textposition="outside",
        cliponaxis=False,
        customdata=zone_shares[["borough", "trips_per_day"]],
        hovertemplate="%{y} (%{customdata[0]})<br>%{x:.1f}% pay the charge<br>"
                      "%{customdata[1]:,.0f} pickups per day<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(title="Trips that pay the charge (%)", range=[0, 108], ticksuffix="%", dtick=20)
    fig.update_layout(showlegend=False)
    title = f"Share of paying trips in the {len(zone_shares)} busiest pickup zones, 2025"
    return _style(fig, title, dark, height=120 + 32 * len(zone_shares))
