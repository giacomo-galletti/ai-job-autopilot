"""Unknown or absent CV data must never crash a build.

Covers optional job/school dates (year-only forms), an optional employer, an optional
CONTACT["availability"], empty PROJECTS / REFERENCES sections, and CERTIFICATIONS.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "templates/cv/designed"))
os.environ["JOB_KIT_EXAMPLE_CONTENT"] = "1"  # example content, not profile/

import content_base  # noqa: E402
import render  # noqa: E402
import render_ats  # noqa: E402

try:
    import pymupdf as fitz
except ImportError:  # older PyMuPDF
    import fitz

MODULE = '''
from content_base import *
CONTACT = {k: v for k, v in CONTACT.items() if k != "availability"}
JOBS = [
    {"role": "Designer", "start": (2014,), "end": None, "sentences": ["Did design work."]},
    {"company": "Acme", "role": "Dev", "start": 2016, "end": (2020, None), "sentences": ["Built things."]},
    {"company": "Beta", "role": "Intern", "start": (2013, 9), "end": (2013, 10), "sentences": ["Learned."]},
    {"company": "Gamma", "role": "Analyst", "sentences": ["Undated work."]},
]
EDUCATION = [{"school": "State School", "degree": "Diploma", "location": "", "sentences": ["Studied."]}]
%s
'''


def build(extra=""):
    """Render both PDFs from a module; return (ats_text, designed_text, designed_pages)."""
    with tempfile.TemporaryDirectory() as tmp:
        module = Path(tmp) / "content_unknown.py"
        module.write_text(MODULE % extra)
        ats, designed = Path(tmp) / "ats.pdf", Path(tmp) / "designed.pdf"
        render_ats.render(module, ats)
        result = render.render(module, designed)
        texts = []
        for pdf in (ats, designed):
            with fitz.open(pdf) as doc:
                texts.append("\n".join(str(p.get_text("text")) for p in doc))
        return texts[0], texts[1], result.pages


class DateForms(unittest.TestCase):
    def test_year_only_forms(self):
        for form in ((2014,), 2014, (2014, None)):
            self.assertEqual(content_base.ats_dates(form, None), "2014 - Present")
            self.assertEqual(content_base.figma_dates(form, form), "2014 - 2014")

    def test_year_month_and_missing(self):
        self.assertEqual(content_base.ats_dates((2014, 7), (2016, 1)), "07/2014 - 01/2016")
        self.assertEqual(content_base.figma_dates((2014, 7), None), "Jul 2014 - Present")
        self.assertEqual(content_base.ats_dates(None, None), "")
        self.assertEqual(content_base.figma_dates(None, (2020, None)), "2020")


class BuildsWithUnknownData(unittest.TestCase):
    def test_education_without_school_or_sentences(self):
        ats, designed, pages = build('EDUCATION = [{"degree": "Self-taught"}, {"school": "Only School"}]')
        self.assertEqual(pages, 1)
        for text in (ats, designed):
            self.assertIn("Self-taught", text)
            self.assertIn("Only School", text)
            self.assertNotIn("None", text)

    def test_year_only_missing_company_missing_availability(self):
        ats, designed, pages = build()
        self.assertEqual(pages, 1)
        for text in (ats, designed):
            self.assertNotIn("None", text)
            self.assertIn("2014", text)
            self.assertIn("Acme", text)
            self.assertIn("Designer", text)

    def test_empty_sections_have_no_headings(self):
        ats, designed, _ = build("PROJECTS = []\nREFERENCES = []\nREFERENCES_NOTE = ''\n")
        for text in (ats, designed):
            flat = "".join(text.upper().split())
            self.assertNotIn("PROJECTS", flat)
            self.assertNotIn("REFERENCES", flat)
            self.assertIn("EDUCATION", flat)

    def test_certifications_render_in_both(self):
        extra = (
            "CERTIFICATIONS = [{'name': 'Cloud Practitioner', 'issuer': 'Acme Cert Body', 'year': 2022},"
            " {'name': 'Scrum Master'}]\n"
        )
        ats, designed, pages = build(extra)
        self.assertEqual(pages, 1)
        for text in (ats, designed):
            self.assertIn("Cloud Practitioner", text)
            self.assertIn("Acme Cert Body", text)
            self.assertIn("2022", text)
            self.assertIn("Scrum Master", text)
            self.assertNotIn("None", text)

    def test_no_certification_heading_when_empty(self):
        ats, designed, _ = build()
        for text in (ats, designed):
            self.assertNotIn("CERTIF", "".join(text.upper().split()))

    def test_language_badges_are_consistent(self):
        html = render.render_html(content_base)
        self.assertNotIn('class="flag"', html)


if __name__ == "__main__":
    unittest.main()
