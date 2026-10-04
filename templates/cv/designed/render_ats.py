"""Render a CV content module to the single-column, ATS-first PDF.

Same page geometry, same Times setting, same flowing layout (blocks measure themselves and
start a new page when the current one is full). The content module and output path are
arguments, and the checks are structural ones that survive tailoring.

This is the variant to put into an ATS: one column, standard fonts, no images, reading order
identical to the visual order.
"""

from __future__ import annotations

from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:  # older PyMuPDF
    import fitz

from render import RenderError, RenderResult, load_content, stamp_metadata

REG_NAME = "Times-Roman"
BOLD_NAME = "Times-Bold"
_reg_font = fitz.Font(fontname=REG_NAME)
_bold_font = fitz.Font(fontname=BOLD_NAME)

PAGE_W, PAGE_H = 594.96, 841.92
MARGIN = 42.75
RIGHT = PAGE_W - MARGIN
BODY = 10.6
LEADING = 13.1
SMALL_GAP = 3.2
SECTION_GAP = 12
BOTTOM = PAGE_H - 46  # last baseline a block may use before the page is full
TOP = 57  # first baseline on a continuation page
BLACK = (0, 0, 0)
SMALL_CAPS = 0.8

HEADINGS = [
    "Profile",
    "Skills",
    "Experience",
    "Projects",
    "Education",
    "Certifications",
    "Languages",
    "References",
]


def text_width(text, bold=False, size=BODY):
    return (_bold_font if bold else _reg_font).text_length(text, fontsize=size)


def wrap(text, width, size=BODY, bold=False):
    lines, current = [], ""
    for word in text.split():
        candidate = word if not current else current + " " + word
        if current and text_width(candidate, bold, size) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_text(page, x, y, text, size=BODY, bold=False, color=BLACK):
    page.insert_text(
        (x, y), text, fontsize=size, fontname=BOLD_NAME if bold else REG_NAME, color=color, overlay=True
    )
    return x + text_width(text, bold, size)


def centered(page, y, text, size=BODY, bold=False):
    draw_text(page, (PAGE_W - text_width(text, bold, size)) / 2, y, text, size, bold)


def small_caps_runs(text, size):
    """(character, font size) pairs: first letter of each word full size, the rest smaller."""
    runs, starts_word = [], True
    for char in text:
        if char.isalpha():
            runs.append((char.upper(), size if starts_word else size * SMALL_CAPS))
            starts_word = False
        else:
            runs.append((char, size))
            starts_word = not char.isalnum()
    return runs


def small_caps_width(text, size):
    return sum(text_width(c, False, s) for c, s in small_caps_runs(text, size))


def draw_small_caps(page, x, y, text, size):
    for char, char_size in small_caps_runs(text, size):
        x = draw_text(page, x, y, char, char_size)
    return x


class Flow:
    """Draws blocks down the page, starting a new one when a block no longer fits."""

    def __init__(self, pdf):
        self.pdf = pdf
        self.page = pdf.new_page(width=PAGE_W, height=PAGE_H)
        self.y = 0.0

    def space_for(self, height):
        if self.y + height > BOTTOM:
            self.page = self.pdf.new_page(width=PAGE_W, height=PAGE_H)
            self.y = TOP

    def paragraph(self, text, width=RIGHT - MARGIN, size=BODY, leading=LEADING, bold=False):
        lines = wrap(text, width, size, bold)
        self.space_for(len(lines) * leading)
        for line in lines:
            draw_text(self.page, MARGIN, self.y, line, size, bold)
            self.y += leading

    def section(self, title, first_block_height=0):
        """A centred small-caps heading with a rule either side; never left alone at a page foot."""
        size = 12.7
        self.space_for(20 + first_block_height)
        title_width = small_caps_width(title, size)
        x = (PAGE_W - title_width) / 2
        line_y = self.y - 4.2
        self.page.draw_line((MARGIN, line_y), (x - 9, line_y), color=BLACK, width=0.8)
        self.page.draw_line((x + title_width + 9, line_y), (RIGHT, line_y), color=BLACK, width=0.8)
        draw_small_caps(self.page, x, self.y, title, size)
        self.y += 20

    def bullet(self, text, width=RIGHT - MARGIN, size=BODY, leading=LEADING):
        lines = wrap(text, width - 19, size)
        self.space_for(len(lines) * leading)
        draw_text(self.page, MARGIN + 5, self.y, "•", size)
        for line in lines:
            draw_text(self.page, MARGIN + 19, self.y, line, size)
            self.y += leading
        self.y += 1.2

    def entry(self, title, dates, company, location, bullets):
        """One job, school or project: kept whole, moved to the next page if it can't be."""
        height = SMALL_GAP + LEADING * (2 if company or location else 1) + 1
        for item in bullets:
            height += len(wrap(item, RIGHT - MARGIN - 19)) * LEADING + 1.2
        self.space_for(height)
        self.y += SMALL_GAP
        x = draw_text(self.page, MARGIN, self.y, title, bold=True)
        if dates:
            draw_text(self.page, x, self.y, ", " + dates)
        self.y += LEADING
        if company or location:  # an unknown employer leaves just the location, or no second line
            x = MARGIN
            if company:
                x = draw_text(self.page, x, self.y, company, bold=True)
            if location:
                draw_text(self.page, x, self.y, (" - " if company else "") + location)
            self.y += LEADING
        self.y += 1
        for item in bullets:
            self.bullet(item)
        self.y += 2.5

    def two_columns(self, left, right, row_height=16):
        gap = 22
        column_width = (RIGHT - MARGIN - gap) / 2
        rows = max(len(left), len(right))
        self.space_for(rows * row_height)
        for index in range(rows):
            if index < len(left):
                draw_text(self.page, MARGIN, self.y, "•")
                draw_text(self.page, MARGIN + 14, self.y, left[index])
            if index < len(right):
                right_x = MARGIN + column_width + gap
                draw_text(self.page, right_x, self.y, "•")
                draw_text(self.page, right_x + 14, self.y, right[index])
            self.y += row_height


def _layout(pdf, cv) -> None:
    flow = Flow(pdf)
    centered(flow.page, 59, cv.NAME, 25.5)
    centered(flow.page, 79, cv.HEADLINE, 12)
    c = cv.CONTACT
    centered(
        flow.page,
        97,
        "  |  ".join([" · ".join(x for x in (c["location"], c.get("availability")) if x), c["phone"], c["email"]]),
        BODY,
    )
    links = [f"Portfolio: {c['website']}" if c.get("website") else None, c.get("linkedin"), c.get("github")]
    links = [x for x in links if x]
    if links:
        centered(flow.page, 111, "  |  ".join(links), BODY)
    flow.y = 136

    flow.section("Profile")
    flow.paragraph(cv.PROFILE)
    flow.y += SECTION_GAP

    flow.section("Skills", first_block_height=len(cv.ATS_SKILLS_LEFT) * 16)
    flow.two_columns(cv.ATS_SKILLS_LEFT, cv.ATS_SKILLS_RIGHT)
    flow.y += SECTION_GAP - 2

    flow.section("Experience", first_block_height=LEADING * 4)
    for job in cv.JOBS:
        flow.entry(
            job["role"],
            cv.ats_dates(job.get("start"), job.get("end")),
            job.get("company"),
            cv.ats_location(job),
            cv.ats_sentences(job),
        )

    projects = getattr(cv, "PROJECTS", None) or []
    if projects:
        flow.y += 3
        flow.section("Projects", first_block_height=LEADING * 4)
        for project in projects:
            flow.entry(project["name"], "", project["descriptor"], "", project["bullets"])

    flow.y += 3
    flow.section("Education", first_block_height=LEADING * 3)
    for school in cv.EDUCATION:
        flow.entry(
            school.get("degree") or school.get("school") or "",
            cv.ats_dates(school.get("start"), school.get("end")),
            school.get("school", "") if school.get("degree") else "",
            school.get("location"),
            school.get("sentences", []),
        )

    certs = [cv.certification_line(c) for c in getattr(cv, "CERTIFICATIONS", None) or []]
    if certs:
        flow.y += 4
        flow.section("Certifications", first_block_height=16)
        half = (len(certs) + 1) // 2
        flow.two_columns(certs[:half], certs[half:])

    flow.y += 4
    flow.section("Languages", first_block_height=16)
    labels = [f"{name} ({level})" for name, level in cv.LANGUAGES]
    half = (len(labels) + 1) // 2
    flow.two_columns(labels[:half], labels[half:])

    refs = getattr(cv, "REFERENCES", None) or []
    note = getattr(cv, "REFERENCES_NOTE", "") or ""
    if refs or note:
        flow.y += SECTION_GAP - 2
        # Reserve the whole block so the heading, names and note stay together on one page.
        flow.section("References", first_block_height=LEADING * (len(refs) + len(wrap(note, RIGHT - MARGIN))))
        for ref in refs:
            x = draw_text(flow.page, MARGIN, flow.y, ref["name"], bold=True)
            draw_text(flow.page, x, flow.y, " - " + ref["role"])
            flow.y += LEADING
        if note:
            flow.paragraph(note)


def _verify(pdf_path: Path, cv) -> RenderResult:
    doc = fitz.open(pdf_path)
    page_texts = [str(page.get_text("text")) for page in doc]
    pages = doc.page_count
    doc.close()
    text = "\n".join(page_texts)
    joined = " ".join(text.split())

    def flat(line: str) -> str:
        """Headings are drawn glyph by glyph in small caps, so ignore case and spacing."""
        return "".join(line.split()).upper()

    # Optional sections only count when the content has them; an empty one draws no heading.
    optional = {
        "Projects": getattr(cv, "PROJECTS", None),
        "Certifications": getattr(cv, "CERTIFICATIONS", None),
        "References": getattr(cv, "REFERENCES", None) or getattr(cv, "REFERENCES_NOTE", None),
    }
    wanted = [flat(h) for h in HEADINGS if optional.get(h, True)]
    order = [flat(l) for pt in page_texts for l in pt.splitlines() if flat(l) in wanted]

    problems, warnings = [], []
    if pages > 2:
        problems.append(f"the ATS CV must fit 1-2 pages, got {pages}. Shorten the profile or a job's bullets.")
    if order != wanted:
        problems.append(f"section headings missing or out of order: {order}")
    if "(cid:" in text or "�" in text:
        problems.append("the text layer contains unreadable glyph markers - an ATS would see garbage")
    if cv.CONTACT["email"] not in joined:
        problems.append("the email is not in the text layer")
    if cv.NAME not in joined:
        problems.append("the name is not in the text layer")
    for job in cv.JOBS:
        if job.get("company") and job["company"] not in joined:
            problems.append(f"job {job['company']!r} is missing from the rendered CV")
    if page_texts and not any(flat(l) == "SKILLS" for l in page_texts[0].splitlines()):
        warnings.append("Skills slipped off page 1")
    for job in cv.JOBS:
        if "Internship" in job["role"] or not job.get("company"):
            continue
        if page_texts and job["company"] not in " ".join(page_texts[0].split()):
            warnings.append(f"{job['company']} slipped off page 1")

    if problems:
        raise RenderError("ATS CV failed verification:\n  - " + "\n  - ".join(problems))

    return RenderResult(pdf=pdf_path, pages=pages, text=text, warnings=warnings)


def render(module_path: Path, out_pdf: Path) -> RenderResult:
    cv = load_content(module_path)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf = fitz.open()
    try:
        _layout(pdf, cv)
        pdf.save(out_pdf, garbage=4, deflate=True)
    finally:
        if not pdf.is_closed:
            pdf.close()
    stamp_metadata(out_pdf, cv)
    return _verify(out_pdf, cv)
