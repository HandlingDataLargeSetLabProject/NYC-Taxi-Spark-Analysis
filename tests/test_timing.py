import unittest

from hlds.timing import measure


class FakeClock:
    """Returns 0, 1, 2, ... seconds, so every timed run lasts exactly one tick."""

    def __init__(self, tick=1.0):
        self.now = 0.0
        self.tick = tick

    def __call__(self):
        value = self.now
        self.now += self.tick
        return value


class MeasureTest(unittest.TestCase):
    def test_runs_warmup_plus_repeats_times(self):
        calls = []
        measure("q", lambda: calls.append(1), repeats=3, warmup=2, clock=FakeClock())
        self.assertEqual(len(calls), 5)

    def test_warmup_runs_are_not_recorded(self):
        result = measure("q", lambda: None, repeats=3, warmup=2, clock=FakeClock())
        self.assertEqual(len(result.runs), 3)

    def test_records_each_run_duration(self):
        result = measure("q", lambda: None, repeats=2, warmup=0, clock=FakeClock(tick=0.5))
        self.assertEqual(result.runs, [0.5, 0.5])

    def test_median_with_odd_number_of_runs(self):
        durations = iter([3.0, 1.0, 2.0])
        result = measure("q", lambda: None, repeats=3, warmup=0, clock=_clock_from(durations))
        self.assertEqual(result.median, 2.0)

    def test_median_with_even_number_of_runs(self):
        durations = iter([1.0, 4.0, 2.0, 3.0])
        result = measure("q", lambda: None, repeats=4, warmup=0, clock=_clock_from(durations))
        self.assertEqual(result.median, 2.5)

    def test_keeps_the_name(self):
        result = measure("busiest zones", lambda: None, repeats=1, warmup=0, clock=FakeClock())
        self.assertEqual(result.name, "busiest zones")

    def test_before_each_runs_before_every_run(self):
        order = []
        measure("q", lambda: order.append("run"), repeats=2, warmup=1,
                before_each=lambda: order.append("reset"), clock=FakeClock())
        self.assertEqual(order, ["reset", "run", "reset", "run", "reset", "run"])

    def test_rejects_zero_repeats(self):
        with self.assertRaises(ValueError):
            measure("q", lambda: None, repeats=0)

    def test_rejects_negative_warmup(self):
        with self.assertRaises(ValueError):
            measure("q", lambda: None, repeats=1, warmup=-1)

    def test_error_in_action_is_not_hidden(self):
        def failing_action():
            raise RuntimeError("query failed")

        with self.assertRaises(RuntimeError):
            measure("q", failing_action, repeats=1, warmup=0, clock=FakeClock())


def _clock_from(durations):
    """Clock whose consecutive start/stop pairs differ by the given durations."""
    state = {"now": 0.0, "started": False}

    def clock():
        if state["started"]:
            state["now"] += next(durations)
        state["started"] = not state["started"]
        return state["now"]

    return clock


if __name__ == "__main__":
    unittest.main()
