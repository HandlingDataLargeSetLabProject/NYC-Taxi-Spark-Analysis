"""Before and after times of the three optimizations (Report 2, Section 10) for Report 3.

Each optimization was measured only on its owner's laptop, so every optimization gets its own
panel and axis: the times of the two laptops must not be compared.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.charts import _style
from dashboard.charts_q1_q2 import legend_below

OWNERS = {"O1": "Alican", "O2": "Berke", "O3": "Berke"}
TITLES = {"O1": "O1 caching (Q1 and Q2)", "O2": "O2 broadcast join", "O3": "O3 partitioned storage"}
VARIANTS = ["before", "after"]

# Not in dashboard/colors.py: light grey before, dark grey after. No hue, because blue already means card payments.
BEFORE_AFTER_COLORS = {"before": "#c3c2b7", "after": "#52514e"}
BEFORE_AFTER_COLORS_DARK = {"before": "#52514e", "after": "#c3c2b7"}
RUN_DOT_COLOR = "#0b0b0b"
RUN_DOT_COLOR_DARK = "#f0efec"


def optimization_runs(alican, berke):
    """The before and after rows of O1 to O3, each from its owner's file, with the single runs in seconds."""
    files = {"Alican": alican, "Berke": berke}
    rows = []
    for optimization, laptop in OWNERS.items():
        timings = files[laptop]
        for variant in VARIANTS:
            row = timings[(timings["optimization"] == optimization) & (timings["variant"] == variant)].iloc[0]
            runs = [float(seconds) for seconds in str(row["runs_s"]).split(";")]
            rows.append((optimization, variant, laptop, float(row["median_s"]), runs))
    return pd.DataFrame(rows, columns=["optimization", "variant", "laptop", "median_s", "runs"])


def before_after_chart(runs, dark=False):
    """One panel per optimization: a bar for the median and a dot for each of the measured runs."""
    colors = BEFORE_AFTER_COLORS_DARK if dark else BEFORE_AFTER_COLORS
    dot_color = RUN_DOT_COLOR_DARK if dark else RUN_DOT_COLOR
    fill_color = RUN_DOT_COLOR if dark else RUN_DOT_COLOR_DARK
    names = list(OWNERS)
    titles = [f"{TITLES[name]}, {OWNERS[name]}'s laptop" for name in names]
    fig = make_subplots(rows=1, cols=len(names), subplot_titles=titles, horizontal_spacing=0.08)
    for column, name in enumerate(names, start=1):
        for variant in VARIANTS:
            row = runs[(runs["optimization"] == name) & (runs["variant"] == variant)].iloc[0]
            fig.add_trace(go.Bar(
                x=[variant], y=[row["median_s"]], name=variant, marker={"color": colors[variant]},
                legendgroup=variant, showlegend=column == 1,
                hovertemplate=f"{name} {variant}<br>median %{{y:.2f}} s<extra></extra>",
            ), row=1, col=column)
            fig.add_trace(go.Scatter(
                x=[variant] * len(row["runs"]), y=row["runs"], mode="markers", name="single run",
                # A filled ring stays visible on the light and on the dark bar.
                marker={"color": fill_color, "size": 9, "line": {"color": dot_color, "width": 1.5}},
                legendgroup="runs", showlegend=column == 1 and variant == "before",
                hovertemplate=f"{name} {variant}<br>one run %{{y:.2f}} s<extra></extra>",
            ), row=1, col=column)
        fig.update_yaxes(title="Seconds" if column == 1 else None, rangemode="tozero", row=1, col=column)
    fig.update_annotations(font={"size": 13})
    title = "Before and after each optimization: median of five runs (bar) and each run (dot)"
    return legend_below(_style(fig, title, dark, height=460))
