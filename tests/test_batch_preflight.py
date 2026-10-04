import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.batch_preflight import build_queue, write_outputs


class BatchPreflightTests(unittest.TestCase):
    def test_filters_final_rows_and_identifies_bad_packages(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tracker = root / "profile/tracker.csv"
            tracker.parent.mkdir(parents=True, exist_ok=True)
            fields = ["company", "role", "status", "source", "cv_file", "cover_letter_file"]
            with tracker.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerow({"company": "Ready", "role": "Engineer", "status": "drafted",
                                 "source": "https://jobs.ashbyhq.com/ready/1", "cv_file": "main_ready_engineer.pdf", "cover_letter_file": ""})
                writer.writerow({"company": "Done", "role": "Engineer", "status": "submitted",
                                 "source": "https://example.com", "cv_file": "cv.pdf", "cover_letter_file": ""})
                writer.writerow({"company": "Broken", "role": "Engineer", "status": "drafted",
                                 "source": "http://example.com", "cv_file": "missing.pdf", "cover_letter_file": ""})
            (root / "main_ready_engineer.pdf").write_bytes(b"%PDF-1.7\nfixture")
            queue = build_queue(root, tracker)
            self.assertEqual(queue["ready_count"], 1)
            self.assertEqual(queue["blocked_count"], 1)
            self.assertEqual(queue["applications"][0]["company"], "Ready")
            self.assertTrue(any(reason.startswith("source must be") for reason in queue["applications"][1]["reasons"]))

    def _queue(self, rows, limit=None, compiled=True):
        """Queue drafted rows; with `compiled`, their documents exist as PDFs on disk."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tracker = root / "profile/tracker.csv"
            tracker.parent.mkdir(parents=True, exist_ok=True)
            fields = ["company", "role", "role_type", "status", "source", "cv_file",
                      "cover_letter_file", "fit_rating", "notes"]
            with tracker.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for row in rows:
                    writer.writerow({"role_type": "", "status": "drafted",
                                     "source": "https://jobs.ashbyhq.com/x/1", "cover_letter_file": "",
                                     "fit_rating": "90", "notes": "Work mode: remote", **row})
                    for column in ("cv_file", "cover_letter_file"):
                        if compiled and row.get(column):
                            pdf = (root / row[column]).with_suffix(".pdf")
                            pdf.parent.mkdir(parents=True, exist_ok=True)
                            pdf.write_bytes(b"%PDF-1.7\nfixture")
            return build_queue(root, tracker, limit)["applications"]

    def _by_company(self, rows):
        return {item["company"]: item for item in self._queue(rows)}

    def test_cv_named_for_another_company_is_blocked(self):
        # Every one of these names overlaps the FlexMade path somewhere; none is FlexMade.
        for company in ("Lexroom", "Frontend Masters", "Front", "AI", "Main Street Health"):
            with self.subTest(company=company):
                item = self._by_company([{"company": company, "role": "Frontend Engineer",
                                          "cv_file": "cv/main_flexmade_frontend_engineer.pdf"}])[company]
                self.assertFalse(item["ready"])
                self.assertTrue(any("main_flexmade_frontend_engineer.pdf" in r for r in item["reasons"]),
                                item["reasons"])

    def test_cv_named_for_the_company_is_accepted_in_any_slug_form(self):
        items = self._by_company([
            {"company": "Trigger.dev", "role": "Design Engineer",
             "cv_file": "cv/main_trigger_dev_design_engineer.pdf"},
            {"company": "ADI Group", "role": "Frontend Developer",
             "cv_file": "cv/main_adi_frontend_developer.pdf"},
            {"company": "Mastercard", "role": "Frontend Engineer",
             "cv_file": "cv/main_mastercard_frontend_engineer.pdf"},
            {"company": "Acme", "role": "Scrum Master", "cv_file": "cv/main_acme_scrum_master.pdf"},
            {"company": "FlexMade", "role": "Frontend Engineer",
             "cv_file": "profile/applications/flexmade_frontend_engineer/submission/abc123/cv.pdf"},
        ])
        for company, item in items.items():
            with self.subTest(company=company):
                self.assertTrue(item["ready"], item["reasons"])

    def test_designed_and_master_cvs_are_blocked(self):
        items = self._by_company([
            {"company": "Clera", "role": "Designer", "cv_file": "cv/main_master_designed.pdf"},
            {"company": "Acme", "role": "Designer", "cv_file": "cv/main_acme_designer_designed.pdf"},
            {"company": "Bunch", "role": "Engineer", "cv_file": "cv/main_master.pdf"},
            {"company": "Jimdo", "role": "Designer", "cv_file": "documents/cv/Alex Example - Resume.pdf"},
        ])
        for company, item in items.items():
            with self.subTest(company=company):
                self.assertFalse(item["ready"])

    def test_cover_letter_for_another_company_is_blocked(self):
        item = self._by_company([{"company": "Lexroom", "role": "Frontend Engineer",
                                   "cv_file": "cv/main_lexroom_frontend_engineer.pdf",
                                   "cover_letter_file": "cover_letters/cover_flexmade_frontend_engineer.pdf"}])["Lexroom"]
        self.assertFalse(item["ready"])
        self.assertTrue(any("cover_flexmade_frontend_engineer.pdf" in r for r in item["reasons"]), item["reasons"])

    def test_row_without_a_cv_is_blocked(self):
        item = self._by_company([{"company": "Acme", "role": "Engineer", "cv_file": ""}])["Acme"]
        self.assertFalse(item["ready"])

    def test_source_module_paths_resolve_to_their_compiled_pdfs(self):
        # /apply Step 6b records the "Files Created" source paths, which are .py modules.
        item = self._by_company([{"company": "Acme", "role": "Engineer",
                                   "cv_file": "cv/main_acme_engineer.py",
                                   "cover_letter_file": "cover_letters/cover_acme_engineer.py"}])["Acme"]
        self.assertTrue(item["ready"], item["reasons"])
        self.assertEqual(item["cv_pdf"], "cv/main_acme_engineer.pdf")
        self.assertEqual(item["cover_letter_pdf"], "cover_letters/cover_acme_engineer.pdf")

    def test_documents_that_were_never_compiled_are_blocked(self):
        item = self._queue([{"company": "Acme", "role": "Engineer", "cv_file": "cv/main_acme_engineer.py",
                             "cover_letter_file": "cover_letters/cover_acme_engineer.py"}], compiled=False)[0]
        self.assertFalse(item["ready"])
        self.assertTrue(any("cv/main_acme_engineer.pdf" in r for r in item["reasons"]), item["reasons"])
        self.assertTrue(any("cover_letters/cover_acme_engineer.pdf" in r for r in item["reasons"]), item["reasons"])

    def test_work_mode_reads_negations_role_type_and_explicit_marker(self):
        cases = [
            # notes, role_type, expected work_mode, expected ready
            ("On-site in Springfield, not remote", "", "onsite", False),
            ("", "On-site (Bangkok)", "onsite", False),
            ("Must relocate to Berlin within three months.", "", "relocation", False),
            ("Fully remote, no hybrid", "", "remote", True),
            ("Remote Europe; no relocation", "", "remote", True),
            ("Hybrid arrangement with 5-15 on-site days per month", "", "hybrid", True),
            ("Work mode: remote. Optional on-site week each quarter.", "", "remote", True),
            ("Strong React match.", "", "unknown", True),
        ]
        for notes, role_type, mode, ready in cases:
            with self.subTest(notes=notes, role_type=role_type):
                item = self._queue([{"company": "Acme", "role": "Engineer", "cv_file": "cv/main_acme_engineer.pdf",
                                     "notes": notes, "role_type": role_type}])[0]
                self.assertEqual(item["work_mode"], mode)
                self.assertEqual(item["ready"], ready, item["reasons"])

    def test_hybrid_and_unrecorded_work_modes_warn(self):
        items = self._by_company([
            {"company": "Hybridco", "role": "Engineer", "cv_file": "cv/main_hybridco_engineer.pdf",
             "notes": "Hybrid, 2 office days in Springfield."},
            {"company": "Quietco", "role": "Engineer", "cv_file": "cv/main_quietco_engineer.pdf",
             "notes": "Strong React match."},
            {"company": "Remoteco", "role": "Engineer", "cv_file": "cv/main_remoteco_engineer.pdf",
             "notes": "Fully remote."},
        ])
        self.assertTrue(items["Hybridco"]["warnings"])
        self.assertTrue(items["Quietco"]["warnings"])
        self.assertEqual(items["Remoteco"]["warnings"], [])

    def test_queue_orders_by_fit_band_then_remote_before_hybrid(self):
        rows = [
            {"company": "HybridStrong", "role": "E", "cv_file": "cv/main_hybridstrong_e.pdf",
             "fit_rating": "95", "notes": "Hybrid, Springfield"},
            {"company": "RemoteGood", "role": "E", "cv_file": "cv/main_remotegood_e.pdf",
             "fit_rating": "62", "notes": "Remote"},
            {"company": "RemoteStrong", "role": "E", "cv_file": "cv/main_remotestrong_e.pdf",
             "fit_rating": "80", "notes": "Remote"},
            {"company": "UnknownStrong", "role": "E", "cv_file": "cv/main_unknownstrong_e.pdf",
             "fit_rating": "78", "notes": "React"},
            {"company": "RemoteGoodLow", "role": "E", "cv_file": "cv/main_remotegoodlow_e.pdf",
             "fit_rating": "61", "notes": "Remote"},
        ]
        order = [item["company"] for item in self._queue(rows)]
        self.assertEqual(order, ["RemoteStrong", "UnknownStrong", "HybridStrong", "RemoteGood", "RemoteGoodLow"])
        limited = [item["company"] for item in self._queue(rows, limit=3)]
        self.assertEqual(limited, ["RemoteStrong", "UnknownStrong", "HybridStrong"])

    def test_fit_below_the_good_band_or_unscored_warns(self):
        items = self._by_company([
            {"company": "Moderateco", "role": "E", "cv_file": "cv/main_moderateco_e.pdf", "fit_rating": "52"},
            {"company": "Goodco", "role": "E", "cv_file": "cv/main_goodco_e.pdf", "fit_rating": "68"},
            {"company": "Blankco", "role": "E", "cv_file": "cv/main_blankco_e.pdf", "fit_rating": ""},
        ])
        self.assertTrue(items["Moderateco"]["warnings"])
        self.assertEqual(items["Goodco"]["warnings"], [])
        self.assertTrue(items["Blankco"]["warnings"])

    def test_outputs_are_machine_and_human_readable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            queue = {"generated_on": "2026-09-24", "ready_count": 0, "blocked_count": 0,
                     "applications": [], "counts": {}, "total_considered": 0, "tracker": "x"}
            write_outputs(queue, root / "q.json", root / "q.md")
            self.assertEqual(json.loads((root / "q.json").read_text())["ready_count"], 0)
            self.assertIn("Browser submission preflight", (root / "q.md").read_text())


if __name__ == "__main__":
    unittest.main()
