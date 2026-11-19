"""Shared chart colours for every Report 3 chart and the dashboard.

Import from here instead of writing colour codes in a chart, so one payment
group or one year has the same colour in all charts:

    from dashboard.colors import PAYMENT_COLORS, PAYMENT_ORDER

The four payment colours are the first four slots of a categorical palette
that was checked for colour blindness (protan, deutan, tritan) in this order,
in light and dark mode. Keep the order: card, flex fare, cash, other.
In light mode cash and other are below 3:1 contrast on white, so every chart
also has a legend, a hover label and a table view.
"""

# Payment groups as they are written in results/*.csv.
PAYMENT_ORDER = ["credit card", "flex fare", "cash", "other"]

PAYMENT_COLORS = {
    "credit card": "#2a78d6",  # blue
    "flex fare": "#eb6834",  # orange
    "cash": "#1baf7a",  # aqua
    "other": "#eda100",  # yellow
}

# The same four hues, stepped for a dark background.
PAYMENT_COLORS_DARK = {
    "credit card": "#3987e5",
    "flex fare": "#d95926",
    "cash": "#199e70",
    "other": "#c98500",
}

# 2024 is the year without the zone charge, so it is the grey baseline and 2025 stands out.
# Violet is not used by any payment group, so a year is never mistaken for a payment group.
YEAR_COLORS = {2024: "#898781", 2025: "#6250d6"}
YEAR_COLORS_DARK = {2024: "#898781", 2025: "#9085e9"}

# Text, grid and background for charts saved as PNG for the report (light mode).
TEXT_COLOR = "#0b0b0b"
MUTED_COLOR = "#52514e"
GRID_COLOR = "#e4e3df"
BACKGROUND_COLOR = "#ffffff"


def payment_colors(dark=False):
    return PAYMENT_COLORS_DARK if dark else PAYMENT_COLORS


def year_colors(dark=False):
    return YEAR_COLORS_DARK if dark else YEAR_COLORS
