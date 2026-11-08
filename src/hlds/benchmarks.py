"""Shared steps of the before/after measurements: run a case, save its plan, write the times to CSV."""

import contextlib
import csv
import ctypes
import io
import os
import platform
import re
import sys
from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional

from hlds.timing import measure

MACHINE_LABEL = re.compile(r"^[a-z0-9_-]+$")
CSV_COLUMNS = ["date", "optimization", "variant", "median_s", "min_s", "max_s", "runs_s",
               "cpu", "logical_cores", "ram_gb", "spark_version", "driver_memory"]


@dataclass(frozen=True)
class BenchmarkCase:
    """One side of a comparison.

    `run(spark)` runs the query and returns the DataFrame the action ran on, for example `count_rows(trips)`.
    `trips.count()` would not do: it starts a new query, so the plan of `trips` itself is never finished.
    """

    optimization: str
    variant: str
    run: Callable
    reset: Optional[Callable] = None


def measure_case(spark, case, repeats=5, warmup=1):
    """Time the case and return the timing and the DataFrame of the last run, whose plan is the final one."""
    frames = []
    before_each = (lambda: case.reset(spark)) if case.reset else None
    result = measure(f"{case.optimization} {case.variant}", lambda: frames.append(case.run(spark)),
                     repeats=repeats, warmup=warmup, before_each=before_each)
    return result, frames[-1]


def count_rows(frame):
    """Count the rows and return the counting DataFrame, which has run and so has a final plan."""
    counted = frame.groupBy().count()
    counted.collect()
    return counted


def save_plan(frame, folder, optimization, variant):
    # With adaptive query execution the plan only shows the join Spark really used after the query has run.
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        frame.explain(mode="formatted")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{optimization}_{variant}.txt"
    path.write_text(output.getvalue(), encoding="utf-8")
    return path


def timings_file(machine_label, folder):
    if not MACHINE_LABEL.match(machine_label):
        raise ValueError(f"machine label must be lower case letters, digits, '-' or '_', got {machine_label!r}")
    return folder / f"timings_{machine_label}.csv"


def timing_row(optimization, variant, result, machine):
    return {
        "date": date.today().isoformat(),
        "optimization": optimization,
        "variant": variant,
        "median_s": round(result.median, 3),
        "min_s": round(min(result.runs), 3),
        "max_s": round(max(result.runs), 3),
        "runs_s": ";".join(str(round(run, 3)) for run in result.runs),
        **machine,
    }


def append_timing(path, row):
    is_new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def machine_info(spark_version, driver_memory):
    # The computer name is left out on purpose; the CSV file is named after a label we choose ourselves.
    return {
        "cpu": platform.processor() or platform.machine(),
        "logical_cores": os.cpu_count(),
        "ram_gb": round(_total_ram_bytes() / 1024 ** 3, 1),
        "spark_version": spark_version,
        "driver_memory": driver_memory,
    }


def _total_ram_bytes():
    if sys.platform != "win32":
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")

    class MemoryStatus(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
                    ("total_physical", ctypes.c_ulonglong), ("available_physical", ctypes.c_ulonglong),
                    ("total_page_file", ctypes.c_ulonglong), ("available_page_file", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
                    ("available_extended_virtual", ctypes.c_ulonglong)]

    status = MemoryStatus(length=ctypes.sizeof(MemoryStatus))
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return status.total_physical
