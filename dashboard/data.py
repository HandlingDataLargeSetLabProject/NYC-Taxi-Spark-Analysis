"""Read the query results from results/ and shape them for the charts.

Spark does not run here: every function works on the small CSV files the
queries already wrote, with pandas.
"""

import pandas as pd

from hlds.paths import RESULTS_DIR

# The four boroughs with enough pickups for a share by payment group (EWR, Staten Island and unknown zones are tiny).
MAIN_BOROUGHS = ["Manhattan", "Queens", "Brooklyn", "Bronx"]


def read_result(file_name):
    return pd.read_csv(RESULTS_DIR / file_name)


def top_zones(zones, count=10, year=2025):
    """Both years of the `count` busiest zones of `year`, busiest first."""
    busiest = zones[zones["year"] == year].nsmallest(count, "rank_in_year")
    order = list(busiest["zone"])
    rows = zones[zones["zone_id"].isin(busiest["zone_id"])].copy()
    rows["zone"] = pd.Categorical(rows["zone"], categories=order, ordered=True)
    return rows.sort_values(["zone", "year"]).reset_index(drop=True)


def top_flows(flows, count=8, year=2025):
    """Both years of the `count` busiest borough flows of `year`, without Manhattan to Manhattan."""
    flows = flows.copy()
    flows["flow"] = flows["pickup_borough"] + " → " + flows["dropoff_borough"]
    # Manhattan to Manhattan has about 85% of all trips; with it on the same axis the other flows are not readable.
    flows = flows[flows["flow"] != "Manhattan → Manhattan"]
    busiest = flows[flows["year"] == year].nlargest(count, "trips_per_day")
    order = list(busiest["flow"])
    rows = flows[flows["flow"].isin(order)].copy()
    rows["flow"] = pd.Categorical(rows["flow"], categories=order, ordered=True)
    return rows.sort_values(["flow", "year"]).reset_index(drop=True)


def manhattan_internal(flows):
    """Trips per day from Manhattan to Manhattan, by year."""
    inside = flows[(flows["pickup_borough"] == "Manhattan") & (flows["dropoff_borough"] == "Manhattan")]
    return dict(zip(inside["year"], inside["trips_per_day"]))


def borough_payment_shares(borough_payment):
    """Share of each payment group among the pickups of the main boroughs, by year."""
    rows = borough_payment[borough_payment["pickup_borough"].isin(MAIN_BOROUGHS)].copy()
    rows["pickup_borough"] = pd.Categorical(rows["pickup_borough"], categories=MAIN_BOROUGHS, ordered=True)
    return rows.sort_values(["pickup_borough", "year", "payment"]).reset_index(drop=True)


def hourly_charge_share(by_hour, year=2025):
    """Share of trips that pay the zone charge in each hour of the day."""
    paying = by_hour[(by_hour["year"] == year) & (by_hour["charge_group"] == "pays the charge")]
    return paying.sort_values("hour").reset_index(drop=True)


def busiest_zone_charge_shares(zone_charge, count=15, year=2025):
    """Share of trips that pay the zone charge in the `count` busiest zones of `year`, busiest first."""
    in_year = zone_charge[zone_charge["year"] == year]
    busiest = in_year[in_year["charge_group"] == "all trips"].nlargest(count, "trips_per_day")
    paying = in_year[in_year["charge_group"] == "pays the charge"][["zone_id", "share"]]
    rows = busiest[["zone_id", "borough", "zone", "trips_per_day"]].merge(paying, on="zone_id", how="left")
    # A zone without any paying trip has no "pays the charge" row.
    rows["share"] = rows["share"].fillna(0.0)
    return rows.reset_index(drop=True)
