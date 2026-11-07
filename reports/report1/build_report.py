"""Build Report 1 as Word and PDF from the Markdown sections in this folder.

The sections are joined in the order of their numbers, the contribution table comes from
docs/contributions.md, and Microsoft Word turns the HTML into .docx and .pdf (see to_word.ps1).
Run: python reports/report1/build_report.py
"""

import html
import re
import struct
import subprocess
from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parents[1]
BUILD_DIR = REPORT_DIR / "build"
SECTION_FILES = ["alican-sections.md", "berke-sections.md"]
CONTRIBUTIONS_FILE = PROJECT_ROOT / "docs" / "contributions.md"
OUTPUT_NAME = "Report1_KayaAlican_TurkBerkeArda"

TITLE = "Report 1: Data preparation and environment"
SUBTITLE = "NYC yellow taxi trips, January to March 2024 and 2025"
COURSE = "Handling Large Data Sets, laboratory project 2 (Apache Spark)"
DATE = "November 2026"
STUDENTS = {"Alican Kaya": "49429", "Berke Arda Türk": "58169"}

# Sections that Berke writes; until berke-sections.md has them, the report shows a placeholder.
EXPECTED_SECTIONS = {
    "4": "Spark environment",
    "5": "Loading the data",
    "7": "Descriptive statistics",
    "8": "Problems and solutions",
    "A": "Appendix A. Code excerpts",
}
REFERENCES = [
    "NYC Taxi and Limousine Commission, TLC Trip Record Data, "
    "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page",
    "NYC Taxi and Limousine Commission, Data Dictionary, Yellow Taxi Trip Records, 18 March 2025, "
    "linked from the page above.",
    "NYC Taxi and Limousine Commission, Taxi Zone Lookup Table (taxi_zone_lookup.csv), linked from the page above.",
    "Apache Spark documentation, https://spark.apache.org/docs/latest/",
]

HEADING = re.compile(r"^(#{2,4}) (.+)$")
SECTION_NUMBER = re.compile(r"^(\d+|[A-Z])[.\s]")
CAPTION = re.compile(r"^(Table|Figure) \d+(\.\d+)*\. ")
IMAGE = re.compile(r"^!\[(.*)\]\((.+)\)$")
BULLET = re.compile(r"^- (.+)$")
NUMBERED = re.compile(r"^\d+\. (.+)$")
# Word reads HTML pixels as 0.75 pt. The text area is about 470 x 700 pt, so pictures stay inside
# 620 px wide and 560 px high (about 60% of the page height, leaving room for the caption).
MAX_IMAGE_WIDTH = 620
MAX_IMAGE_HEIGHT = 560
# Word only keeps a page break from HTML when it is written as a line break with this style.
PAGE_BREAK = "<br clear=all style='page-break-before:always'>"


def split_sections(text):
    """Return {section number: lines}; anything before the first '## ' heading is a note for us, not the report."""
    sections, current = {}, None
    for line in text.splitlines():
        match = HEADING.match(line)
        if match and len(match.group(1)) == 2:
            title = match.group(2).replace("Appendix ", "")
            current = SECTION_NUMBER.match(title).group(1)
            sections[current] = []
        if current is not None:
            sections[current].append(line)
    return sections


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"(https?://[^\s<)]+[^\s<).,])", r'<a href="\1">\1</a>', text)
    for name, number in STUDENTS.items():
        text = text.replace(f"Written by {name}", f"Written by {name} ({number})")
    return text


def fitted_size(png_path):
    """Pixel size for the <img> tag: the picture's own size, made smaller if it is wider or taller than the page."""
    with open(png_path, "rb") as file:
        header = file.read(24)
    width, height = struct.unpack(">II", header[16:24])
    scale = min(1, MAX_IMAGE_WIDTH / width, MAX_IMAGE_HEIGHT / height)
    return round(width * scale), round(height * scale)


def table_html(rows):
    cells = [[cell.strip() for cell in row.strip().strip("|").split("|")] for row in rows]
    header, body = cells[0], cells[2:]
    lines = ["<table>", "<tr>" + "".join(f"<th>{inline(cell)}</th>" for cell in header) + "</tr>"]
    lines += ["<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>" for row in body]
    # Word ignores the CSS margin under a table, so a small empty paragraph keeps the text below apart.
    return "\n".join(lines + ["</table>", '<p class="gap">&nbsp;</p>'])


def list_html(items, tag):
    return f"<{tag}>" + "".join(f"<li>{inline(item)}</li>" for item in items) + f"</{tag}>"


def block_html(block, base_dir):
    first = block[0]
    if first.startswith("```"):
        code = "\n".join(block[1:-1])
        return f"<pre>{html.escape(code, quote=False)}</pre>"
    if first.startswith("|"):
        return table_html(block)
    heading = HEADING.match(first)
    if heading:
        level = len(heading.group(1)) - 1
        return f"<h{level}>{inline(heading.group(2))}</h{level}>"
    image = IMAGE.match(first)
    if image:
        path = (base_dir / image.group(2)).resolve()
        width, height = fitted_size(path)
        return (f'<p class="figure"><img src="{path.as_uri()}" width="{width}" height="{height}" '
                f'alt="{html.escape(image.group(1))}"></p>')
    if BULLET.match(first):
        return list_html([BULLET.match(line).group(1) for line in block], "ul")
    if NUMBERED.match(first):
        return list_html([NUMBERED.match(line).group(1) for line in block], "ol")
    text = " ".join(line.strip() for line in block)
    if CAPTION.match(text):
        return f'<p class="caption">{inline(text)}</p>'
    if text.startswith("Source:"):
        return f'<p class="source">{inline(text)}</p>'
    return f"<p>{inline(text)}</p>"


def blocks(lines):
    """Group lines into blocks: a code fence, a table, a list, a heading or one paragraph."""
    group = []
    in_code = False
    for line in lines:
        if line.startswith("```"):
            group.append(line)
            if in_code:
                yield group
                group = []
            in_code = not in_code
            continue
        if in_code:
            group.append(line)
        elif not line.strip():
            if group:
                yield group
            group = []
        elif HEADING.match(line):
            if group:
                yield group
            yield [line]
            group = []
        else:
            group.append(line)
    if group:
        yield group


def section_html(lines, base_dir):
    return "\n".join(block_html(block, base_dir) for block in blocks(lines))


def placeholder(number, title):
    heading = title if number == "A" else f"{number}. {title}"
    return f"<h1>{inline(heading)}</h1>\n<p class=\"todo\">Section written by Berke Arda Türk; not added yet.</p>"


def contributions_html():
    text = CONTRIBUTIONS_FILE.read_text(encoding="utf-8")
    report_one = text.split("## Report 1", 1)[1].split("## Report 2", 1)[0]
    rows = [line for line in report_one.splitlines() if line.startswith("|")]
    intro = ("<p>Each line is one finished task. The table is copied from <code>docs/contributions.md</code>, "
             "which we filled in when each task was merged.</p>")
    return "<h1>9. Team contributions</h1>\n" + intro + "\n" + table_html(rows)


def references_html():
    return "<h1>References</h1>\n" + list_html(REFERENCES, "ol")


def cover_html():
    students = "".join(f"<p class=\"cover-name\">{name} ({number})</p>" for name, number in STUDENTS.items())
    return (f'<p class="cover-course">{html.escape(COURSE)}</p>'
            f'<p class="cover-title">{html.escape(TITLE)}</p>'
            f'<p class="cover-subtitle">{html.escape(SUBTITLE)}</p>'
            f"{students}"
            f'<p class="cover-date">{DATE}</p>'
            f"{PAGE_BREAK}"
            '<p class="toc-title">Contents</p><p>[[TOC]]</p>')


STYLE = """
@page Section1 { size: 21cm 29.7cm; margin: 2.5cm 2.2cm 2.5cm 2.2cm; }
div.Section1 { page: Section1; }
body { font-family: Calibri, sans-serif; font-size: 11pt; line-height: 1.25; }
h1 { font-size: 16pt; color: #1F3864; margin-top: 18pt; page-break-before: always; }
h2 { font-size: 13pt; color: #1F3864; margin-top: 12pt; }
h3 { font-size: 11pt; color: #1F3864; margin-top: 10pt; }
p { margin: 0 0 6pt 0; text-align: justify; }
code { font-family: Consolas, monospace; font-size: 10pt; }
pre { font-family: Consolas, monospace; font-size: 9pt; background: #F2F2F2; padding: 6pt; }
table { border-collapse: collapse; margin: 4pt 0 10pt 0; }
th, td { border: 1px solid #A6A6A6; padding: 2pt 5pt; font-size: 9.5pt; vertical-align: top; }
th { background: #DCE6F2; }
.caption { font-weight: bold; font-size: 10pt; margin-top: 8pt; text-align: left; }
.source { font-style: italic; font-size: 9pt; color: #404040; }
.figure { text-align: center; }
.todo { color: #C00000; font-style: italic; }
.gap { font-size: 4pt; margin: 0; }
.cover-course { font-size: 13pt; text-align: center; margin-top: 120pt; }
.cover-title { font-size: 24pt; font-weight: bold; color: #1F3864; text-align: center; margin-top: 30pt; }
.cover-subtitle { font-size: 14pt; text-align: center; margin-bottom: 60pt; }
.cover-name { font-size: 13pt; text-align: center; margin: 0; }
.cover-date { font-size: 12pt; text-align: center; margin-top: 40pt; }
.toc-title { font-size: 16pt; font-weight: bold; color: #1F3864; }
"""


def build_html():
    sections = {}
    for name in SECTION_FILES:
        path = REPORT_DIR / name
        if path.exists():
            for number, lines in split_sections(path.read_text(encoding="utf-8")).items():
                sections[number] = (lines, path.parent)
    parts = [cover_html()]
    for number in ["1", "2", "3", "4", "5", "6", "7", "8"]:
        if number in sections:
            parts.append(section_html(*sections[number]))
        else:
            parts.append(placeholder(number, EXPECTED_SECTIONS[number]))
    parts.append(contributions_html())
    parts.append(references_html())
    parts.append(section_html(*sections["A"]) if "A" in sections else placeholder("A", EXPECTED_SECTIONS["A"]))
    body = "\n".join(parts)
    return (f'<html><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>'
            f"<style>{STYLE}</style></head><body><div class=\"Section1\">{body}</div></body></html>")


def main():
    BUILD_DIR.mkdir(exist_ok=True)
    html_file = BUILD_DIR / f"{OUTPUT_NAME}.html"
    html_file.write_text(build_html(), encoding="utf-8")
    subprocess.run(
        ["powershell", "-NoProfile", "-File", str(REPORT_DIR / "to_word.ps1"),
         "-Html", str(html_file), "-Docx", str(BUILD_DIR / f"{OUTPUT_NAME}.docx"),
         "-Pdf", str(BUILD_DIR / f"{OUTPUT_NAME}.pdf"), "-Title", TITLE, "-Author", "; ".join(STUDENTS)],
        check=True,
    )
    print(f"wrote {BUILD_DIR / OUTPUT_NAME}.docx and .pdf")


if __name__ == "__main__":
    main()
