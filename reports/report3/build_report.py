"""Build Report 3 as Word and PDF from the Markdown sections in this folder.

The Markdown to HTML part and to_word.ps1 come from the Report 1 script, the joining of the two files
from the Report 2 script. New here: every picture gets a numbered caption from its alt text
(Figure 3.1, Figure 3.2, ...), because Word does not show the alt text.
Run: python reports/report3/build_report.py
"""

import html
import importlib.util
import subprocess
from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
BUILD_DIR = REPORT_DIR / "build"
SECTION_FILES = ["alican-sections.md", "berke-sections.md"]
CONTRIBUTIONS_FILE = PROJECT_ROOT / "docs" / "contributions.md"
OUTPUT_NAME = "Report3_KayaAlican_TurkBerkeArda"

TITLE = "Report 3: Visualization, dashboard and summary"
SUBTITLE = "NYC yellow taxi trips, January to March 2024 and 2025"
COURSE = "Handling Large Data Sets, laboratory project 2 (Apache Spark)"
DATE = "December 2026"
ALICAN, BERKE = "Alican Kaya", "Berke Arda Türk"

# The section order we agreed on; a missing section shows a placeholder with its owner.
SECTIONS = [
    ("1", "Introduction", ALICAN),
    ("2", "Workflow of the project", ALICAN),
    ("3", "Charts and what they show", ALICAN),
    ("4", "Dashboard", BERKE),
    ("5", "Key findings and their practical meaning", BERKE),
    ("6", "Limitations and possible improvements", ALICAN),
    ("7", "Optional extension: zone groups with Spark MLlib", BERKE),
    ("8", "Conclusions", ALICAN),
]
CONTRIBUTIONS_NUMBER = "9"
TOOLS = [
    "Apache Spark MLlib guide, part of the Apache Spark documentation above.",
    "pandas 2.3.3, Plotly 7.1.0, Kaleido 1.5.0 and Streamlit 1.67.0, the Python packages of the dashboard, "
    "with the versions fixed in requirements.txt.",
]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


report1 = load_module("report1_build", REPORTS_DIR / "report1" / "build_report.py")
report2 = load_module("report2_build", REPORTS_DIR / "report2" / "build_report.py")


def with_figure_captions(lines, number):
    """Add 'Figure <section>.<n>. <alt text>' as its own paragraph under every picture that has an alt text."""
    result, count = [], 0
    for line in lines:
        result.append(line)
        image = report1.IMAGE.match(line)
        if image and image.group(1):
            count += 1
            result += ["", f"Figure {number}.{count}. {image.group(1)}", ""]
    return result


def section_or_placeholder(sections, number, heading, owner):
    if number in sections:
        return report1.section_html(with_figure_captions(sections[number], number), REPORT_DIR)
    return report2.placeholder(heading, owner)


def contributions_html():
    text = CONTRIBUTIONS_FILE.read_text(encoding="utf-8")
    report_three = text.split("## Report 3", 1)[1]
    rows = [line for line in report_three.splitlines() if line.startswith("|")]
    intro = ("<p>Each line is one finished task. The table is copied from <code>docs/contributions.md</code>, "
             "which we filled in when each task was merged.</p>")
    return f"<h1>{CONTRIBUTIONS_NUMBER}. Team contributions</h1>\n" + intro + "\n" + report1.table_html(rows)


def references_html():
    return "<h1>References</h1>\n" + report1.list_html(report1.REFERENCES + TOOLS, "ol")


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
    parts.append(references_html())
    body = "\n".join(parts)
    return (f'<html><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>'
            f"<style>{report1.STYLE}</style></head><body><div class=\"Section1\">{body}</div></body></html>")


def read_sections():
    texts = [(REPORT_DIR / name).read_text(encoding="utf-8") for name in SECTION_FILES if (REPORT_DIR / name).exists()]
    return report2.merge_sections(texts)


def main():
    BUILD_DIR.mkdir(exist_ok=True)
    html_file = BUILD_DIR / f"{OUTPUT_NAME}.html"
    html_file.write_text(build_html(read_sections()), encoding="utf-8")
    subprocess.run(
        ["powershell", "-NoProfile", "-File", str(REPORTS_DIR / "report1" / "to_word.ps1"),
         "-Html", str(html_file), "-Docx", str(BUILD_DIR / f"{OUTPUT_NAME}.docx"),
         "-Pdf", str(BUILD_DIR / f"{OUTPUT_NAME}.pdf"), "-Title", TITLE, "-Author", "; ".join(report1.STUDENTS)],
        check=True,
    )
    print(f"wrote {BUILD_DIR / OUTPUT_NAME}.docx and .pdf")


if __name__ == "__main__":
    main()
