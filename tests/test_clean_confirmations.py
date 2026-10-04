import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from tools import clean_confirmations as cc

HEADER = "date,company,sector,role,role_type,channel,status,contact_person,fit_rating,notes,cv_file,cover_letter_file,source,deadline\n"


class FakeGmail:
    def __init__(self, inbox=(), trash=(), bodies=None):
        self.inbox, self.trash_box, self.bodies, self.trashed = list(inbox), list(trash), bodies or {}, []

    def search(self, query, mailbox="inbox", limit=200):
        return list(self.inbox if mailbox == "inbox" else self.trash_box)

    def trash(self, msgid, mailbox="inbox"):
        hit = [m for m in self.inbox if m["id"] == msgid]
        self.inbox = [m for m in self.inbox if m["id"] != msgid]
        self.trashed.append(msgid)
        return bool(hit)

    def read(self, msgid, mailbox="inbox", max_chars=None):
        return self.bodies.get(msgid, "")

    def read_many(self, msgids, mailbox="inbox", max_chars=None, links=True):
        self.read_many_links = links
        return {i: self.bodies[i] for i in msgids if i in self.bodies}


def now(offset_days=0):
    return (datetime.now() - timedelta(days=offset_days)).strftime("%Y-%m-%d %H:%M:%S")


class Sandbox(unittest.TestCase):
    """Tracker, applications folder and logs in a temp dir; Gmail replaced by FakeGmail."""

    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.tracker = tmp / "tracker.csv"
        self.apps = tmp / "applications"
        self.apps.mkdir()
        for name, value in (("TRACKER", self.tracker), ("APPS", self.apps), ("LOG", tmp / "mail-cleanup.log"),
                            ("ALERTS", tmp / "alerts.json")):
            patcher = mock.patch.object(cc, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        cc._SCAN_CACHE = None

    def use(self, fake):
        patcher = mock.patch.object(cc, "gmail", fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        return fake

    def rows(self, *rows):
        self.tracker.write_text(HEADER + "".join(f"{d},{c},,{r},,,{s},,,,,,,\n" for d, c, r, s in rows), encoding="utf-8")


class ParseMailDateTests(unittest.TestCase):
    def test_parses_gmail_client_date_string(self):
        self.assertEqual(cc._parse_mail_date("2026-09-28 16:13:06"), datetime(2026, 9, 28, 16, 13, 6))

    def test_unparseable_text_returns_none_not_an_exception(self):
        self.assertIsNone(cc._parse_mail_date("not a date"))
        self.assertIsNone(cc._parse_mail_date(""))


class ConfirmationPassTests(Sandbox):
    def test_receipt_is_logged_then_trashed(self):
        today = now()[:10]
        self.rows((today, "Example Corp", "Product Engineer", "applied"))
        (self.apps / "example_corp_product_engineer").mkdir()
        fake = self.use(FakeGmail(inbox=[{"id": "11", "date": now(), "sender": "Example Corp Hiring Team <no-reply@ashbyhq.com>",
                                          "subject": "Thanks for applying to Example Corp!"}]))
        cc.confirmation_pass(3, True)
        self.assertEqual(fake.trashed, ["11"])
        self.assertIn("Thanks for applying", (self.apps / "example_corp_product_engineer/confirmation.txt").read_text())

    def test_dry_run_trashes_nothing(self):
        self.rows((now()[:10], "Example Corp", "Product Engineer", "applied"))
        (self.apps / "example_corp_product_engineer").mkdir()
        fake = self.use(FakeGmail(inbox=[{"id": "11", "date": now(), "sender": "x", "subject": "Thanks for applying to Example Corp!"}]))
        cc.confirmation_pass(3, False)
        self.assertEqual(fake.trashed, [])


class RejectionTests(Sandbox):
    def test_tracker_updated_before_trash(self):
        self.rows(("2026-09-20", "Sample Co", "Staff Product Designer", "applied"))
        fake = self.use(FakeGmail(inbox=[{"id": "7", "date": now(), "sender": "Sample Co <notifications@example.com>",
                                          "subject": "Unfortunately we will not be moving forward - Sample Co"}]))
        cc.handle_rejections(3, True)
        self.assertEqual(fake.trashed, ["7"])
        self.assertIn(",rejected,", self.tracker.read_text())



class TrashOutcomeTests(Sandbox):
    def test_linkedin_style_rejection_found_in_trash_marks_row_rejected(self):
        # LinkedIn: subject is only "Your application to <role> at <company>"; the decision is in the body.
        self.rows(("2026-10-01", "Globex Corp", "Artificial Intelligence Engineer", "applied"))
        body = "Your update from Globex Corp. Unfortunately, we will not be moving forward with your application."
        fake = self.use(FakeGmail(trash=[{"id": "8", "date": now(), "sender": "LinkedIn <jobs-noreply@linkedin.com>",
                                          "subject": "Your application to Artificial Intelligence Engineer at Globex Corp"}],
                                  bodies={"8": body}))
        cc.handle_trash_outcomes(14, True)
        self.assertIn(",rejected,", self.tracker.read_text())
        self.assertFalse(fake.read_many_links, "cleanup reads words, not tracking URLs")

    RECOMMENDED = ("Top jobs looking for your skills\nSenior Front-End Software Engineer\nHooli · Italy\n"
                   "Frontend Developer\nOverIT · Italy\nSee more jobs")

    def _linkedin(self, company, role):
        subject = f"Your application to {role} at {company}"
        body = (f"Your update from {company}\nThank you for your interest in the {role} position at {company}. "
                f"Unfortunately, we will not be moving forward with your application.\nRegards,\n{company}\n"
                + self.RECOMMENDED)
        return {"id": "8", "date": now(), "sender": "LinkedIn <jobs-noreply@linkedin.com>", "subject": subject}, body

    def test_recommended_jobs_block_never_matches_a_live_interview_row(self):
        # Hooli is a live interview and appears in LinkedIn's "Top jobs" block of unrelated rejections.
        self.rows(("2026-10-01", "Hooli", "Senior Front-End Software Engineer", "interview"))
        mail, body = self._linkedin("Initech Ltd", "Artificial Intelligence Engineer")
        self.use(FakeGmail(trash=[mail], bodies={"8": body}))
        cc.handle_trash_outcomes(14, True)
        self.assertIn(",interview,", self.tracker.read_text())
        self.assertNotIn(",rejected,", self.tracker.read_text())

    def test_linkedin_rejection_files_only_its_own_company_row(self):
        self.rows(("2026-10-01", "Hooli", "Senior Front-End Software Engineer", "interview"),
                  ("2026-10-01", "Initech Ltd", "Artificial Intelligence Engineer", "applied"))
        mail, body = self._linkedin("Initech Ltd", "Artificial Intelligence Engineer")
        self.use(FakeGmail(trash=[mail], bodies={"8": body}))
        cc.handle_trash_outcomes(14, True)
        text = self.tracker.read_text()
        self.assertIn("Hooli,,Senior Front-End Software Engineer,,,interview", text)
        self.assertIn("Initech Ltd,,Artificial Intelligence Engineer,,,rejected", text)

    def test_generic_subject_matches_on_the_rejection_sentence_not_recommendations_far_below(self):
        self.rows(("2026-10-01", "Hooli", "Senior Front-End Software Engineer", "interview"),
                  ("2026-10-01", "Acme", "Product Designer", "applied"))
        body = ("Thank you for your interest in the Product Designer position at Acme. Unfortunately, we will "
                "not be moving forward." + " Best of luck." * 20 + "\nTop jobs: Senior Front-End Software Engineer, Hooli")
        self.use(FakeGmail(trash=[{"id": "7", "date": now(), "sender": "no-reply@ats.example.com",
                                   "subject": "Update on your application"}], bodies={"7": body}))
        cc.handle_trash_outcomes(14, True)
        text = self.tracker.read_text()
        self.assertIn("Hooli,,Senior Front-End Software Engineer,,,interview", text)
        self.assertIn("Acme,,Product Designer,,,rejected", text)

    def test_invite_in_trash_is_flagged_not_filed(self):
        self.rows(("2026-10-01", "Hooli", "Senior Front-End Engineer", "applied"))
        self.use(FakeGmail(trash=[{"id": "9", "date": now(), "sender": "Sam Recruiter <sam@example.com>",
                                   "subject": "Re: Hooli - Senior Front-End Software Engineer"}],
                           bodies={"9": "Can we schedule a call for the technical interview on Tuesday?"}))
        cc.handle_trash_outcomes(14, True)
        self.assertIn(",applied,", self.tracker.read_text())


class AlertPassTests(Sandbox):
    def alerts(self, data):
        cc.ALERTS.parent.mkdir(parents=True, exist_ok=True)
        cc.ALERTS.write_text(json.dumps(data), encoding="utf-8")

    def entry(self, roles, skip_reason=""):
        return {"date": now(), "sender": "LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>",
                "subject": "Solutions Architect at Acme", "skip_reason": skip_reason, "roles": roles}

    def test_all_roles_handled_trashes_and_drops_entry(self):
        self.rows()
        fake = self.use(FakeGmail(inbox=[{"id": "5", "date": now(), "sender": "x", "subject": "y"}]))
        self.alerts({"5": self.entry([{"company": "Acme", "role": "Solutions Architect", "status": "sent"},
                                      {"company": "Foo", "role": "Designer", "status": "skipped", "reason": "on-site"}])})
        cc.handle_alerts(True)
        self.assertEqual(fake.trashed, ["5"])
        self.assertEqual(json.loads(cc.ALERTS.read_text()), {})
        self.assertIn("trashed alert", cc.LOG.read_text())

    def test_tracker_row_counts_as_handled(self):
        self.rows((now()[:10], "Acme Italia", "Solutions Architect (Remote)", "applied"))
        fake = self.use(FakeGmail(inbox=[{"id": "5", "date": now(), "sender": "x", "subject": "y"}]))
        self.alerts({"5": self.entry([{"company": "Acme", "role": "Solutions Architect", "status": "new"}])})
        cc.handle_alerts(True)
        self.assertEqual(fake.trashed, ["5"])

    def test_drafted_role_keeps_alert(self):
        self.rows(("2026-10-04", "Acme", "Solutions Architect", "drafted"))
        fake = self.use(FakeGmail(inbox=[{"id": "5", "date": now(), "sender": "x", "subject": "y"}]))
        self.alerts({"5": self.entry([{"company": "Acme", "role": "Solutions Architect", "status": "drafted"}])})
        cc.handle_alerts(True)
        self.assertEqual(fake.trashed, [])
        self.assertIn("5", json.loads(cc.ALERTS.read_text()))

    def test_skip_reason_handles_whole_email(self):
        self.rows()
        fake = self.use(FakeGmail(inbox=[{"id": "9", "date": now(), "sender": "x", "subject": "y"}]))
        self.alerts({"9": self.entry([], skip_reason="OfferZen digest - platform signup, not a job")})
        cc.handle_alerts(True)
        self.assertEqual(fake.trashed, ["9"])

    def test_handled_alert_already_gone_is_dropped(self):
        self.rows()
        fake = self.use(FakeGmail(inbox=[]))
        self.alerts({"5": self.entry([{"company": "Acme", "role": "Solutions Architect", "status": "sent"}])})
        cc.handle_alerts(True)
        self.assertEqual(json.loads(cc.ALERTS.read_text()), {})

    def test_dry_run_changes_nothing(self):
        self.rows()
        fake = self.use(FakeGmail(inbox=[{"id": "5", "date": now(), "sender": "x", "subject": "y"}]))
        self.alerts({"5": self.entry([{"company": "Acme", "role": "Solutions Architect", "status": "sent"}])})
        cc.handle_alerts(False)
        self.assertEqual(fake.trashed, [])
        self.assertIn("5", json.loads(cc.ALERTS.read_text()))

    def test_drafted_role_keeps_alert_even_with_older_settled_row(self):
        # A repost: an older, rejected application to a similar title must not settle today's drafted role.
        self.rows(("2026-09-01", "Acme", "Product Designer", "rejected"),
                  ("2026-10-04", "Acme", "Senior Product Designer", "drafted"))
        fake = self.use(FakeGmail(inbox=[{"id": "5", "date": now(), "sender": "x", "subject": "y"}]))
        self.alerts({"5": self.entry([{"company": "Acme", "role": "Senior Product Designer", "status": "drafted"}])})
        cc.handle_alerts(True)
        self.assertEqual(fake.trashed, [])

    def test_new_role_not_settled_by_an_older_application(self):
        self.rows(("2026-09-01", "Acme", "Senior Product Designer", "rejected"))
        fake = self.use(FakeGmail(inbox=[{"id": "5", "date": now(), "sender": "x", "subject": "y"}]))
        self.alerts({"5": self.entry([{"company": "Acme", "role": "Senior Product Designer", "status": "new"}])})
        cc.handle_alerts(True)
        self.assertEqual(fake.trashed, [])

    def test_new_role_settled_by_tracker_row_with_same_url(self):
        self.tracker.write_text(HEADER + "2026-09-01,Acme,,Designer II,,,applied,,,,,,https://jobs.acme.com/42,\n", encoding="utf-8")
        fake = self.use(FakeGmail(inbox=[{"id": "5", "date": now(), "sender": "x", "subject": "y"}]))
        self.alerts({"5": self.entry([{"company": "Acme", "role": "Senior Product Designer", "status": "new",
                                       "url": "https://jobs.acme.com/42"}])})
        cc.handle_alerts(True)
        self.assertEqual(fake.trashed, ["5"])

    def test_role_without_meaningful_words_is_not_settled_by_tracker(self):
        self.rows((now()[:10], "Acme Labs", "Backend Engineer", "skipped"))
        fake = self.use(FakeGmail(inbox=[{"id": "5", "date": now(), "sender": "x", "subject": "y"}]))
        self.alerts({"5": self.entry([{"company": "Acme", "role": "Lead", "status": "new"}])})
        cc.handle_alerts(True)
        self.assertEqual(fake.trashed, [])

    def test_skip_reason_does_not_override_a_drafted_role(self):
        self.rows()
        fake = self.use(FakeGmail(inbox=[{"id": "9", "date": now(), "sender": "x", "subject": "y"}]))
        self.alerts({"9": self.entry([{"company": "Acme", "role": "Designer", "status": "drafted"}], skip_reason="digest")})
        cc.handle_alerts(True)
        self.assertEqual(fake.trashed, [])

    def test_interview_like_subject_is_never_trashed_as_alert(self):
        self.rows()
        fake = self.use(FakeGmail(inbox=[{"id": "5", "date": now(), "sender": "x", "subject": "y"}]))
        entry = self.entry([{"company": "Acme", "role": "Designer", "status": "sent"}])
        entry["subject"] = "Re: Designer role - can we schedule a call / interview?"
        self.alerts({"5": entry})
        cc.handle_alerts(True)
        self.assertEqual(fake.trashed, [])

    def test_broken_alerts_file_does_not_stop_the_pass(self):
        self.use(FakeGmail())
        cc.ALERTS.parent.mkdir(parents=True, exist_ok=True)
        cc.ALERTS.write_text('{"5": {"roles": [],}', encoding="utf-8")
        cc.handle_alerts(True)  # must not raise

    def test_non_dict_role_does_not_crash(self):
        self.rows()
        fake = self.use(FakeGmail(inbox=[{"id": "5", "date": now(), "sender": "x", "subject": "y"}]))
        self.alerts({"5": self.entry(["Acme Designer"]), "6": "garbage"})
        cc.handle_alerts(True)  # must not raise
        self.assertEqual(fake.trashed, [])

    def test_no_alerts_file_is_a_no_op(self):
        self.use(FakeGmail())
        cc.handle_alerts(True)  # must not raise


if __name__ == "__main__":
    unittest.main()
