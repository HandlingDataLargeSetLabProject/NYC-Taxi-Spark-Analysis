"""Run the before/after measurements on this computer and write them to results/timings_<machine>.csv.

Run: python scripts/run_benchmarks.py --machine alican [--case pilot] [--repeats 5]
The plan of the last run of each case goes to results/plans/<machine>/.
"""

import argparse
import sys
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hlds.benchmarks import (BenchmarkCase, append_timing, count_rows, machine_info, measure_case, save_plan,
                             timing_row, timings_file)
from hlds.caching import run_q1_and_q2
from hlds.cleaning import clean_trips
from hlds.loading import load_trips
from hlds.paths import RESULTS_DIR
from hlds.session import DRIVER_MEMORY, get_spark


def clean_and_count(spark):
    return count_rows(clean_trips(load_trips(spark)))


def q1_q2_without_cache(spark):
    return run_q1_and_q2(clean_trips(load_trips(spark)))


def q1_q2_with_cache(spark):
    # The time to fill the cache is part of the run, because a real run pays for it too.
    return run_q1_and_q2(clean_trips(load_trips(spark)).cache())


def clear_cache(spark):
    spark.catalog.clearCache()


# Each optimization adds its "before" and "after" cases here (R2-06 to R2-08).
CASES = [
    BenchmarkCase("pilot", "clean_count", clean_and_count, reset=clear_cache),
    BenchmarkCase("O1", "before", q1_q2_without_cache, reset=clear_cache),
    BenchmarkCase("O1", "after", q1_q2_with_cache, reset=clear_cache),
]


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--machine", required=True, help="our own label for this computer, for example alican")
    parser.add_argument("--case", help="run only the cases of this optimization, for example pilot")
    parser.add_argument("--repeats", type=int, default=5)
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    output = timings_file(arguments.machine, RESULTS_DIR)
    cases = [case for case in CASES if arguments.case in (None, case.optimization)]
    if not cases:
        raise SystemExit(f"no case for optimization {arguments.case!r}")

    spark = get_spark("benchmarks")
    spark.sparkContext.setLogLevel("ERROR")
    machine = machine_info(spark.version, DRIVER_MEMORY)
    for case in cases:
        result, frame = measure_case(spark, case, repeats=arguments.repeats)
        save_plan(frame, RESULTS_DIR / "plans" / arguments.machine, case.optimization, case.variant)
        append_timing(output, timing_row(case.optimization, case.variant, result, machine))
        print(f"{case.optimization} {case.variant}: median {result.median:.2f} s over {len(result.runs)} runs")
    spark.stop()


if __name__ == "__main__":
    main()
