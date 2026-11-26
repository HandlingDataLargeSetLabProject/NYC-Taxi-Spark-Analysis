"""Report 3 dashboard: key findings, Q1 to Q4 and the performance results.

Run from the repository root: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

import streamlit as st

# Make the repository root (for dashboard.*) and src/ (for hlds.*) importable when Streamlit runs this file.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from dashboard import charts, data, findings_tab, tabs_q1_q2  # noqa: E402
from dashboard.colors import PAYMENT_ORDER, payment_colors, year_colors  # noqa: E402

st.set_page_config(page_title="NYC taxi Q1 2024 vs Q1 2025", layout="wide")


@st.cache_data
def load(file_name):
    return data.read_result(file_name)


def is_dark():
    try:
        return st.context.theme.type == "dark"
    except AttributeError:
        return False


def show(fig, table, source, key=None):
    # A chart shown on two tabs (key findings and its own tab) needs a key, or Streamlit stops with a duplicate ID.
    st.plotly_chart(fig, theme=None, key=key)
    st.caption(f"Source: `results/{source}`")
    with st.expander("Show the numbers"):
        st.dataframe(table, hide_index=True, key=f"{key}-table" if key else None)


def in_short(text):
    st.markdown(f"**In short:** {text}")


def sidebar(dark):
    with st.sidebar:
        st.header("About the data")
        st.markdown(
            "- **Trips:** NYC TLC yellow taxi trip records, January to March of 2024 and 2025, "
            "19.9 million trips after cleaning.\n"
            "- **Zone charge:** the Manhattan congestion relief zone charge started on 5 January 2025. "
            "The Q4 tab compares 5 January to 31 March in both years.\n"
            "- **How it is built:** Spark queries wrote small CSV files to `results/`; this dashboard reads "
            "only those files with pandas, so Spark does not run here.\n"
            "- **Numbers:** every chart has a table under *Show the numbers*.")
        st.subheader("Colours")
        swatch = ('<span style="display:inline-block;width:12px;height:12px;border-radius:3px;'
                  'background:{color};margin-right:6px;vertical-align:-1px"></span>{name}')
        payments = payment_colors(dark)
        years = year_colors(dark)
        st.markdown("<br>".join(swatch.format(color=payments[name], name=name) for name in PAYMENT_ORDER),
                    unsafe_allow_html=True)
        st.markdown("<br>".join(swatch.format(color=years[year], name=year) for year in (2024, 2025)),
                    unsafe_allow_html=True)
        st.caption("Flex fare has its own colour in every chart that compares the years. "
                   "The dark theme is under ⋮ → Settings.")


def places_tab(dark):
    in_short("Most taxi trips start and end in Manhattan, but the fastest growth is in Brooklyn and the "
             "Bronx, where most new pickups are flex fare. The airports did not grow.")
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
    in_short("Three in four trips of 2025 pay the zone charge. The share is lowest early in the morning and "
             "highest at night, and the charged zones grew about as much as the city.")
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
st.caption("Report 3 of the Handling Large Data Sets project (Apache Spark) by Alican Kaya and Berke Arda Türk. "
           "Every chart reads the CSV files in `results/`.")

dark = is_dark()
sidebar(dark)
summary, demand, prices, places, charge, speed = st.tabs(
    ["Key findings", "Q1 · Demand", "Q2 · Prices and tips", "Q3 · Places", "Q4 · Zone charge", "Performance"])
with summary:
    findings_tab.findings_tab(load, show, dark)
with demand:
    in_short("17% more trips per day in 2025, in almost every week. The growth is largest in the late evening, "
             "at night and at weekends.")
    tabs_q1_q2.demand_tab(load, show, dark)
with prices:
    in_short("Flex fare trips almost tripled, most of all in the late evening and at night. Card trips cost "
             "a little more per mile in 2025, and the mean card tip stayed about the same.")
    tabs_q1_q2.prices_tab(load, show, dark)
with places:
    places_tab(dark)
with charge:
    charge_tab(dark)
with speed:
    in_short("All three optimizations made their query faster: caching by a third, the broadcast join by a quarter "
             "and partitioned storage by two fifths.")
    tabs_q1_q2.performance_tab(load, show, dark)
