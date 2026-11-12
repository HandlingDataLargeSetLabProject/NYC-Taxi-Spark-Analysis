import importlib.util
import unittest

from hlds.paths import PROJECT_ROOT

SCRIPT = PROJECT_ROOT / "reports" / "report2" / "build_report.py"


def load_script():
    spec = importlib.util.spec_from_file_location("report2_build", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ALICAN = """# Report 2: sections by Alican

## 1. Introduction
*Written by Alican Kaya*
Intro text.

## 12. Problems and solutions
*Written by Alican Kaya*
### 12.1 Slow tests
Our part.
"""

BERKE = """# Report 2: sections by Berke

## 5. Q3 Places and routes
*Written by Berke Arda Türk*
Q3 text.

## 12. Problems and solutions
*Written by Berke Arda Türk*
### 12.5 Shuffle files
His part.
"""


class MergeSectionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = load_script()
        cls.sections = cls.build.merge_sections([ALICAN, BERKE])

    def test_keeps_sections_that_only_one_of_us_wrote(self):
        self.assertEqual(sorted(self.sections), ["1", "12", "5"])

    def test_a_shared_section_has_one_heading(self):
        headings = [line for line in self.sections["12"] if line.startswith("## ")]
        self.assertEqual(headings, ["## 12. Problems and solutions"])

    def test_a_shared_section_puts_alicans_part_first(self):
        text = "\n".join(self.sections["12"])
        self.assertLess(text.index("Our part."), text.index("His part."))
        self.assertIn("*Written by Berke Arda Türk*", text)


class BuildHtmlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = load_script()
        cls.page = cls.build.build_html({})

    def test_missing_sections_get_a_placeholder_with_the_owner(self):
        self.assertIn("8. O2 Broadcast join", self.page)
        self.assertIn("Section written by Berke Arda Türk; not added yet.", self.page)
        self.assertIn("Section written by Alican Kaya; not added yet.", self.page)

    def test_sections_come_in_the_agreed_order(self):
        order = ["1. Introduction", "5. Q3 Places and routes", "12. Problems and solutions",
                 "13. Dashboard tool for Report 3", "14. Team contributions", "References", "Appendix A."]
        positions = [self.page.index(title) for title in order]
        self.assertEqual(positions, sorted(positions))

    def test_contributions_come_from_the_report_2_part(self):
        contributions = self.page.split("14. Team contributions", 1)[1].split("References", 1)[0]
        self.assertIn("Wrote optimization O1", contributions)
        self.assertNotIn("Set up the repository", contributions)


if __name__ == "__main__":
    unittest.main()
