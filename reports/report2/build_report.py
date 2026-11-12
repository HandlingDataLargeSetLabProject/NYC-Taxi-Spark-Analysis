"""Build Report 2 as Word and PDF from the Markdown sections in this folder.

The Markdown to HTML part and to_word.ps1 come from the Report 1 script. New here: a section number that
both of us write (12, problems and solutions) is joined into one section, Alican's part first.
Run: python reports/report2/build_report.py
"""

import html
import importlib.util
import subprocess
from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parents[1]
REPORT1_DIR = PROJECT_ROOT / "reports" / "report1"
BUILD_DIR = REPORT_DIR / "build"
SECTION_FILES = ["alican-sections.md", "berke-sections.md"]  # in this order inside a shared section
CONTRIBUTIONS_FILE = PROJECT_ROOT / "docs" / "contributions.md"
OUTPUT_NAME = "Report2_KayaAlican_TurkBerkeArda"

TITLE = "Report 2: Data processing, analysis and optimization"
SUBTITLE = "NYC yellow taxi trips, January to March 2024 and 2025"
COURSE = "Handling Large Data Sets, laboratory project 2 (Apache Spark)"
DATE = "December 2026"
ALICAN, BERKE = "Alican Kaya", "Berke Arda Türk"

# The section order we agreed on; a missing section shows a placeholder with its owner.
SECTIONS = [
    ("1", "Introduction", ALICAN),
    ("2", "Environment and measuring method", ALICAN),
    ("3", "Q1 Demand over time", ALICAN),
    ("4", "Q2 Prices, speed and tips", ALICAN),
    ("5", "Q3 Places and routes", BERKE),
    ("6", "Q4 Zone charge", BERKE),
    ("7", "O1 Caching", ALICAN),
    ("8", "O2 Broadcast join", BERKE),
    ("9", "O3 Partitioned storage", BERKE),
    ("10", "Before and after the optimizations", ALICAN),
    ("11", "What the queries show together", ALICAN),
    ("12", "Problems and solutions", f"{ALICAN} and {BERKE}"),
    ("13", "Dashboard tool for Report 3", BERKE),
]
CONTRIBUTIONS_NUMBER = "14"
APPENDIX = ("A", "Appendix A. Code excerpts", BERKE)


def load_report1_builder():
    spec = importlib.util.spec_from_file_location("report1_build", REPORT1_DIR / "build_report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


report1 = load_report1_builder()


def merge_sections(texts):
    """Split each text into numbered sections; a number found in a later text is added below the earlier one."""
    merged = {}
    for text in texts:
        for number, lines in report1.split_sections(text).items():
            if number in merged:
                merged[number] += [""] + lines[1:]  # the heading is already there
            else:
                merged[number] = lines
    return merged


def placeholder(heading, owner):
    return (f"<h1>{report1.inline(heading)}</h1>\n"
            f"<p class=\"todo\">Section written by {html.escape(owner)}; not added yet.</p>")


def section_or_placeholder(sections, number, heading, owner):
    if number in sections:
        return report1.section_html(sections[number], REPORT_DIR)
    return placeholder(heading, owner)


def contributions_html():
    text = CONTRIBUTIONS_FILE.read_text(encoding="utf-8")
    report_two = text.split("## Report 2", 1)[1].split("## Report 3", 1)[0]
    rows = [line for line in report_two.splitlines() if line.startswith("|")]
    intro = ("<p>Each line is one finished task. The table is copied from <code>docs/contributions.md</code>, "
             "which we filled in when each task was merged.</p>")
    return f"<h1>{CONTRIBUTIONS_NUMBER}. Team contributions</h1>\n" + intro + "\n" + report1.table_html(rows)


def cover_html():
    students = "".join(f"<p class=\"cover-name\">{name} ({number})</p>" for name, number in report1.STUDENTS.items())
    return (f'<p class="cover-course">{html.escape(COURSE)}</p>'
            f'<p class="cover-title">{html.escape(TITLE)}</p>'
            f'<p class="cover-subtitle">{html.escape(SUBTITLE)}</p>'
            f"{students}"
            f'<p class="cover-date">{DATE}</p>'
            f"{report1.PAGE_BREAK}"
            '<p class="toc-title">Contents</p><p>[[TOC]]</p>')


def build_html(sections):
    parts = [cover_html()]
    for number, title, owner in SECTIONS:
        parts.append(section_or_placeholder(sections, number, f"{number}. {title}", owner))
    parts.append(contributions_html())
    parts.append(report1.references_html())
    parts.append(section_or_placeholder(sections, *APPENDIX))
    body = "\n".join(parts)
    return (f'<html><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>'
            f"<style>{report1.STYLE}</style></head><body><div class=\"Section1\">{body}</div></body></html>")


def read_sections():
    texts = [(REPORT_DIR / name).read_text(encoding="utf-8") for name in SECTION_FILES if (REPORT_DIR / name).exists()]
    return merge_sections(texts)


def main():
    BUILD_DIR.mkdir(exist_ok=True)
    html_file = BUILD_DIR / f"{OUTPUT_NAME}.html"
    html_file.write_text(build_html(read_sections()), encoding="utf-8")
    subprocess.run(
        ["powershell", "-NoProfile", "-File", str(REPORT1_DIR / "to_word.ps1"),
         "-Html", str(html_file), "-Docx", str(BUILD_DIR / f"{OUTPUT_NAME}.docx"),
         "-Pdf", str(BUILD_DIR / f"{OUTPUT_NAME}.pdf"), "-Title", TITLE, "-Author", "; ".join(report1.STUDENTS)],
        check=True,
    )
    print(f"wrote {BUILD_DIR / OUTPUT_NAME}.docx and .pdf")


if __name__ == "__main__":
    main()
