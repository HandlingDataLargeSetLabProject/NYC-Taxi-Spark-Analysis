"""Numbers and tables for the key findings tab of the dashboard.

Every function works on the CSV files in results/, like dashboard/data.py, so the
numbers on the first tab always match the charts in the other tabs and Report 2.
"""

import pandas as pd

from dashboard.colors import PAYMENT_ORDER

# Zone groups of Report 2, Table 6.3: share of a zone's 2025 pickups that pay the charge.
CHARGE_SHARE_GROUPS = ["90% or more", "50% to 90%", "10% to 50%", "below 10%"]
CHARGE_SHARE_EDGES = [0.9, 0.5, 0.1]
# Zones 264 and 265 are "Unknown" and "Outside of NYC", not places.
NOT_PLACES = {264, 265}


def trips_per_day(daily_average):
    """Trips per day of the whole quarter in each year (Q1)."""
    return dict(zip(daily_average["year"], daily_average["trips_per_day"]))


def growth_by_payment(borough_payment, daily_average):
    """Trips per day of each payment group in both years and its part of the growth.

    The trips per day are the sums over all boroughs divided by the days of the quarter, as in
    Report 2, Table 11.1, so the numbers include the pickups in zones 264 and 265.
    """
    days = dict(zip(daily_average["year"], daily_average["days"]))
    trips = borough_payment.groupby(["payment", "year"])["trips"].sum().unstack("year")
    rows = pd.DataFrame({
        "payment": trips.index,
        "per_day_2024": trips[2024].to_numpy() / days[2024],
        "per_day_2025": trips[2025].to_numpy() / days[2025],
    })
    rows["extra_per_day"] = rows["per_day_2025"] - rows["per_day_2024"]
    rows["change"] = rows["per_day_2025"] / rows["per_day_2024"] - 1
    rows["share_2024"] = rows["per_day_2024"] / rows["per_day_2024"].sum()
    rows["share_2025"] = rows["per_day_2025"] / rows["per_day_2025"].sum()
    rows["part_of_growth"] = rows["extra_per_day"] / rows["extra_per_day"].sum()
    rows["payment"] = pd.Categorical(rows["payment"], categories=PAYMENT_ORDER, ordered=True)
    return rows.sort_values("payment").reset_index(drop=True)


def _charge_share_group(share):
    for edge, group in zip(CHARGE_SHARE_EDGES, CHARGE_SHARE_GROUPS):
        if share >= edge:
            return group
    return CHARGE_SHARE_GROUPS[-1]


def zone_groups_by_charge_share(zone_charge):
    """Pickups per day in zone groups by the share of their 2025 trips that pay the charge.

    Same grouping as Report 2, Table 6.3: zones 264 and 265 and zones without trips in one of the
    years are left out, and the last row is all remaining zones together.
    """
    all_trips = zone_charge[zone_charge["charge_group"] == "all trips"]
    per_day = all_trips.pivot_table(index="zone_id", columns="year", values="trips_per_day")
    per_day = per_day.dropna()
    per_day = per_day[~per_day.index.isin(NOT_PLACES)]
    paying = zone_charge[(zone_charge["year"] == 2025) & (zone_charge["charge_group"] == "pays the charge")]
    share = paying.set_index("zone_id")["share"].reindex(per_day.index).fillna(0.0)
    per_day["group"] = share.map(_charge_share_group)
    groups = per_day.groupby("group").agg(zones=(2024, "size"), per_day_2024=(2024, "sum"),
                                          per_day_2025=(2025, "sum"))
    groups = groups.reindex(CHARGE_SHARE_GROUPS)
    groups.loc["all zones"] = [len(per_day), per_day[2024].sum(), per_day[2025].sum()]
    groups["change"] = groups["per_day_2025"] / groups["per_day_2024"] - 1
    groups["zones"] = groups["zones"].astype(int)
    return groups.rename_axis("share paying in 2025").reset_index()


def charge_overview(q4_overview):
    """Share of 2025 trips that pay the charge and the median total price in both years (Q4)."""
    overview = q4_overview.set_index(["year", "charge_group"])
    return {
        "share_paying": overview.loc[(2025, "pays the charge"), "share"],
        "median_total_2024": overview.loc[(2024, "all trips"), "median_total_amount"],
        "median_total_2025": overview.loc[(2025, "all trips"), "median_total_amount"],
    }


def optimization_changes(runs):
    """Change of the median time from before to after for each optimization, from performance.optimization_runs."""
    medians = runs.pivot(index="optimization", columns="variant", values="median_s")
    return (medians["after"] / medians["before"] - 1).to_dict()


def extra_trips_outside_working_hours(hour_weekday, first_hour=7, last_hour=18):
    """Part of the extra trips per week of 2025 that fall outside 7:00 to 19:00 on Monday to Friday (Q1)."""
    cells = hour_weekday.pivot_table(index=["weekday", "hour"], columns="year", values="trips_per_day")
    extra = (cells[2025] - cells[2024]).reset_index(name="extra")
    working = (extra["weekday"] < 5) & extra["hour"].between(first_hour, last_hour)
    return extra.loc[~working, "extra"].sum() / extra["extra"].sum()


# Names of the KMeans zone groups of results/ml_zone_groups.csv (scripts/query_zone_groups.py). The groups are
# numbered by their trips, busiest first, and named after their weekly profile; rename them if the run changes.
ZONE_GROUP_NAMES = {
    1: "all day, Manhattan core and airports",
    2: "weekend nights",
    3: "weekday mornings, residential zones",
}
