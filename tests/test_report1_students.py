import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from hlds.paths import PROJECT_ROOT

SCRIPT = PROJECT_ROOT / "reports" / "report1" / "build_report.py"


def load_script():
    spec = importlib.util.spec_from_file_location("report1_build", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StudentNumbersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = load_script()

    def test_without_the_local_file_only_the_names_are_shown(self):
        students = self.build.load_students(Path(tempfile.gettempdir()) / "no-such-student-file.json")
        self.assertEqual(students, {"Alican Kaya": "", "Berke Arda Türk": ""})
        self.assertEqual(self.build.name_with_number("Alican Kaya", students), "Alican Kaya")

    def test_the_local_file_adds_the_numbers(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "student_numbers.json"
            path.write_text(json.dumps({"Alican Kaya": "111", "Berke Arda Türk": "222"}), encoding="utf-8")
            students = self.build.load_students(path)
        self.assertEqual(self.build.name_with_number("Berke Arda Türk", students), "Berke Arda Türk (222)")

    def test_no_student_number_is_written_in_the_repository_files(self):
        for path in [SCRIPT, PROJECT_ROOT / "reports" / "report1" / "alican-sections.md"]:
            self.assertNotRegex(path.read_text(encoding="utf-8"), r"\(\d{5}\)|\"\d{5}\"")


if __name__ == "__main__":
    unittest.main()
