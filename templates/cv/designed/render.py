"""Render a CV content module to the designed one-page PDF.

    python3 templates/cv/designed/build.py cv/main_acme_frontend.py

The module is any Python file exposing the names in content_base.py (a per-application
module does `from content_base import *` and overrides what the role needs).

Pipeline: Jinja2 -> HTML -> headless Chromium print-to-PDF -> PyMuPDF for metadata and
verification. Chromium is the one in Playwright's cache; no LaTeX, no system browser.

Verification is part of rendering, not an afterthought: the build fails on a second page,
on an unreadable text layer, and on contact details an ATS parser would not find. The
Figma-exported CVs often fail all three of those checks - text there is Type 3 outlines, so
`pdftotext` returns garbled words and phone numbers. This renderer emits real text.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:  # older PyMuPDF
    import fitz
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from theme import css_overrides, load_theme

HERE = Path(__file__).resolve().parent

# Section labels live here rather than in the template so a non-English CV only needs a
# different mapping, not a second template. /apply may pass its own via `labels`.
LABELS_EN = {
    "profile": "Profile",
    "projects": "Projects",
    "experience": "Experience",
    "education": "Education",
    "contact": "Contact",
    "skills": "Skills",
    "languages": "Languages",
    "certifications": "Certifications",
    "references": "References",
}

class RenderError(RuntimeError):
    """A build problem the caller must fix - overflow, unreadable text, missing asset."""


@dataclass
class RenderResult:
    pdf: Path
    pages: int
    text: str
    warnings: list[str]


def load_content(module_path: Path):
    """Import a content module by file path, with the template dir on sys.path.

    Per-application modules do `from content_base import *`, so content_base has to be
    importable no matter where the module file itself lives (normally cv/).
    """
    module_path = module_path.resolve()
    if not module_path.is_file():
        raise RenderError(f"content module not found: {module_path}")
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    if spec is None or spec.loader is None:
        raise RenderError(f"cannot import {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _contact_fields(cv) -> list[dict]:
    """The sidebar's labelled contact rows, in a fixed order."""
    c = cv.CONTACT
    rows = [
        ("Email", c["email"], f"mailto:{c['email']}", None),
        *([("Portfolio", c["website"], f"https://{c['website']}", None)] if c.get("website") else []),
        *([("LinkedIn", c["linkedin"].split("/in/")[-1], f"https://{c['linkedin']}", None)]
          if c.get("linkedin") else []),
        *([("GitHub", "@" + c["github"].rstrip("/").split("/")[-1], f"https://{c['github']}", None)]
          if c.get("github") else []),
        ("Phone", c["phone"], None, None),
        ("Location", c["location"], None, c.get("availability")),
    ]
    return [
        {"label": label, "value": value, "href": href, "extra": extra}
        for label, value, href, extra in rows
    ]


def _cards(cv, assets: Path) -> list[dict]:
    """Project cards: the PROJECTS entries that carry a `card`, in order."""
    cards = []
    for project in getattr(cv, "PROJECTS", None) or []:
        card = project.get("card")
        if not card:
            continue
        image = card.get("image")
        image_path = assets / image if image else None
        cards.append(
            {
                "name": project["name"],
                "title": card.get("title"),
                "description": card["description"],
                "stack": card.get("stack") or [],
                "image": f"assets/{image}" if image_path and image_path.is_file() else None,
            }
        )
    return cards


def render_html(cv, labels: dict | None = None) -> str:
    env = Environment(
        loader=FileSystemLoader(HERE),
        undefined=StrictUndefined,
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("cv.html.j2")
    photo = HERE / "assets" / "photo.jpg"
    html = template.render(
        cv=cv,
        labels={**LABELS_EN, **(labels or {})},
        theme_css=css_overrides(load_theme()),
        cards=_cards(cv, HERE / "assets"),
        contact_fields=_contact_fields(cv),
        photo="assets/photo.jpg" if photo.is_file() else None,
        dates=cv.figma_dates,
        location=cv.figma_location,
        certifications=[cv.certification_line(c) for c in getattr(cv, "CERTIFICATIONS", None) or []],
        references=getattr(cv, "REFERENCES", None) or [],
        references_note=getattr(cv, "REFERENCES_NOTE", "") or "",
    )
    return html


def html_to_pdf(html: str, out_pdf: Path, base_dir: Path | None = None) -> None:
    """Print the HTML with Playwright's Chromium.

    The temporary HTML is written inside `base_dir` (the template folder) so the relative
    URLs in it - fonts/, assets/, the stylesheet - resolve exactly as they do in the source.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - environment problem, not logic
        raise RenderError(
            "playwright is not installed. Run: python3 -m pip install playwright "
            "&& python3 -m playwright install chromium"
        ) from exc

    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", dir=base_dir or HERE, delete=False, encoding="utf-8"
    ) as fh:
        fh.write(html)
        tmp_html = Path(fh.name)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto(tmp_html.as_uri())
            page.emulate_media(media="print")
            # Webfonts are font-display: block; without this the first paint can use a
            # fallback face and every measurement below it shifts.
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(250)
            page.pdf(
                path=str(out_pdf),
                format="A4",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                prefer_css_page_size=True,
            )
            browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)


def stamp_metadata(pdf: Path, cv) -> None:
    doc = fitz.open(pdf)
    meta = getattr(cv, "METADATA", {})
    # A tailored module overrides HEADLINE but not METADATA, so the base title (built from the
    # base headline) would go stale; follow the module's headline unless it set its own title.
    base = sys.modules.get("content_base")
    default_title = f"{cv.NAME} - {base.HEADLINE}" if base is not None and hasattr(base, "HEADLINE") else None
    title = meta.get("title")
    if not title or title == default_title:
        title = f"{cv.NAME} - {cv.HEADLINE}" if getattr(cv, "HEADLINE", "") else f"{cv.NAME} - CV"
    doc.set_metadata(
        {
            "title": title,
            "author": meta.get("author", cv.NAME),
            "subject": meta.get("subject", ""),
            "keywords": meta.get("keywords", ""),
            "creator": "ai-job-autopilot / designed",
            "producer": "Chromium + PyMuPDF",
        }
    )
    tmp = pdf.with_suffix(".tmp.pdf")
    doc.save(tmp)
    doc.close()
    shutil.move(tmp, pdf)


def verify(pdf: Path, cv) -> RenderResult:
    """Fail the build on anything that would reach an employer broken."""
    doc = fitz.open(pdf)
    pages = doc.page_count
    text = "\n".join(str(page.get_text("text")) for page in doc)
    doc.close()

    problems: list[str] = []
    warnings: list[str] = []

    if pages != 1:
        problems.append(
            f"the designed CV must be exactly 1 page, got {pages}. Shorten PROFILE, a job "
            f"paragraph, or a skills group in the content module."
        )

    flat = re.sub(r"\s+", " ", text)
    if "(cid:" in text or "�" in text:
        problems.append("the text layer contains unreadable glyph markers - an ATS would see garbage")

    email = cv.CONTACT["email"]
    if email not in flat:
        problems.append(f"email {email!r} is not in the PDF text layer (invisible to an ATS)")

    phone_digits = re.sub(r"\D", "", cv.CONTACT["phone"])
    text_digits = re.sub(r"\D", "", flat)
    if phone_digits not in text_digits:
        problems.append("the phone number is not in the PDF text layer (invisible to an ATS)")

    if cv.NAME not in flat:
        problems.append(f"the name {cv.NAME!r} is not in the PDF text layer")

    for job in cv.JOBS:
        if job.get("company") and job["company"] not in flat:
            warnings.append(f"company {job['company']!r} missing from the text layer")

    if problems:
        raise RenderError("designed CV failed verification:\n  - " + "\n  - ".join(problems))

    return RenderResult(pdf=pdf, pages=pages, text=text, warnings=warnings)


def render(module_path: Path, out_pdf: Path, labels: dict | None = None) -> RenderResult:
    cv = load_content(module_path)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    html_to_pdf(render_html(cv, labels), out_pdf)
    stamp_metadata(out_pdf, cv)
    return verify(out_pdf, cv)
