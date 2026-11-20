"""Report 3 dashboard (draft): Q3 places and Q4 zone charge.

Run from the repository root: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

import streamlit as st

# Make the repository root (for dashboard.*) and src/ (for hlds.*) importable when Streamlit runs this file.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from dashboard import charts, data, tabs_q1_q2  # noqa: E402

st.set_page_config(page_title="NYC taxi Q1 2024 vs Q1 2025", layout="wide")


@st.cache_data
def load(file_name):
    return data.read_result(file_name)


def is_dark():
    try:
        return st.context.theme.type == "dark"
    except AttributeError:
        return False


def show(fig, table, source):
    st.plotly_chart(fig, theme=None)
    st.caption(f"Source: `results/{source}`")
    with st.expander("Show the numbers"):
        st.dataframe(table, hide_index=True)


def places_tab(dark):
    left, right = st.columns([1, 2])
    end = left.radio("Zones by", ["pickup", "drop-off"], horizontal=True)
    count = right.slider("Number of zones", 5, 20, 10)
    file_name = "q3_pickup_zones.csv" if end == "pickup" else "q3_dropoff_zones.csv"
    zones = data.top_zones(load(file_name), count)
    title = f"The {count} busiest {end} zones of 2025, trips per day in both years"
    show(charts.year_comparison_bars(zones, "zone", title, dark), zones, file_name)
    st.info("The zone results of Q3 are not split by payment group. "
            "The next chart shows flex fare on its own for each borough.")

    shares = data.borough_payment_shares(load("q2_borough_payment.csv"))
    show(charts.borough_payment_chart(shares, dark), shares, "q2_borough_payment.csv")

    flows_file = load("q3_borough_flows.csv")
    flows = data.top_flows(flows_file)
    inside = data.manhattan_internal(flows_file)
    title = "Busiest borough flows other than Manhattan to Manhattan, trips per day"
    show(charts.year_comparison_bars(flows, "flow", title, dark), flows, "q3_borough_flows.csv")
    st.caption(f"Manhattan to Manhattan, left out of the chart: {inside[2024]:,.0f} trips per day in 2024 "
               f"and {inside[2025]:,.0f} in 2025.")


def charge_tab(dark):
    overview = load("q4_overview.csv").set_index(["year", "charge_group"])
    all_2024 = overview.loc[(2024, "all trips")]
    all_2025 = overview.loc[(2025, "all trips")]
    paying = overview.loc[(2025, "pays the charge")]
    not_paying = overview.loc[(2025, "does not pay")]
    first, second, third = st.columns(3)
    first.metric("Trips per day, 5 Jan to 31 Mar 2025", f"{all_2025['trips_per_day']:,.0f}",
                 f"{all_2025['trips_per_day'] / all_2024['trips_per_day'] - 1:+.1%} on 2024")
    second.metric("Trips that pay the zone charge", f"{paying['share']:.0%}")
    third.metric("Median total amount, paying / not paying",
                 f"${paying['median_total_amount']:.2f} / ${not_paying['median_total_amount']:.2f}")
    st.caption("Source: `results/q4_overview.csv`. Both years are counted from 5 January, the day the charge started.")

    by_hour = data.hourly_charge_share(load("q4_by_hour.csv"))
    show(charts.hourly_charge_share_chart(by_hour, dark), by_hour, "q4_by_hour.csv")

    count = st.slider("Number of pickup zones", 5, 25, 15)
    zone_shares = data.busiest_zone_charge_shares(load("q4_by_pickup_zone.csv"), count)
    show(charts.zone_charge_share_chart(zone_shares, dark), zone_shares, "q4_by_pickup_zone.csv")


st.title("NYC yellow taxi trips, Q1 2024 and Q1 2025")
st.caption("Draft dashboard for Report 3. Every chart reads the CSV files in `results/`; Spark does not run here.")

dark = is_dark()
demand, prices, places, charge, speed = st.tabs(
    ["Q1 · Demand", "Q2 · Prices and tips", "Q3 · Places", "Q4 · Zone charge", "Performance"])
with demand:
    tabs_q1_q2.demand_tab(load, show, dark)
with prices:
    tabs_q1_q2.prices_tab(load, show, dark)
with places:
    places_tab(dark)
with charge:
    charge_tab(dark)
with speed:
    tabs_q1_q2.performance_tab(load, show, dark)
