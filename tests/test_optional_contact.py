"""CONTACT website/linkedin/github are optional: contact blocks build without them."""
import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CV_TEMPLATE = ROOT / "templates/cv/designed"
sys.path.insert(0, str(CV_TEMPLATE))

os.environ["JOB_KIT_EXAMPLE_CONTENT"] = "1"  # example content, not profile/

import render  # noqa: E402

MINIMAL = {
    "location": "Example City",
    "availability": "Open to remote work",
    "phone": "+00 000 000 000",
    "email": "alex@example.com",
}


def _load_cover_build():
    spec = importlib.util.spec_from_file_location(
        "cover_build_under_test", ROOT / "templates/cover_letters/designed/build.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OptionalContact(unittest.TestCase):
    def test_cv_sidebar_omits_missing_links(self):
        cv = types.SimpleNamespace(CONTACT=dict(MINIMAL))
        labels = [f["label"] for f in render._contact_fields(cv)]
        self.assertEqual(labels, ["Email", "Phone", "Location"])

    def test_cv_sidebar_keeps_given_links(self):
        cv = types.SimpleNamespace(CONTACT={**MINIMAL, "github": "github.com/alex"})
        labels = [f["label"] for f in render._contact_fields(cv)]
        self.assertIn("GitHub", labels)
        self.assertNotIn("LinkedIn", labels)

    def test_cover_contact_line_without_website(self):
        build = _load_cover_build()
        line = build._contact_line(types.SimpleNamespace(CONTACT=dict(MINIMAL)))
        self.assertEqual(line, "Example City  ·  +00 000 000 000  ·  alex@example.com")

    def test_ats_resume_renders_without_links(self):
        import tempfile

        import render_ats

        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "content_no_links.py"
            module.write_text(f"from content_base import *\nCONTACT = {MINIMAL!r}\n")
            out = Path(tmp) / "out.pdf"
            render_ats.render(module, out)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
