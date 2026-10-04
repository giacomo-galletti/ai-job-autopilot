"""Guards for /reset: it must wipe profile/ and documents/ and nothing tracked."""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESET = REPO / ".claude" / "commands" / "reset.md"
DOCS_README = REPO / "documents" / "README.md"

# Drop folders the reset must clear; kept in step with documents/README.md.
DOCUMENT_SUBFOLDERS = ["cv", "linkedin", "diplomas", "references", "projects", "postings", "applications"]


class TestResetDocuments(unittest.TestCase):
    def setUp(self):
        self.text = RESET.read_text(encoding="utf-8")

    def test_preview_lists_every_subfolder(self):
        for f in DOCUMENT_SUBFOLDERS:
            self.assertIn(f"documents/{f}/", self.text, f)

    def test_delete_block_removes_every_subfolder(self):
        deleted = set(re.findall(r"rm -r?f documents/(\w+)/", self.text))
        self.assertEqual(sorted(set(DOCUMENT_SUBFOLDERS) - deleted), [])

    def test_documents_folders_exist_in_repo(self):
        for f in DOCUMENT_SUBFOLDERS:
            self.assertTrue((REPO / "documents" / f).exists(), f)


class TestResetProfile(unittest.TestCase):
    def setUp(self):
        self.text = RESET.read_text(encoding="utf-8")

    def test_wipes_profile_folder_only(self):
        self.assertIn("find profile -mindepth 1 -delete", self.text)
        self.assertIn("profile.example/", self.text)  # named as untouched

    def test_requires_exact_confirmation(self):
        self.assertIn("`RESET`", self.text)
        self.assertIn("Nothing was changed", self.text)

    def test_checks_profile_is_gitignored_first(self):
        self.assertIn("git check-ignore profile/", self.text)

    def test_points_back_to_onboard(self):
        self.assertIn("/onboard", self.text)
        self.assertNotIn("/setup", self.text)


if __name__ == "__main__":
    unittest.main()
