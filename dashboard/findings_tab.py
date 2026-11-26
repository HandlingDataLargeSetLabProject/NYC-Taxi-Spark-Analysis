"""The first tab of the dashboard: the key findings of the project and what they mean in practice.

`load` and `show` are the helpers of dashboard/app.py. Every number on this tab is computed from the
CSV files in results/ (dashboard/findings.py), so it changes with them and matches the other tabs.
"""

import streamlit as st

from dashboard import charts, charts_q1_q2, data, data_q1_q2, findings, performance


def _finding(title, fig, table, source, show, text):
    st.subheader(title)
    chart, words = st.columns([3, 2], gap="large")
    with chart:
        # Some of these charts are on their own tab too, so each gets a key of this tab.
        show(fig, table, source, key=f"findings-{title.split('.')[0]}")
    with words:
        st.markdown(text)


def findings_tab(load, show, dark):
    daily_average = load("q1_daily_average.csv")
    per_day = findings.trips_per_day(daily_average)
    growth = findings.growth_by_payment(load("q2_borough_payment.csv"), daily_average)
    flex = growth.set_index("payment").loc["flex fare"]
    card = growth.set_index("payment").loc["credit card"]
    cash = growth.set_index("payment").loc["cash"]
    charge = findings.charge_overview(load("q4_overview.csv"))
    groups = findings.zone_groups_by_charge_share(load("q4_by_pickup_zone.csv")).set_index("share paying in 2025")
    runs = performance.optimization_runs(load("timings_alican.csv"), load("timings_berke.csv"))
    saved = findings.optimization_changes(runs)
    outside_work = findings.extra_trips_outside_working_hours(load("q1_hour_weekday.csv"))
    prices = load("q2_by_payment.csv").set_index(["year", "payment"])
    flex_per_mile = prices.loc[(2025, "flex fare"), "median_price_per_mile"]
    card_per_mile = prices.loc[(2025, "credit card"), "median_price_per_mile"]
    shares = data.borough_payment_shares(load("q2_borough_payment.csv"))
    borough = load("q2_borough_payment.csv").groupby(["pickup_borough", "year"])["trips_per_day"].sum()

    def borough_change(name):
        return borough[(name, 2025)] / borough[(name, 2024)] - 1

    def flex_share(name, year):
        row = shares[(shares["pickup_borough"] == name) & (shares["year"] == year) & (shares["payment"] == "flex fare")]
        return row["share_in_borough"].iloc[0]

    st.markdown("What changed in New York yellow taxi trips between the first quarters of 2024 and 2025, "
                "the first winter with the Manhattan zone charge. Each finding below has one chart; "
                "the other tabs show the details.")
    tiles = st.columns(5)
    tiles[0].metric("Trips per day, Q1 2025", f"{per_day[2025]:,.0f}",
                    f"{per_day[2025] / per_day[2024] - 1:+.1%} on Q1 2024", delta_color="off")
    tiles[1].metric("Flex fare share of trips", f"{flex['share_2025']:.1%}",
                    f"from {flex['share_2024']:.1%} in 2024", delta_color="off")
    tiles[2].metric("Extra trips that are flex fare", f"{flex['part_of_growth']:.1%}",
                    f"{flex['extra_per_day']:+,.0f} of {growth['extra_per_day'].sum():+,.0f} per day",
                    delta_color="off")
    tiles[3].metric("Trips paying the zone charge", f"{charge['share_paying']:.0%}",
                    "2025, from 5 January", delta_color="off")
    tiles[4].metric("Median total price, 2025", f"${charge['median_total_2025']:.2f}",
                    f"{charge['median_total_2025'] - charge['median_total_2024']:+.2f} dollars on 2024",
                    delta_color="off")
    st.divider()

    aligned = data_q1_q2.aligned_daily_trips(load("q1_daily_trips.csv"))
    _finding(
        f"1. {per_day[2025] / per_day[2024] - 1:.0%} more taxi trips per day",
        # The column is narrower than the Q1 tab, so the legend goes under the chart instead of over the title.
        charts_q1_q2.legend_below(charts_q1_q2.daily_trips_chart(aligned, dark)), aligned, "q1_daily_trips.csv",
        show,
        f"**What we see.** {per_day[2024]:,.0f} trips per day in Q1 2024 and {per_day[2025]:,.0f} in Q1 2025. "
        "The weekly rhythm is the same in both years, and 2025 is higher in almost every week. The growth is "
        "largest in the late evening, at night and at weekends (heat maps in the Q1 tab).\n\n"
        "**For the city.** The zone charge started in a winter when taxi demand grew, so the total number of "
        "taxi trips did not fall.\n\n"
        f"**For taxi operators.** There are more trips to serve than a year earlier, and {outside_work:.0%} of the "
        "extra trips fall outside 7:00 to 19:00 on working days.")

    _finding(
        f"2. {flex['part_of_growth']:.1%} of the extra trips are flex fare",
        charts.growth_by_payment_chart(growth, dark), growth, "q2_borough_payment.csv", show,
        f"**What we see.** Flex fare trips grew from {flex['per_day_2024']:,.0f} to {flex['per_day_2025']:,.0f} "
        f"per day. Card trips grew by {card['change']:.0%} and cash trips fell by {-cash['change']:.0%}. "
        "The data only says that these trips have `payment_type` 0; it does not say how they were booked.\n\n"
        "**For the city.** A count of all trips hides this change. Reports on taxi demand should show flex fare "
        "on its own.\n\n"
        f"**For taxi operators.** The growth is in trips with a lower recorded price per mile (median "
        f"\\${flex_per_mile:.2f} against \\${card_per_mile:.2f} for card trips in 2025) and with no recorded tip, so "
        "more trips do not mean the same growth in income.")

    _finding(
        "3. The fastest growth is outside Manhattan",
        charts.borough_payment_chart(shares, dark), shares, "q2_borough_payment.csv", show,
        f"**What we see.** Pickups grew by {borough_change('Brooklyn'):.0%} in Brooklyn and by "
        f"{borough_change('Bronx'):.0%} in the Bronx, against {borough_change('Manhattan'):.0%} in Manhattan. "
        f"They start from a small base, and in 2025 about three in four of them are flex fare "
        f"({flex_share('Brooklyn', 2025):.0%} in Brooklyn, {flex_share('Bronx', 2025):.0%} in the Bronx).\n\n"
        "**For the city.** Yellow taxis now serve a new demand outside Manhattan. Planning for taxi pickups "
        "there should use 2025 data, not the years before.\n\n"
        "**For taxi operators.** The new pickups outside Manhattan are almost all flex fare trips, so this is "
        "where flex fare matters most (Q3 tab for zones and borough flows).")

    _finding(
        "4. No sign that the zone charge lowered taxi demand",
        charts.zone_group_change_chart(groups.reset_index(), dark), groups.reset_index(),
        "q4_by_pickup_zone.csv", show,
        f"**What we see.** {charge['share_paying']:.0%} of the 2025 trips pay the charge. In the "
        f"{groups.loc['90% or more', 'zones']} zones where at least 90% of the trips pay, pickups grew by "
        f"{groups.loc['90% or more', 'change']:.1%}, about as much as all zones "
        f"({groups.loc['all zones', 'change']:+.1%}). The median total price rose by "
        f"\\${charge['median_total_2025'] - charge['median_total_2024']:.2f}.\n\n"
        "**For the city.** In the first winter, taxi trips that start in the zone did not move away from it, "
        "and the charge is small next to the median price of a trip.\n\n"
        "**For taxi operators.** Riders kept taking taxis inside the zone. Two winters are not an experiment: "
        "the growth of flex fare is much larger than any change we can link to the charge (Q4 tab).")

    st.subheader("5. Reading and cleaning the raw files is the main cost of the analysis")
    cells = st.columns(3)
    for cell, (name, label) in zip(cells, performance.TITLES.items()):
        cell.metric(label, f"{saved[name]:+.0%}", f"median time, {performance.OWNERS[name]}'s laptop",
                    delta_color="off")
    st.markdown("Each optimization made its query faster (Performance tab). Caching saved the most seconds because "
                "it avoids reading and cleaning the six raw files again, which takes about 30 seconds every time. "
                "**For the next analysis:** clean once, store the cleaned table as Parquet partitioned by date, "
                "and read only that copy. This dashboard goes one step further and reads only the small result "
                "files, so it runs without Spark.")
    st.caption("All findings compare two winters, January to March 2024 and 2025. They describe what changed "
               "together with the zone charge; they do not show what the charge caused.")
