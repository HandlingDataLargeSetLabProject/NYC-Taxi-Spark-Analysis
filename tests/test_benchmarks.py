import csv
import tempfile
import unittest
from pathlib import Path

from hlds.benchmarks import (BenchmarkCase, append_timing, count_rows, machine_info, measure_case, save_plan,
                             timing_row, timings_file)
from hlds.paths import PROJECT_ROOT
from hlds.timing import TimingResult


class FakeFrame:
    """Stands in for a DataFrame: explain() prints a plan like PySpark does."""

    def __init__(self, plan):
        self.plan = plan
        self.modes = []

    def explain(self, mode):
        self.modes.append(mode)
        print(self.plan)


MACHINE = {"cpu": "Test CPU", "logical_cores": 4, "ram_gb": 8.0, "spark_version": "4.2.0", "driver_memory": "6g"}


class TimingRowTest(unittest.TestCase):
    def test_has_median_min_and_max_of_the_runs(self):
        row = timing_row("O1", "after", TimingResult("q", [3.0, 1.0, 2.0]), MACHINE)
        self.assertEqual((row["median_s"], row["min_s"], row["max_s"]), (2.0, 1.0, 3.0))

    def test_keeps_every_run(self):
        row = timing_row("O1", "after", TimingResult("q", [1.25, 2.5]), MACHINE)
        self.assertEqual(row["runs_s"], "1.25;2.5")

    def test_names_the_optimization_and_variant(self):
        row = timing_row("O2", "before", TimingResult("q", [1.0]), MACHINE)
        self.assertEqual((row["optimization"], row["variant"]), ("O2", "before"))

    def test_includes_the_machine_details(self):
        row = timing_row("O1", "after", TimingResult("q", [1.0]), MACHINE)
        self.assertEqual(row["cpu"], "Test CPU")
        self.assertEqual(row["driver_memory"], "6g")


class TimingsFileTest(unittest.TestCase):
    def test_file_name_uses_the_machine_label(self):
        self.assertEqual(timings_file("alican", Path("out")), Path("out") / "timings_alican.csv")

    def test_rejects_a_label_that_is_not_a_plain_name(self):
        for label in ["", "../x", "Alican Kaya", "a/b"]:
            with self.subTest(label=label), self.assertRaises(ValueError):
                timings_file(label, Path("out"))


class AppendTimingTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "timings_test.csv"

    def tearDown(self):
        self.folder.cleanup()

    def read_rows(self):
        with open(self.path, newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))

    def test_writes_the_header_once(self):
        row = timing_row("O1", "before", TimingResult("q", [1.0]), MACHINE)
        append_timing(self.path, row)
        append_timing(self.path, row)
        lines = self.path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum(line.startswith("date,") for line in lines), 1)

    def test_keeps_earlier_rows(self):
        append_timing(self.path, timing_row("O1", "before", TimingResult("q", [2.0]), MACHINE))
        append_timing(self.path, timing_row("O1", "after", TimingResult("q", [1.0]), MACHINE))
        self.assertEqual([row["variant"] for row in self.read_rows()], ["before", "after"])


class SavePlanTest(unittest.TestCase):
    def test_writes_the_formatted_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            frame = FakeFrame("AdaptiveSparkPlan isFinalPlan=true")
            path = save_plan(frame, Path(folder) / "plans", "O2", "before")
            self.assertEqual(path.read_text(encoding="utf-8").strip(), "AdaptiveSparkPlan isFinalPlan=true")
            self.assertEqual(frame.modes, ["formatted"])

    def test_hides_the_local_project_folder(self):
        plan = f"Location: InMemoryFileIndex [file:/{PROJECT_ROOT.as_posix()}/data/raw/yellow_tripdata_2024-01.parquet]"
        with tempfile.TemporaryDirectory() as folder:
            text = save_plan(FakeFrame(plan), Path(folder), "pilot", "clean_count").read_text(encoding="utf-8")
        self.assertIn("file:/<project>/data/raw/yellow_tripdata_2024-01.parquet", text)
        self.assertNotIn(PROJECT_ROOT.as_posix(), text)

    def test_names_the_file_after_optimization_and_variant(self):
        with tempfile.TemporaryDirectory() as folder:
            path = save_plan(FakeFrame("plan"), Path(folder), "O2", "before")
            self.assertEqual(path.name, "O2_before.txt")


class MeasureCaseTest(unittest.TestCase):
    def test_runs_warmup_plus_repeats_times(self):
        calls = []
        case = BenchmarkCase("O1", "after", lambda spark: calls.append(spark) or FakeFrame("plan"))
        measure_case("spark", case, repeats=2, warmup=1)
        self.assertEqual(calls, ["spark", "spark", "spark"])

    def test_returns_the_frame_of_the_last_run(self):
        frames = iter([FakeFrame("first"), FakeFrame("last")])
        case = BenchmarkCase("O1", "after", lambda spark: next(frames))
        _, frame = measure_case("spark", case, repeats=1, warmup=1)
        self.assertEqual(frame.plan, "last")

    def test_reset_runs_before_every_run(self):
        order = []
        case = BenchmarkCase("O1", "after", lambda spark: order.append("run") or FakeFrame("plan"),
                             reset=lambda spark: order.append("reset"))
        measure_case("spark", case, repeats=1, warmup=1)
        self.assertEqual(order, ["reset", "run", "reset", "run"])


class CountRowsTest(unittest.TestCase):
    """Starts a real local Spark session, because the point is what Spark keeps as the final plan."""

    @classmethod
    def setUpClass(cls):
        from hlds.session import get_spark
        cls.spark = get_spark("hlds-test")

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_returns_a_frame_whose_saved_plan_is_final(self):
        # dropDuplicates needs a shuffle, so adaptive query execution has a plan to finish.
        frame = count_rows(self.spark.range(1000).dropDuplicates())
        with tempfile.TemporaryDirectory() as folder:
            text = save_plan(frame, Path(folder), "test", "final").read_text(encoding="utf-8")
        self.assertIn("isFinalPlan=true", text)

    def test_counts_the_rows(self):
        frame = count_rows(self.spark.range(1000))
        self.assertEqual(frame.collect()[0][0], 1000)


class MachineInfoTest(unittest.TestCase):
    def test_reports_cores_and_memory_but_not_the_computer_name(self):
        info = machine_info("4.2.0", "6g")
        self.assertGreater(info["logical_cores"], 0)
        self.assertGreater(info["ram_gb"], 0)
        self.assertEqual(set(info), {"cpu", "logical_cores", "ram_gb", "spark_version", "driver_memory"})


if __name__ == "__main__":
    unittest.main()
