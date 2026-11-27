"""Save the charts of the dashboard as PNG files for Report 3.

Run: python scripts/export_charts.py
Writes reports/report3/figures/*.png: the Q3, Q4, key findings and MLlib zone group charts below and the Q1, Q2 and
performance charts of dashboard/figures_q1_q2.py. Kaleido draws the
pictures with the Chrome or Edge browser installed on the computer.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Make hlds (in src/) and dashboard importable when this file is run as a script.
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from dashboard import charts, data, figures_q1_q2, findings  # noqa: E402
from dashboard.colors import BACKGROUND_COLOR  # noqa: E402

FIGURES_DIR = ROOT / "reports" / "report3" / "figures"
WIDTH = 1000
SCALE = 2


def build_figures():
    flows = data.read_result("q3_borough_flows.csv")
    return {
        "q3_top_pickup_zones": charts.year_comparison_bars(
            data.top_zones(data.read_result("q3_pickup_zones.csv"), 10), "zone",
            "The 10 busiest pickup zones of 2025, trips per day in both years"),
        "q3_borough_payment": charts.borough_payment_chart(
            data.borough_payment_shares(data.read_result("q2_borough_payment.csv"))),
        "q3_borough_flows": charts.year_comparison_bars(
            data.top_flows(flows), "flow",
            "Busiest borough flows other than Manhattan to Manhattan, trips per day"),
        "q4_charge_share_by_hour": charts.hourly_charge_share_chart(
            data.hourly_charge_share(data.read_result("q4_by_hour.csv"))),
        "q4_charge_share_by_zone": charts.zone_charge_share_chart(
            data.busiest_zone_charge_shares(data.read_result("q4_by_pickup_zone.csv"), 15)),
        "findings_growth_by_payment": charts.growth_by_payment_chart(
            findings.growth_by_payment(data.read_result("q2_borough_payment.csv"),
                                       data.read_result("q1_daily_average.csv"))),
        "findings_zone_groups": charts.zone_group_change_chart(
            findings.zone_groups_by_charge_share(data.read_result("q4_by_pickup_zone.csv"))),
        "ml_zone_group_profiles": charts.zone_group_profiles_chart(
            data.read_result("ml_group_profiles.csv"), findings.ZONE_GROUP_NAMES),
    }


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for name, fig in {**build_figures(), **figures_q1_q2.build_figures()}.items():
        # The dashboard uses a transparent background; a report page needs white.
        fig.update_layout(paper_bgcolor=BACKGROUND_COLOR, plot_bgcolor=BACKGROUND_COLOR)
        path = FIGURES_DIR / f"{name}.png"
        fig.write_image(path, width=WIDTH, height=fig.layout.height, scale=SCALE)
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
