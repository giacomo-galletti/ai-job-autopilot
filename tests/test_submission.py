"""Exercise submission history, interruption recovery and tracker updates without a browser."""

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.submission import Ledger, SubmissionError


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.fields = ["date", "company", "role", "status", "notes", "cv_file", "cover_letter_file", "source"]
        self.cv, self.cover = "cv/main_acme_engineer.pdf", "cover_letters/cover_acme_engineer.pdf"
        self.initial = {"date": "2026-01-01", "company": "Acme", "role": "Engineer",
                        "status": "drafted", "notes": "Contains, a comma", "source": "https://example.com/job",
                        "cv_file": self.cv, "cover_letter_file": self.cover}
        self.write_rows([self.initial])
        self.write_pdf(self.cv, b"fixture CV")
        self.write_pdf(self.cover, b"fixture cover")
        (self.root / "answers.json").write_text(json.dumps({"Name": "Test Person", "Why?": "Design, then build."}))
        (self.root / "proof.txt").write_text("Application received for Acme Engineer; reference TEST-123")
        self.ledger = Ledger(self.root, "Acme", "Engineer")

    def write_pdf(self, relative, body):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"%PDF-1.4\n" + body)

    def write_rows(self, rows):
        (self.root / "profile").mkdir(exist_ok=True)
        with (self.root / "profile/tracker.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fields)
            writer.writeheader()
            writer.writerows(rows)

    def row(self):
        with (self.root / "profile/tracker.csv").open(newline="") as f:
            return next(csv.DictReader(f))

    def prepare(self):
        return self.ledger.prepare("https://example.com/job", self.cv, "answers.json", self.cover)

    def test_confirmed_send_preserves_exact_package_and_tracker_data(self):
        prepared = self.prepare()
        original = (self.root / self.cv).read_bytes()
        self.write_pdf(self.cv, b"later draft")
        self.ledger.begin("Submit the Acme Engineer application")
        result = self.ledger.finish("confirmed", "proof.txt")
        row = self.row()
        self.assertEqual(row["status"], "applied")
        self.assertEqual(row["date"], result["submission_date"])
        self.assertEqual((self.root / row["cv_file"]).read_bytes(), original)
        self.assertEqual(row["source"], self.initial["source"])
        self.assertIn(self.initial["notes"], row["notes"])
        self.assertEqual(prepared["attempt"], result["attempt"])
        self.assertTrue((self.ledger.folder / prepared["attempt"] / "record.json").exists())
        with self.assertRaises(SubmissionError):
            self.ledger.begin("Submit again")
        with self.assertRaises(SubmissionError):
            self.prepare()

    def test_unknown_result_prevents_retry_and_does_not_mark_applied(self):
        self.prepare()
        self.ledger.begin("Submit Acme Engineer")
        with self.assertRaises(SubmissionError):
            self.ledger.begin("Submit Acme Engineer")
        self.ledger.finish("uncertain", "proof.txt")
        self.assertEqual(self.row()["status"], "drafted")
        with self.assertRaises(SubmissionError):
            self.prepare()
        with self.assertRaises(SubmissionError):
            self.ledger.sync()
        self.ledger.finish("confirmed", "proof.txt")
        self.assertEqual(self.row()["status"], "applied")
        self.assertEqual(len(self.ledger.state()["observations"]), 2)

    def test_validation_failure_allows_new_package_without_losing_attempt(self):
        old = self.prepare()
        self.ledger.begin("Submit Acme Engineer")
        self.ledger.finish("not_submitted", "proof.txt")
        new = self.prepare()
        self.assertNotEqual(old["attempt"], new["attempt"])
        self.assertTrue((self.ledger.folder / old["attempt"] / "record.json").exists())
        self.assertEqual(self.row()["status"], "drafted")

    def test_modified_snapshot_and_empty_authorization_block_begin(self):
        prepared = self.prepare()
        with self.assertRaises(SubmissionError):
            self.ledger.begin("  ")
        (self.root / prepared["files"]["answers.json"]["path"]).write_text('{"changed":true}')
        with self.assertRaises(SubmissionError):
            self.ledger.begin("Submit Acme Engineer")
        self.assertEqual(self.ledger.state()["status"], "ready")

    def test_receipt_survives_failed_tracker_write_and_sync_is_idempotent(self):
        self.prepare()
        self.ledger.begin("Submit Acme Engineer")
        with patch.object(self.ledger, "sync", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                self.ledger.finish("confirmed", "proof.txt")
        self.assertEqual(self.ledger.state()["status"], "submitted")
        self.assertEqual(self.row()["status"], "drafted")
        self.ledger.sync()
        first = self.row()
        self.ledger.sync()
        self.assertEqual(first, self.row())
        first["status"] = "interview"
        self.write_rows([first])
        self.ledger.sync()
        self.assertEqual(self.row()["status"], "interview")

    def test_interrupted_pointer_refresh_cannot_reenable_submit(self):
        self.prepare()
        stale = self.ledger.path.read_text()
        self.ledger.begin("Submit Acme Engineer")
        self.ledger.path.write_text(stale)
        with self.assertRaises(SubmissionError):
            self.ledger.begin("Submit Acme Engineer")
        self.assertEqual(self.ledger.state()["status"], "attempting")

    def test_duplicate_rows_or_existing_application_block_preparation(self):
        self.write_rows([self.initial, self.initial])
        with self.assertRaises(SubmissionError):
            self.prepare()
        self.write_rows([{**self.initial, "status": "applied"}])
        with self.assertRaises(SubmissionError):
            self.prepare()

    def test_invalid_url_document_answers_and_empty_evidence(self):
        with self.assertRaises(SubmissionError):
            self.ledger.prepare("https://person:secret@example.com/job", self.cv, "answers.json")
        (self.root / self.cv).write_text("not a PDF")
        with self.assertRaises(SubmissionError):
            self.prepare()
        self.write_pdf(self.cv, b"fixture")
        (self.root / "answers.json").write_text("[]")
        with self.assertRaises(SubmissionError):
            self.prepare()
        (self.root / "answers.json").write_text('{"Name":"Test"}')
        self.prepare()
        self.ledger.begin("Submit Acme Engineer")
        (self.root / "proof.txt").write_text("")
        with self.assertRaises(SubmissionError):
            self.ledger.finish("confirmed", "proof.txt")
        self.assertEqual(self.row()["status"], "drafted")

    def assert_prepare_refused(self, cv=None, cover=None):
        with self.assertRaises(SubmissionError):
            self.ledger.prepare("https://example.com/job", cv or self.cv, "answers.json", cover)
        self.assertFalse(self.ledger.path.exists(), "a refused package must not become the active attempt")

    def test_prepare_refuses_a_cv_other_than_the_one_the_tracker_records(self):
        self.write_pdf("cv/main_acme_platform_engineer.pdf", b"another Acme draft")
        self.assert_prepare_refused(cv="cv/main_acme_platform_engineer.pdf")

    def test_prepare_refuses_a_cv_tailored_for_another_company(self):
        self.write_pdf("cv/main_flexmade_engineer.pdf", b"FlexMade CV")
        self.write_rows([{**self.initial, "cv_file": "cv/main_flexmade_engineer.pdf"}])
        self.assert_prepare_refused(cv="cv/main_flexmade_engineer.pdf")

    def test_prepare_refuses_the_designed_cv_even_when_the_tracker_records_it(self):
        self.write_pdf("cv/main_acme_engineer_designed.pdf", b"two-column CV")
        self.write_rows([{**self.initial, "cv_file": "cv/main_acme_engineer_designed.pdf"}])
        self.assert_prepare_refused(cv="cv/main_acme_engineer_designed.pdf")

    def test_prepare_refuses_a_cover_letter_written_for_another_company(self):
        self.write_pdf("cover_letters/cover_flexmade_engineer.pdf", b"Dear FlexMade")
        self.write_rows([{**self.initial, "cover_letter_file": ""}])
        self.assert_prepare_refused(cover="cover_letters/cover_flexmade_engineer.pdf")

    def test_prepare_refuses_a_cover_letter_other_than_the_one_the_tracker_records(self):
        self.write_pdf("cover_letters/cover_acme_platform_engineer.pdf", b"Dear Acme, another role")
        self.assert_prepare_refused(cover="cover_letters/cover_acme_platform_engineer.pdf")

    def test_prepare_refuses_a_row_with_no_recorded_cv(self):
        self.write_rows([{**self.initial, "cv_file": ""}])
        self.assert_prepare_refused()

    def test_prepare_accepts_the_source_module_path_apply_records(self):
        self.write_rows([{**self.initial, "cv_file": "cv/main_acme_engineer.py",
                          "cover_letter_file": "cover_letters/cover_acme_engineer.py"}])
        self.prepare()
        self.assertEqual(self.ledger.state()["status"], "ready")

    def test_draft_status_is_compared_case_insensitively(self):
        self.write_rows([{**self.initial, "status": "Drafted"}])
        self.prepare()
        self.ledger.begin("Submit the Acme Engineer application")
        self.assertEqual(self.ledger.state()["status"], "attempting")

    def write_profile_name(self, name):
        profile = self.root / "profile/profile.md"
        profile.parent.mkdir(parents=True, exist_ok=True)
        profile.write_text(f"# Candidate Profile\n\n- **Name:** {name}\n- **Location:** Somewhere\n")

    def test_uploaded_files_have_simple_names_and_record_their_source(self):
        # The employer sees these names: the candidate's name and the document, nothing else.
        self.write_profile_name("Test Person")
        files = self.prepare()["files"]
        self.assertEqual(Path(files["cv.pdf"]["path"]).name, "Test Person - Resume.pdf")
        self.assertEqual(Path(files["cover_letter.pdf"]["path"]).name, "Test Person - Cover Letter.pdf")
        self.assertEqual(files["cv.pdf"]["source"], self.cv)
        self.assertEqual(files["cover_letter.pdf"]["source"], self.cover)

    def test_upload_names_fall_back_without_a_profile_name(self):
        files = self.prepare()["files"]
        self.assertEqual(Path(files["cv.pdf"]["path"]).name, "Resume.pdf")
        self.assertEqual(Path(files["cover_letter.pdf"]["path"]).name, "Cover Letter.pdf")

    def test_a_slash_in_the_profile_name_never_splits_the_snapshot_path(self):
        self.write_profile_name("Test Person (they/them)")
        data = self.prepare()
        cv = self.ledger.root / data["files"]["cv.pdf"]["path"]
        self.assertEqual(cv.parent, self.ledger.folder / data["attempt"])

    def test_employer_refusal_is_final_and_closes_the_row(self):
        self.prepare()
        self.ledger.begin("Submit the Acme Engineer application")
        (self.root / "refusal.txt").write_text("You have already applied within the last 90 days.")
        self.ledger.finish("refused", "refusal.txt")
        self.assertEqual(self.ledger.state()["status"], "refused")
        row = self.row()
        self.assertEqual(row["status"], "withdrawn")
        self.assertIn("refused", row["notes"])
        self.assertIn(self.initial["notes"], row["notes"])
        with self.assertRaises(SubmissionError):
            self.prepare()

    def test_cli_accepts_a_refusal(self):
        script = Path(__file__).resolve().parents[1] / "tools/submission.py"
        prefix = [sys.executable, str(script), "--root", str(self.root), "--company", "Acme", "--role", "Engineer"]
        auth = self.root / "authorization.txt"
        auth.write_text("Submit the Acme Engineer application")
        for command in (["prepare", "--url", "https://example.com/job", "--cv", self.cv, "--answers", "answers.json"],
                        ["begin", "--authorization-file", str(auth)],
                        ["finish", "--result", "refused", "--evidence", "proof.txt"]):
            result = subprocess.run(prefix + command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.row()["status"], "withdrawn")

    def test_cli_round_trip_without_cover_letter(self):
        script = Path(__file__).resolve().parents[1] / "tools/submission.py"
        prefix = [sys.executable, str(script), "--root", str(self.root), "--company", "Acme", "--role", "Engineer"]
        auth = self.root / "authorization.txt"
        auth.write_text("Submit the Acme Engineer application")
        commands = [
            ["prepare", "--url", "https://example.com/job", "--cv", self.cv, "--answers", "answers.json"],
            ["begin", "--authorization-file", str(auth)],
            ["finish", "--result", "confirmed", "--evidence", "proof.txt"],
            ["sync"], ["status"],
        ]
        for command in commands:
            result = subprocess.run(prefix + command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("status", json.loads(result.stdout))
        self.assertEqual(self.row()["status"], "applied")
        self.assertEqual(self.row()["cover_letter_file"], "")


if __name__ == "__main__":
    unittest.main()
