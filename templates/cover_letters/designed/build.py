#!/usr/bin/env python3
"""Build a cover letter from a letter module.

    python3 templates/cover_letters/designed/build.py cover_letters/cover_acme_frontend.py

Writes cover_acme_frontend.pdf next to the module. One A4 page, matching the CV design; the
build fails if the letter runs onto a second page or its text layer is unreadable.

The letter module supplies only the letter (company, date, paragraphs). Everything about
the candidate - name, headline, contact details - is read from the CV's content module, so a
changed phone number reaches both documents from one place.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CV_TEMPLATE = HERE.parents[1] / "cv" / "designed"
sys.path.insert(0, str(CV_TEMPLATE))

try:
    import pymupdf as fitz  # noqa: E402
except ImportError:  # older PyMuPDF
    import fitz  # noqa: E402
from jinja2 import Environment, FileSystemLoader, StrictUndefined  # noqa: E402

from theme import css_overrides, load_theme  # noqa: E402
import render as cv_render  # noqa: E402  (the CV template's renderer: PDF printing, verification helpers)

RenderError = cv_render.RenderError


def _contact_line(cv) -> str:
    c = cv.CONTACT
    return "  ·  ".join(x for x in (c["location"], c["phone"], c["email"], c.get("website")) if x)


def _blocks(letter) -> list[dict]:
    """PARAGRAPHS entries are strings, or a list of strings for a bulleted run."""
    blocks = []
    for item in letter.PARAGRAPHS:
        if isinstance(item, (list, tuple)):
            blocks.append({"kind": "points", "points": list(item)})
        else:
            blocks.append({"kind": "para", "text": item})
    return blocks


def render_letter(module_path: Path, out_pdf: Path) -> cv_render.RenderResult:
    letter = cv_render.load_content(module_path)
    cv_module = getattr(letter, "CV_MODULE", None)
    cv = cv_render.load_content(
        Path(cv_module) if cv_module else CV_TEMPLATE / "content_base.py"
    )

    env = Environment(
        loader=FileSystemLoader(HERE),
        undefined=StrictUndefined,
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    html = env.get_template("letter.html.j2").render(
        cv=cv,
        letter=letter,
        blocks=_blocks(letter),
        contact_line=_contact_line(cv),
        theme_css=css_overrides(load_theme()),
    )

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    cv_render.html_to_pdf(html, out_pdf, base_dir=HERE)
    cv_render.stamp_metadata(out_pdf, cv)

    doc = fitz.open(out_pdf)
    pages = doc.page_count
    text = "\n".join(str(page.get_text("text")) for page in doc)
    doc.close()
    flat = " ".join(text.split())

    problems, warnings = [], []
    if pages != 1:
        problems.append(
            f"a cover letter must be exactly 1 page, got {pages}. Cut a paragraph - "
            f"three or four is the working length."
        )
    if "(cid:" in text or "�" in text:
        problems.append("the text layer contains unreadable glyph markers")
    if letter.COMPANY not in flat:
        problems.append(f"the company name {letter.COMPANY!r} is not in the rendered letter")
    if cv.CONTACT["email"] not in flat:
        problems.append("the email is not in the rendered letter")
    if "TODO" in flat:
        problems.append("the letter still contains a TODO placeholder")
    if letter.GREETING.strip().lower().startswith("dear hiring manager"):
        warnings.append("addressed to 'Dear Hiring Manager' - look for a named recipient first")

    if problems:
        raise RenderError("cover letter failed verification:\n  - " + "\n  - ".join(problems))

    return cv_render.RenderResult(pdf=out_pdf, pages=pages, text=text, warnings=warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("module", help="letter module, e.g. cover_letters/cover_acme_frontend.py")
    parser.add_argument("--out-dir", help="write the PDF here instead of next to the module")
    args = parser.parse_args()

    module_path = Path(args.module)
    out_dir = Path(args.out_dir) if args.out_dir else module_path.parent
    target = out_dir / f"{module_path.stem}.pdf"
    try:
        result = render_letter(module_path, target)
    except RenderError as exc:
        print(f"FAIL cover letter: {exc}", file=sys.stderr)
        return 1
    print(f"OK   cover letter -> {target} ({result.pages} page)")
    for warning in result.warnings:
        print(f"     warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
