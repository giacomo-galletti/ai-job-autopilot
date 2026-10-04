"""Guards for the onboarding privacy model.

Personal data must live only in the gitignored profile/ folder. The README must say so at the
point of decision, and /onboard must verify the folder is ignored before writing into it.
"""
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"
ONBOARD = REPO / ".claude" / "commands" / "onboard.md"


class TestReadmePrivacy(unittest.TestCase):
    def setUp(self):
        self.text = README.read_text(encoding="utf-8")

    def test_readme_has_privacy_section(self):
        self.assertIn("## Privacy model", self.text)
        self.assertIn("gitignored", self.text)
        self.assertIn("profile/", self.text)

    def test_readme_warns_about_private_repo_for_modified_files(self):
        self.assertIn("private", self.text.lower())

    def test_readme_carries_attribution_and_warnings(self):
        for needle in ("MadsLorentzen/ai-job-search", "MIT", "Terms of Service", "AGPL", "Keychain"):
            self.assertIn(needle, self.text, needle)


class TestOnboardChecksIgnoreBeforeWriting(unittest.TestCase):
    def test_gitignore_check_precedes_profile_writing(self):
        text = ONBOARD.read_text(encoding="utf-8")
        check = text.index("git check-ignore profile/")
        self.assertLess(check, text.index("## Step 3: Write the profile"))


if __name__ == "__main__":
    unittest.main()
