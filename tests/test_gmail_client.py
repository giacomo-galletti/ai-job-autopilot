import unittest
from unittest import mock

from tools import gmail_client as g


def setUpModule():
    g.ACCOUNT, g.DISPLAY_NAME = "alex@example.com", "Alex Example"


class ConfigTests(unittest.TestCase):
    def test_password_prefers_env_var_and_strips_spaces(self):
        with mock.patch.dict("os.environ", {"JOB_KIT_GMAIL_APP_PASSWORD": "abcd efgh ijkl mnop"}):
            self.assertEqual(g.password(), "abcdefghijklmnop")

    def test_password_falls_back_to_keyring_when_no_keychain(self):
        with mock.patch.dict("os.environ", {}, clear=False) as env:
            env.pop("JOB_KIT_GMAIL_APP_PASSWORD", None)
            with mock.patch.object(g, "_keychain_password", return_value=""), \
                    mock.patch.object(g, "_keyring_password", return_value="secret"):
                self.assertEqual(g.password(), "secret")

    def test_missing_password_exits_cleanly(self):
        with mock.patch.dict("os.environ", {}, clear=False) as env:
            env.pop("JOB_KIT_GMAIL_APP_PASSWORD", None)
            with mock.patch.object(g, "_keychain_password", return_value=""), \
                    mock.patch.object(g, "_keyring_password", return_value=""):
                with self.assertRaises(SystemExit):
                    g.password()

    def test_unconfigured_account_exits_cleanly(self):
        with mock.patch.object(g, "ACCOUNT", ""), self.assertRaises(SystemExit):
            g.build_message("a@b.co", "s", "t")

    def test_identity_reads_environment(self):
        env = {"JOB_KIT_GMAIL_ADDRESS": "pat@example.com", "JOB_KIT_GMAIL_NAME": "Pat Example"}
        with mock.patch.dict("os.environ", env):
            self.assertEqual(g._load_identity(), ("pat@example.com", "Pat Example"))

HTML_ALERT = (b"From: LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>\r\n"
              b"Subject: Solutions Architect at Acme\r\n"
              b"Message-ID: <abc@linkedin.com>\r\n"
              b"Date: Sat, 03 Oct 2026 09:12:00 +0200\r\n"
              b"MIME-Version: 1.0\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
              b"<p>New job</p><a href=\"https://www.linkedin.com/jobs/view/123\">Solutions Architect</a>"
              b"<style>.x{color:red}</style><br>Acme &amp; partners")


class PureHelperTests(unittest.TestCase):
    def test_parse_list_line_reads_flags_and_quoted_name(self):
        flags, name = g.parse_list_line('(\\HasNoChildren \\Trash) "/" "[Gmail]/Bin"')
        self.assertIn("\\Trash", flags)
        self.assertEqual(name, "[Gmail]/Bin")

    def test_parse_list_line_garbage_returns_none(self):
        self.assertEqual(g.parse_list_line("nonsense"), (set(), None))

    def test_summarize_decodes_encoded_words(self):
        raw = (b"From: =?UTF-8?Q?Himalayas_=E2=9B=B0?= <hi@himalayas.app>\r\n"
               b"Subject: =?UTF-8?B?R3JhemllIHBlciBsYSB0dWEgY2FuZGlkYXR1cmEg4pyU?=\r\n"
               b"Date: Sat, 03 Oct 2026 09:12:00 +0000\r\n\r\n")
        row = g.summarize("1812", raw)
        self.assertEqual(row["id"], "1812")
        self.assertIn("Himalayas", row["sender"])
        self.assertTrue(row["subject"].startswith("Grazie per la tua candidatura"))
        self.assertRegex(row["date"], r"^2026-10-0[34] \d\d:\d\d:\d\d$")

    def test_summarize_survives_unknown_charset_and_truncated_word(self):
        row = g.summarize("2", b"From: =?utf-8?Q?=E2=82?= <a@b.c>\r\nSubject: =?x-bogus?B?SGk=?=\r\n\r\n")
        self.assertIn("a@b.c", row["sender"])
        self.assertTrue(row["subject"])

    def test_summarize_raw_utf8_header_is_readable(self):
        row = g.summarize("3", "From: José <a@b.c>\r\nSubject: Candidatura ricevuta – ok\r\n\r\n".encode())
        self.assertEqual(row["sender"], "José <a@b.c>")
        self.assertEqual(row["subject"], "Candidatura ricevuta – ok")

    def test_setup_store_failure_never_prints_password(self):
        err = g.subprocess.CalledProcessError(1, ["security", "-w", "abcdefghijklmnop"])
        with mock.patch.object(g.getpass, "getpass", return_value="abcd efgh ijkl mnop"), \
                mock.patch.object(g.subprocess, "run", side_effect=err):
            with self.assertRaises(SystemExit) as ctx:
                g.setup()
        self.assertNotIn("abcdefghijklmnop", str(ctx.exception))

    def test_summarize_bad_date_is_empty_string(self):
        self.assertEqual(g.summarize("1", b"Subject: x\r\nDate: not a date\r\n\r\n")["date"], "")

    def test_text_of_html_keeps_link_urls(self):
        text = g.text_of(HTML_ALERT)
        self.assertIn("Solutions Architect <https://www.linkedin.com/jobs/view/123>", text)
        self.assertIn("Acme & partners", text)
        self.assertNotIn("color:red", text)
        self.assertNotIn("<p>", text)

    def test_text_of_truncates(self):
        self.assertLessEqual(len(g.text_of(HTML_ALERT, max_chars=10)), 10)

    def test_build_reply_threads_and_quotes(self):
        reply = g.build_reply(HTML_ALERT, "Thanks, happy to talk.")
        self.assertEqual(reply["Subject"], "Re: Solutions Architect at Acme")
        self.assertEqual(reply["In-Reply-To"], "<abc@linkedin.com>")
        self.assertIn("<abc@linkedin.com>", reply["References"])
        self.assertIn("jobalerts-noreply@linkedin.com", reply["To"])
        self.assertIn("Alex Example", reply["From"])
        plain = reply.get_body(preferencelist=("plain",)).get_content()
        self.assertTrue(plain.startswith("Thanks, happy to talk."))

    def test_build_reply_html_keeps_original_html_untouched_in_one_blockquote(self):
        # The history stays below in the style it was, never re-typed or ">"-prefixed.
        reply = g.build_reply(HTML_ALERT, "Thanks, happy to talk.\nBest, Alex")
        body = reply.get_body(preferencelist=("html",)).get_content()
        self.assertLess(body.index("Thanks, happy to talk."), body.index("<blockquote"))
        self.assertEqual(body.count("<blockquote"), 1)
        self.assertIn('<a href="https://www.linkedin.com/jobs/view/123">Solutions Architect</a>', body)
        self.assertIn("wrote:", body)
        self.assertNotRegex(body, r"(^|<br>|\n)&gt; ")  # no ">"-prefixed quote lines

    def test_build_reply_keeps_cc_recipients_but_not_me(self):
        raw = HTML_ALERT.replace(b"Message-ID:", b"Cc: Abdul Rehman <cc@example.com>, alex@example.com\r\nMessage-ID:")
        reply = g.build_reply(raw, "x")
        self.assertIn("cc@example.com", reply["Cc"])
        self.assertNotIn("alex@example.com", reply["Cc"])

    def test_build_reply_plain_original_is_escaped_in_html(self):
        raw = (b"From: Pat <pat@example.com>\r\nSubject: Walkthrough\r\nMessage-ID: <m1@x.com>\r\n"
               b"Content-Type: text/plain; charset=utf-8\r\n\r\nCan you do <Tuesday>?")
        body = g.build_reply(raw, "Yes").get_body(preferencelist=("html",)).get_content()
        self.assertIn("Can you do &lt;Tuesday&gt;?", body)

    def test_build_reply_keeps_existing_re_prefix(self):
        raw = HTML_ALERT.replace(b"Subject: Solutions", b"Subject: RE: Solutions")
        self.assertEqual(g.build_reply(raw, "x")["Subject"], "RE: Solutions Architect at Acme")

    def test_password_missing_exits_with_fix(self):
        done = mock.Mock(returncode=44, stdout="")
        with mock.patch.object(g.subprocess, "run", return_value=done):
            with self.assertRaises(SystemExit) as ctx:
                g.password()
        self.assertIn("gmail_client.py setup", str(ctx.exception))


def _alternative(plain, html_doc):
    from email.message import EmailMessage
    m = EmailMessage()
    m["From"], m["Subject"] = "LinkedIn <jobs-noreply@linkedin.com>", "Your application to X at Y"
    m.set_content(plain)
    m.add_alternative(html_doc, subtype="html")
    return m.as_bytes()


class StubPlainPartTests(unittest.TestCase):
    """LinkedIn sends a stub text/plain (preheader + footer); the real message is only in the HTML."""

    def test_stub_plain_falls_back_to_html_and_drops_invisible_padding(self):
        plain = "Your update from Globex Corp\n" + "Learn why: https://www.linkedin.com/help/x?" + "a" * 400
        html_doc = ("<html><body><p>Your update from Globex Corp</p><p>" + "\u034f \u200b " * 300 + "</p>"
                    "<p>Unfortunately, we will not be moving forward with your application.</p></body></html>")
        text = g.text_of(_alternative(plain, html_doc), max_chars=400)
        self.assertIn("Unfortunately, we will not be moving forward", text)
        self.assertNotIn("\u034f", text)

    def test_links_false_keeps_long_tracking_urls_out_of_the_character_window(self):
        html_doc = ('<p><a href="https://www.linkedin.com/comm/feed/?' + "x" * 1500 + '">Logo</a></p>'
                    "<p>Unfortunately, we will not be moving forward with your application.</p>")
        raw = _alternative("stub " + "a" * 400, html_doc)
        self.assertNotIn("Unfortunately", g.text_of(raw, max_chars=200))
        self.assertIn("Unfortunately", g.text_of(raw, max_chars=200, links=False))

    def test_real_plain_part_still_wins_over_equivalent_html(self):
        body = "Hi Alex, are you free on Tuesday for a quick call? " * 4
        text = g.text_of(_alternative("PLAINMARK " + body, "<p>HTMLMARK " + body + "</p>"))
        self.assertIn("PLAINMARK", text)
        self.assertNotIn("HTMLMARK", text)

    def test_html_only_message_has_invisible_padding_stripped(self):
        raw = (b"Subject: x\r\nMIME-Version: 1.0\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
               + "<p>Hello</p><p>\u034f \u034f \u200b</p><p>World</p>".encode())
        self.assertEqual(g.text_of(raw).replace("\n", " ").split(), ["Hello", "World"])

    def test_non_numeric_id_exits_with_a_clear_message_not_a_traceback(self):
        with self.assertRaises(SystemExit) as ctx:
            g._uid_for("")
        self.assertIn("Gmail id", str(ctx.exception))


class ReadManyTests(unittest.TestCase):
    def test_read_many_maps_ids_with_one_body_fetch(self):
        conn = mock.Mock()

        def uid(cmd, *args):
            if cmd == "FETCH" and args[1] == "(X-GM-MSGID)":
                return "OK", [b"1 (X-GM-MSGID 111 UID 7)", b"2 (X-GM-MSGID 222 UID 9)"]
            return "OK", [(b"1 (UID 7 BODY[] {10}", HTML_ALERT), b")"]
        conn.uid.side_effect = uid
        with mock.patch.object(g, "_conn", return_value=conn), mock.patch.object(g, "_select"):
            out = g.read_many(["111", "333"], "trash", 40)
        self.assertEqual(set(out), {"111"})
        self.assertTrue(out["111"].startswith("New job"))
        body_fetches = [c for c in conn.uid.call_args_list if c.args[0] == "FETCH" and c.args[2] == "(UID BODY.PEEK[])"]
        self.assertEqual(len(body_fetches), 1)


class DraftNewTests(unittest.TestCase):
    def _pdf(self, name, payload=b"%PDF-1.4 test"):
        import tempfile
        from pathlib import Path
        path = Path(tempfile.mkdtemp()) / name
        path.write_bytes(payload)
        return str(path)

    def test_build_message_has_headers_body_first_and_named_attachments(self):
        cv, cover = self._pdf("main_x.pdf", b"%PDF-1 cv"), self._pdf("cover_x.pdf", b"%PDF-1 cover")
        msg = g.build_message("careers@simlocal.com", "Sim Local - Senior Product Designer, UI/UX", "Hello,\nHere is my CV.",
                              [(cv, "Alex Example - Resume.pdf"), (cover, "Alex Example - Cover Letter.pdf")])
        self.assertEqual(msg["To"], "careers@simlocal.com")
        self.assertEqual(msg["Subject"], "Sim Local - Senior Product Designer, UI/UX")
        self.assertIn("alex@example.com", msg["From"])
        self.assertIsNone(msg["Cc"])
        self.assertTrue(msg.get_body(preferencelist=("plain",)).get_content().startswith("Hello,"))
        names = [a.get_filename() for a in msg.iter_attachments()]
        self.assertEqual(names, ["Alex Example - Resume.pdf", "Alex Example - Cover Letter.pdf"])
        self.assertTrue(all(a.get_content_type() == "application/pdf" for a in msg.iter_attachments()))
        self.assertEqual(next(msg.iter_attachments()).get_content(), b"%PDF-1 cv")

    def test_draft_new_appends_once_to_drafts_and_never_retries(self):
        calls = []
        with mock.patch.object(g, "_imap", side_effect=lambda *a, **k: calls.append((a, k)) or ("OK", [b""])), \
                mock.patch.object(g, "folder", return_value="[Gmail]/Drafts"):
            self.assertTrue(g.draft_new("a@b.c", "Subject", "Body", []))
        (args, kwargs), = calls
        self.assertEqual(args[0], "append")
        self.assertEqual(args[1], '"[Gmail]/Drafts"')
        self.assertIn("\\Draft", args[2])
        self.assertIs(kwargs.get("retry"), False)


class ImapErrorTests(unittest.TestCase):
    def setUp(self):
        g._SELECTED = ("INBOX", True)
        self.addCleanup(setattr, g, "_SELECTED", None)

    def _conns(self, *conns):
        seq = list(conns)
        return lambda: seq.pop(0) if len(seq) > 1 else seq[0]

    def test_dropped_connection_reconnects_once_and_reselects_the_folder(self):
        dead, live = mock.Mock(), mock.Mock()
        dead.uid.side_effect = g.imaplib.IMAP4.abort("socket error: EOF")
        live.uid.return_value = ("OK", [b"7"])
        with mock.patch.object(g, "_conn", side_effect=self._conns(dead, live)):
            self.assertEqual(g._imap("uid", "SEARCH", "ALL"), ("OK", [b"7"]))
        live.select.assert_called_once_with('"INBOX"', readonly=True)

    def test_second_failure_exits_with_one_line_not_a_traceback(self):
        dead = mock.Mock()
        dead.uid.side_effect = g.imaplib.IMAP4.abort("socket error: EOF")
        with mock.patch.object(g, "_conn", return_value=dead):
            with self.assertRaises(SystemExit) as ctx:
                g._imap("uid", "SEARCH", "ALL")
        self.assertIn("connection", str(ctx.exception).lower())

    def test_rejected_command_exits_with_one_line(self):
        conn = mock.Mock()
        conn.uid.side_effect = g.imaplib.IMAP4.error("UID command error: BAD")
        with mock.patch.object(g, "_conn", return_value=conn):
            with self.assertRaises(SystemExit) as ctx:
                g._imap("uid", "SEARCH", "ALL")
        self.assertIn("rejected", str(ctx.exception).lower())

    def test_append_is_never_retried_so_a_draft_cannot_be_duplicated(self):
        dead = mock.Mock()
        dead.append.side_effect = g.imaplib.IMAP4.abort("socket error: EOF")
        with mock.patch.object(g, "_conn", return_value=dead):
            with self.assertRaises(SystemExit):
                g._imap("append", "Drafts", "", "", b"x", retry=False)
        self.assertEqual(dead.append.call_count, 1)

    def test_select_passes_readonly_through_and_remembers_the_folder(self):
        # Unlike the other tests this does NOT patch _select: the first refactor broke exactly this path.
        conn = mock.Mock()
        conn.select.return_value = ("OK", [b"3"])
        with mock.patch.object(g, "_conn", return_value=conn), mock.patch.object(g, "folder", return_value="INBOX"):
            g._select("inbox", readonly=False)
        conn.select.assert_called_once_with('"INBOX"', readonly=False)
        self.assertEqual(g._SELECTED, ("INBOX", False))

    def test_non_ascii_query_uses_a_utf8_literal(self):
        conn = mock.Mock()
        conn.uid.return_value = ("OK", [b""])
        with mock.patch.object(g, "_conn", return_value=conn), mock.patch.object(g, "_select"):
            g.search("from:José newer_than:3d")
        self.assertEqual(conn.uid.call_args.args, ("SEARCH", "CHARSET", "UTF-8", "X-GM-RAW"))
        self.assertEqual(conn.literal, "from:José newer_than:3d".encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
