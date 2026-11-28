import importlib.util
import unittest

from hlds.paths import PROJECT_ROOT

SCRIPT = PROJECT_ROOT / "reports" / "report3" / "build_report.py"


def load_script():
    spec = importlib.util.spec_from_file_location("report3_build", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SECTION = """## 3. Charts and what they show
*Written by Alican Kaya*

![Trips per day in both years](figures/q1_daily_trips.png)

Source: `results/q1_daily_trips.csv`.

![](figures/q1_hour_weekday.png)
![Heat maps of the change](figures/q1_hour_weekday_change.png)
Text right under the picture.
"""


class FigureCaptionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = load_script()
        cls.lines = cls.build.with_figure_captions(SECTION.splitlines(), "3")

    def test_every_picture_with_a_text_gets_a_numbered_caption(self):
        captions = [line for line in self.lines if line.startswith("Figure ")]
        self.assertEqual(captions, ["Figure 3.1. Trips per day in both years", "Figure 3.2. Heat maps of the change"])

    def test_a_caption_is_its_own_paragraph(self):
        html = self.build.report1.section_html(self.lines, self.build.REPORT_DIR)
        self.assertIn('<p class="caption">Figure 3.2. Heat maps of the change</p>', html)
        self.assertIn("<p>Text right under the picture.</p>", html)


class BuildHtmlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = load_script()
        cls.empty = cls.build.build_html({})
        cls.page = cls.build.build_html(cls.build.read_sections())

    def test_missing_sections_get_a_placeholder_with_the_owner(self):
        self.assertIn("7. Optional extension: zone groups with Spark MLlib", self.empty)
        self.assertIn("Section written by Berke Arda Türk; not added yet.", self.empty)

    def test_sections_come_in_the_agreed_order(self):
        order = ["1. Introduction", "3. Charts and what they show", "4. Dashboard",
                 "6. Limitations and possible improvements", "8. Conclusions", "9. Team contributions",
                 "References"]
        positions = [self.empty.index(title) for title in order]
        self.assertEqual(positions, sorted(positions))

    def test_contributions_come_from_the_report_3_part(self):
        contributions = self.empty.split("9. Team contributions", 1)[1].split("References", 1)[0]
        self.assertIn("Took a full-page screenshot", contributions)
        self.assertNotIn("Wrote optimization O1", contributions)

    def test_the_written_sections_of_both_of_us_are_used(self):
        self.assertIn("What it shows.", self.page)
        self.assertIn("The tabs of the dashboard", self.page)
        self.assertIn("Figure 4.1.", self.page)

    def test_the_figure_numbers_that_section_3_names_point_at_the_findings_charts(self):
        self.assertIn("Figure 5.1. Where the extra trips come from", self.page)
        self.assertIn("Figure 5.2. Change in pickups", self.page)


if __name__ == "__main__":
    unittest.main()
