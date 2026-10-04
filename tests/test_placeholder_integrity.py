"""Guards for placeholder integrity.

Personal data lives in the gitignored profile/ folder, so every tracked template must carry only
placeholders. CI runs this test file (python-tests job), so the sentinels asserted here are the
placeholder-integrity check.

Each sentinel has to sit IN the data /onboard replaces, not in a header comment the model may
leave untouched. These tests pin (a) that the sentinels exist in the pristine tracked files,
(b) that simulating the personalization edit destroys at least one sentinel per file, i.e. the
guard would fire on committed personal data, and (c) that profile.example/ keeps its placeholder
shape (no file there may hold real-looking contact data).
"""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLE_CV = REPO / "cv" / "main_example.tex"
PROFILE_EXAMPLE = REPO / "profile.example"
PROFILE = PROFILE_EXAMPLE / "profile.md"

# The literal sentinel strings (unescaped) that ci.yml's grep patterns match.
CV_SENTINELS = ["\\name{[First]}{[Last]}", "\\email{[your.email@example.com]}"]
PROFILE_SENTINELS = ["[YOUR_EMAIL]", "[FULL_NAME]", "[YOUR_PHONE]"]


def personalize_cv(text: str) -> str:
    """Apply /setup Step 3.8's documented edit: replace placeholder personal
    data with a real name and contact info. Header comments and hyperref
    metadata are not personal data, so they are deliberately left alone -
    that is exactly why a comment-located sentinel guards nothing."""
    return (
        text.replace("\\name{[First]}{[Last]}", "\\name{Jane}{Doe}")
        .replace("[Your Address, City, Country]", "Some Street 1, Aarhus, Denmark")
        .replace("[+XX XXXXXXXXXX]", "+45 12345678")
        .replace("[your.email@example.com]", "jane.doe@example.org")
    )


class TestCvSentinelsAreDataLocated(unittest.TestCase):
    def setUp(self):
        self.cv = EXAMPLE_CV.read_text(encoding="utf-8")

    def test_pristine_cv_carries_both_sentinels(self):
        for sentinel in CV_SENTINELS:
            self.assertIn(sentinel, self.cv)

    def test_setup_edit_destroys_the_sentinels(self):
        personalized = personalize_cv(self.cv)
        self.assertNotEqual(personalized, self.cv, "the simulated /setup edit must change the file")
        surviving = [s for s in CV_SENTINELS if s in personalized]
        self.assertEqual(
            surviving,
            [],
            "a sentinel survived the documented /setup personalization - the "
            f"guard would pass on committed personal data: {surviving}",
        )


class TestProfileExampleStaysPlaceholderOnly(unittest.TestCase):
    def test_every_template_file_exists(self):
        for name in ("profile.md", "behavioral.md", "deal-breakers.md", "forms.md",
                     "portals.md", "search-queries.md", "README.md"):
            self.assertTrue((PROFILE_EXAMPLE / name).is_file(), name)

    def test_pristine_profile_carries_the_sentinels(self):
        text = PROFILE.read_text(encoding="utf-8")
        for sentinel in PROFILE_SENTINELS:
            self.assertIn(sentinel, text)

    def test_filling_the_identity_destroys_the_sentinels(self):
        filled = (
            PROFILE.read_text(encoding="utf-8")
            .replace("[FULL_NAME]", "Alex Example")
            .replace("[YOUR_EMAIL]", "alex@example.org")
            .replace("[YOUR_PHONE]", "+1 555 0100")
        )
        for sentinel in PROFILE_SENTINELS:
            self.assertNotIn(sentinel, filled)

    def test_no_real_contact_data_in_templates(self):
        email = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
        phone = re.compile(r"\+\d{2}[\s\d]{8,}")
        for path in PROFILE_EXAMPLE.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            self.assertEqual(phone.findall(text), [], f"{path.name}: phone-like number")
            for found in email.findall(text):
                self.assertTrue(
                    found.endswith(("example.com", "example.org")),
                    f"{path.name}: real-looking email {found}",
                )


if __name__ == "__main__":
    unittest.main()
