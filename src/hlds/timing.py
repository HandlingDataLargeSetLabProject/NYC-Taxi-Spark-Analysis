"""Shared way to time Spark work, so before/after comparisons use the same method."""

import statistics
import time
from dataclasses import dataclass


@dataclass
class TimingResult:
    name: str
    runs: list

    @property
    def median(self):
        return statistics.median(self.runs)


def measure(name, action, repeats=5, warmup=1, before_each=None, clock=time.perf_counter):
    """Run `action` warmup + repeats times and keep the durations of the last `repeats` runs.

    `action` must trigger a Spark action (count, collect, write), otherwise nothing is computed.
    `before_each` runs before every run and is not timed, for example to clear the cache.
    """
    if repeats < 1:
        raise ValueError(f"repeats must be at least 1, got {repeats}")
    if warmup < 0:
        raise ValueError(f"warmup must not be negative, got {warmup}")

    runs = []
    for run in range(warmup + repeats):
        if before_each is not None:
            before_each()
        start = clock()
        action()
        duration = clock() - start
        if run >= warmup:
            runs.append(duration)
    return TimingResult(name, runs)
