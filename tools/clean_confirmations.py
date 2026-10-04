"""Log and trash application-confirmation emails in Gmail (tools/gmail_client.py).

After an application is recorded as sent, its automatic confirmation email ("your application
was sent to X", "Thank you for applying", "Grazie per la tua candidatura") has no further use in
the inbox. This tool finds those emails, matches each to an `applied` tracker row by company,
appends the email's date, sender and subject to that application's `confirmation.txt` (so the
evidence survives), then moves the email to Trash (recoverable).

Emails that match no applied row are listed and left alone. Rejections, emails from a person
and account-activation emails never match the confirmation patterns, so they are kept.

Rejections are handled separately and only ever the safe way round: the tracker row is updated
to `status=rejected` with a dated note FIRST, and only once that write has succeeded does the
email get trashed - never the other way, since the email is often the only record of the outcome
(two rejection notifications once sat in the inbox with their tracker rows still reading `applied`).

"Your application was viewed by X" notifications (LinkedIn) carry no evidentiary value - unlike a
confirmation, there's nothing worth preserving - so they are matched to an applied/interview/offer
tracker row the same way confirmations are (never trashed on subject alone) and trashed outright,
with no tracker mutation and no confirmation.txt entry (a recurring noise email).

    python3 tools/clean_confirmations.py            # dry run: show what would happen
    python3 tools/clean_confirmations.py --delete   # log, then move to Trash
    python3 tools/clean_confirmations.py --reject   # dry run: also show rejection matches
    python3 tools/clean_confirmations.py --reject --delete
        # update matched tracker rows to status=rejected, then trash the confirmations AND
        # the matched rejection emails
    # --reject also reads Gmail's Trash (last 14 days, newest 400): a rejection the user trashed themselves sets
    # its still-open tracker row to `rejected`; ambiguous or invite-like emails are reported, not filed.
    python3 tools/clean_confirmations.py --trash-alert <gmail id> --reason "<why>"
        # trash one handled job-alert email; the reason is appended to reports/mail-cleanup.log
    python3 tools/clean_confirmations.py --reject --delete --settle 6
        # THE END-OF-CYCLE COMMAND. Receipts arrive 1-3 minutes AFTER a send, so a single pass run
        # right after submitting misses them (cleanup must never be a manual
        # afterthought). --settle keeps re-running the
        # pass every ~60s for up to N minutes, stops early once every fresh send has its receipt
        # trashed, and lists any send whose receipt never showed up (some boards send none).
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from tools import gmail_client as gmail
except ImportError:  # run as a script: tools/ itself is on sys.path
    import gmail_client as gmail

ROOT = Path(__file__).resolve().parent.parent
TRACKER = ROOT / "profile/tracker.csv"
APPS = ROOT / "profile/applications"
LOG = ROOT / "reports/mail-cleanup.log"
ALERTS = ROOT / "profile/job_alerts/alerts.json"
SEP = "\x1f"

CONFIRMATION = re.compile(
    r"your application was sent to|thank you for applying|thanks for applying|application received"
    r"|we received your application|grazie per la tua candidatura|candidatura ricevuta"
    r"|acknowledg(e)?ment - application|application has been received|thanks for your interest in"
    r"|we've received your application|your application has been submitted"
    r"|what's next|application (was )?(successfully )?submitted|received your application"
    r"|thanks? for (your )?application|thank you for your application|we got your application"
    r"|application confirmation|your application (is|was) (complete|received)|successfully applied"
    r"|thanks? for submitting your application|^job application for ", re.I)
# Receipts from ATS mailers whose subject is just "<role> - <company>" (Workable). Only treated as a
# receipt when it lands on the same day as the application, because the same mailer also sends
# rejections and interview invites, which must never be auto-trashed.
RECEIPT_SENDERS = re.compile(r"(candidates|inbound)\.workablemail\.com", re.I)
# A confirmation-shaped subject is kept unprocessed by the confirmation path if it also matches
# one of these - it needs the user's eyes (handled instead, deliberately, by --reject) or is
# simply not a job-application email at all.
KEEP = re.compile(r"unfortunately|not (be )?moving forward|regret|activate|verify your|interview", re.I)
# Genuine final-rejection language only - never matches an interview invite or a request for info.
REJECTION = re.compile(
    r"unfortunately|not (be )?moving forward|decided not to (progress|move forward)"
    r"|regret to inform|will not be (moving|proceeding)|not (been )?selected|not successful"
    r"|other candidates|pursue other candidates|non proseguiremo|non procederemo", re.I)
# A rejection email must never also look like an interview invite, a request for more info, or an
# account/verification email - those need the user, not automated closure.
REJECTION_KEEP = re.compile(r"interview|schedule a call|next steps|verify your|activate|assessment", re.I)
# Tracker statuses a rejection can close. Never `drafted` (nothing was sent) or an already-final one.
OPEN_FOR_REJECTION = {"applied", "interview", "offer"}
# Pure-noise "someone looked at your application" pings - safe to trash outright once matched.
VIEWED = re.compile(r"your application was viewed by", re.I)
SUFFIXES = re.compile(r"\b(gmbh|ltd|limited|llc|inc|sas|srl|s\.r\.l|spa|ag|bv|plc|digital|group|portugal"
                      r"|italia|recruitment|services|the)\b", re.I)


# The inbox is read with one Gmail search per pass over the last INBOX_SCAN_DAYS days (newest
# INBOX_SCAN_LIMIT messages), then filtered by --days in Python. Nothing older than the newest
# messages can slip through a fixed-size window.
INBOX_SCAN_DAYS = 14
INBOX_SCAN_LIMIT = 500
# Trash is scanned too (the user sometimes trashes rejection emails themselves, so the
# tracker would keep saying `applied`).
TRASH_SCAN_LIMIT = 400
TRASH_DAYS = 14
# Subjects worth opening in Trash: anything that can carry a hiring decision. Receipts, job alerts
# and "viewed by" pings are excluded earlier, in Python, by CONFIRMATION / VIEWED / alert senders.
OUTCOME_SUBJECT = re.compile(
    r"update|your interest|important info|information about your application|regarding your application"
    r"|about your application|follow-up|status of your|unfortunately|your application (at|to|with|for)|candidacy"
    r"|thank you for your (application|interest)|thanks for your interest|application for|^re:", re.I)
NOT_OUTCOME_SENDER = re.compile(
    r"vinted|subito|linkedin job alerts|testflight|newsletter|offerzen|joinrs|property|spotify|dribbble|mobbin"
    r"|amazon|inpost|fineco|revolut|lhv|quora|grok|siae|paypal|ebay|google|apple|github|tiktok|kraken", re.I)
# Words that make a Trash email a task or an invite rather than a closed door: report it, never file it.
NEEDS_EYES = re.compile(r"interview|schedule a call|questionnaire|assessment|next steps|book a (time|slot)|calendly", re.I)


def _parse_mail_date(text):
    """Parse gmail_client's local "YYYY-MM-DD HH:MM:SS" date.

    Returns None on anything unexpected - callers keep the row rather than risk dropping mail on a
    parsing miss; erring toward inclusion just means handling a slightly wider window.
    """
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


_SCAN_CACHE = None


def inbox(days, refresh=False):
    """The cached scan (one Gmail search per pass), filtered to the last `days` days."""
    global _SCAN_CACHE
    if _SCAN_CACHE is None or refresh:
        _SCAN_CACHE = gmail.search(f"newer_than:{max(days, INBOX_SCAN_DAYS)}d", "inbox", INBOX_SCAN_LIMIT)
    cutoff = datetime.now() - timedelta(days=days)
    out = []
    for row in _SCAN_CACHE:
        parsed = _parse_mail_date(row["date"])
        if parsed is None or parsed > cutoff:
            out.append(row)
    return out


def trash(mail):
    """Move one inbox message to Gmail's Trash, by its stable Gmail id."""
    ok = gmail.trash(mail["id"])
    if ok and _SCAN_CACHE is not None:
        _SCAN_CACHE[:] = [m for m in _SCAN_CACHE if m["id"] != mail["id"]]
    return ok


def norm(text):
    text = SUFFIXES.sub(" ", text.lower())
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def slug(value):
    value = "".join(c for c in value.lower().replace(" ", "_") if c.isalnum() or c == "_")
    return re.sub("_+", "_", value).strip("_")


def read_tracker():
    with TRACKER.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def write_tracker(fields, rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    fd, tmp = tempfile.mkstemp(dir=TRACKER.parent, prefix=".tracker-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(output.getvalue())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, TRACKER)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def applied_rows():
    _, rows = read_tracker()
    return [r for r in rows if (r.get("status") or "").strip().lower() == "applied"]


def open_rows_for_rejection():
    _, rows = read_tracker()
    return [r for r in rows if (r.get("status") or "").strip().lower() in OPEN_FOR_REJECTION]


def matches(mail, rows):
    """Applied rows whose company appears in the email's subject or sender."""
    hay = norm(mail["subject"] + " " + mail["sender"])
    hits = []
    for r in rows:
        name = norm(r["company"])
        if name and (re.search(rf"\b{re.escape(name)}\b", hay) or re.search(rf"\b{re.escape(name.split()[0])}\b", hay)
                     and len(name.split()[0]) > 3):
            hits.append(r)
    # Prefer the most recent application(s) to that company.
    if hits:
        latest = max(r["date"] for r in hits)
        hits = [r for r in hits if r["date"] == latest]
    return hits


def folder(row):
    path = APPS / f"{slug(row['company'])}_{slug(row['role'])}"
    return path if path.exists() else None


def clean_note(text):
    """Strip commas/quotes/linebreaks so the note can't corrupt the CSV (see /outcome's rule)."""
    text = re.sub(r"[\r\n]+", " ", text)
    text = text.replace(",", " -").replace('"', "'")
    return re.sub(r"\s+", " ", text).strip()


def handle_rejections(days, do_delete):
    rows = open_rows_for_rejection()
    for mail in inbox(days):
        subject = mail["subject"]
        if not REJECTION.search(subject) or REJECTION_KEEP.search(subject):
            continue
        hits = matches(mail, rows)
        if not hits:
            print(f"REJECTION, no open tracker row matched (kept): {mail['date']} | {mail['sender']} | {subject}")
            continue
        if len(hits) > 1:
            print(f"REJECTION matched {len(hits)} open rows, ambiguous (kept): {subject}")
            continue
        row = hits[0]
        label = f"{row['company']} / {row['role']}"
        if not do_delete:
            print(f"would mark rejected + trash: {subject}  ->  {label}")
            continue
        # Update the tracker BEFORE touching the mailbox - the email is often the only record.
        fields, all_rows = read_tracker()
        target = next((r for r in all_rows if r.get("company") == row.get("company")
                       and r.get("role") == row.get("role") and r.get("date") == row.get("date")), None)
        if target is None:
            print(f"REJECTION matched row disappeared from tracker, skipped: {label}")
            continue
        note = clean_note(f"{date.today()} rejected - email {mail['date']!r} subject {subject!r}")
        target["status"] = "rejected"
        target["notes"] = "; ".join(filter(None, [target.get("notes"), note]))
        write_tracker(fields, all_rows)
        ok = trash(mail)
        print(("rejected+trashed: " if ok else "tracker updated, email NOT trashed: ") + f"{subject}  ->  {label}")


def handle_viewed(days, do_delete):
    rows = open_rows_for_rejection()  # same statuses are meaningful here: applied/interview/offer
    for mail in inbox(days):
        subject = mail["subject"]
        if not VIEWED.search(subject):
            continue
        hits = matches(mail, rows)
        if not hits:
            print(f"VIEWED, no open tracker row matched (kept): {mail['date']} | {mail['sender']} | {subject}")
            continue
        label = ", ".join(f"{r['company']} / {r['role']}" for r in hits)
        if not do_delete:
            print(f"would trash (viewed-by notification): {subject}  ->  {label}")
            continue
        print(("trashed: " if trash(mail) else "NOT trashed: ") + f"{subject}  ->  {label}")


def _norm_subject(text):
    return text.replace("\u2019", "'").replace("\u2018", "'")


def _same_day(mail, row):
    parsed = _parse_mail_date(mail["date"])
    return parsed is not None and parsed.date().isoformat() == (row.get("date") or "")[:10]


def is_receipt(mail, rows):
    """A confirmation by subject, or a same-day Workable '<role> - <company>' receipt."""
    subject = _norm_subject(mail["subject"])
    if KEEP.search(subject):
        return False
    if CONFIRMATION.search(subject):
        return True
    if RECEIPT_SENDERS.search(mail["sender"]) and not REJECTION.search(subject) \
            and not REJECTION_KEEP.search(subject):
        return any(_same_day(mail, r) for r in matches(mail, rows))
    return False


def confirmation_pass(days, do_delete):
    rows = applied_rows()
    for mail in inbox(days):
        subject = mail["subject"]
        if not is_receipt(mail, rows):
            continue
        hits = [(r, folder(r)) for r in matches(mail, rows)]
        hits = [(r, p) for r, p in hits if p]
        if not hits:
            print(f"UNMATCHED (kept): {mail['date']} | {mail['sender']} | {subject}")
            continue
        names = ", ".join(p.name for _, p in hits)
        if not do_delete:
            print(f"would log+trash: {subject}  ->  {names}")
            continue
        line = f"Confirmation email (logged before moving it to Trash): {mail['date']}, from {mail['sender']}, subject \"{subject}\"\n"
        for _, p in hits:
            with (p / "confirmation.txt").open("a", encoding="utf-8") as f:
                f.write(line)
        print(("trashed: " if trash(mail) else "logged, NOT trashed: ") + f"{subject}  ->  {names}")


_ROLE_STOP = {"the", "and", "for", "of", "a", "an", "senior", "staff", "principal", "lead", "remote", "m", "f", "d",
              "x", "mfd", "eu", "emea"}


def _role_tokens(role):
    return [w for w in norm(role).split() if w not in _ROLE_STOP and (len(w) > 2 or w.isdigit())]


def _trash_scan(days):
    return gmail.search(f"newer_than:{days}d", "trash", TRASH_SCAN_LIMIT)


def _trash_bodies(ids):
    """First ~1500 characters of each Trash message body, keyed by Gmail id. Words only: LinkedIn-style
    tracking URLs would otherwise fill the window before the decision sentence."""
    return gmail.read_many(ids, "trash", 1500, links=False)


# LinkedIn's own wording: the subject already names the role and the company.
LINKEDIN_SUBJECT = re.compile(r"^your application to .+ at .+", re.I)


def _decision_text(subject, body):
    """The part of a body allowed to name the company in a rejection.

    LinkedIn rejections end with a "Top jobs looking for your skills" block of OTHER companies, and one of
    them was Example Corp, a live interview: matching on the first 700 characters would file that row as
    rejected. So a LinkedIn-style subject ("Your application to <role> at <company>") matches on the
    subject alone, and any other body only on the sentences around the rejection wording.
    """
    if LINKEDIN_SUBJECT.match(subject):
        return ""
    hit = REJECTION.search(body)
    if not hit:
        return body[:300]
    return body[max(0, hit.start() - 400):hit.end() + 150]


def handle_trash_outcomes(days, do_delete):
    """Rejections the user trashed themselves: set the matched open tracker row to `rejected`.

    Only open rows (applied/interview/offer) are touched, so a message already handled is a no-op on
    the next run. A message that names a company with several open rows is narrowed by the role's
    words and otherwise reported as ambiguous, never guessed. An interview invite, a task or a person's
    reply found in Trash is reported ("needs eyes"), not filed. Nothing is moved: it is already in Trash.
    """
    rows = open_rows_for_rejection()
    cutoff = datetime.now() - timedelta(days=days)
    cands = []
    for m in _trash_scan(days):
        parsed = _parse_mail_date(m["date"])
        if parsed is not None and parsed < cutoff:
            continue
        subject = _norm_subject(m["subject"])
        if NOT_OUTCOME_SENDER.search(m["sender"]) or VIEWED.search(subject) or KEEP.search(subject) \
                and not REJECTION.search(subject):
            continue
        if CONFIRMATION.search(subject) and not REJECTION.search(subject):
            continue
        if OUTCOME_SUBJECT.search(subject):
            cands.append(m)
    bodies = _trash_bodies([m["id"] for m in cands])
    filed = flagged = 0
    for m in cands:
        subject, body = _norm_subject(m["subject"]), bodies.get(m["id"], "")
        if not REJECTION.search(subject + " " + body):
            if NEEDS_EYES.search(subject + " " + body[:600]) and matches({"subject": subject + " " + body[:600],
                                                                           "sender": m["sender"]}, rows):
                flagged += 1
                print(f"TRASH needs eyes (not a rejection; not filed): {m['date']} | {m['sender']} | {subject}")
            continue
        if REJECTION_KEEP.search(subject):
            continue
        hay = norm(f"{subject} {m['sender']} {_decision_text(subject, body)}")
        words = set(hay.split())

        def role_share(r):
            toks = _role_tokens(r["role"])
            return sum(w in words for w in toks) / len(toks) if toks else 0.0

        hits = [r for r in rows if norm(r["company"]) and re.search(rf"\b{re.escape(norm(r['company']))}\b", hay)]
        if not hits:
            continue
        # Company is not enough: Constructor has several roles, and the one still open is not necessarily
        # the one this email is about. The role's own words have to appear too.
        confirmed = [r for r in hits if role_share(r) >= 0.6]
        if not confirmed:
            print(f"TRASH rejection, role not confirmed (not filed): {m['date']} | {subject} -> "
                  + "; ".join(f"{r['company']} / {r['role']}" for r in hits))
            continue
        hits = confirmed
        if len(hits) > 1:
            best = max(role_share(r) for r in hits)
            hits = [r for r in hits if role_share(r) == best]
        if len(hits) > 1:
            print(f"TRASH rejection matched {len(hits)} open rows, ambiguous (not filed): {m['date']} | {subject} -> "
                  + "; ".join(f"{r['company']} / {r['role']}" for r in hits))
            continue
        row = hits[0]
        label = f"{row['company']} / {row['role']}"
        if not do_delete:
            print(f"would mark rejected (found in Trash): {subject}  ->  {label}")
            continue
        fields, all_rows = read_tracker()
        target = next((r for r in all_rows if r.get("company") == row.get("company")
                       and r.get("role") == row.get("role") and r.get("date") == row.get("date")), None)
        if target is None:
            continue
        note = clean_note(f"{date.today()} rejected - email {m['date']!r} subject {subject!r} (found in Trash)")
        target["status"] = "rejected"
        target["notes"] = "; ".join(filter(None, [target.get("notes"), note]))
        write_tracker(fields, all_rows)
        rows = open_rows_for_rejection()  # a second email for the same row must not re-match it
        filed += 1
        print(f"rejected (found in Trash): {subject}  ->  {label}")
    if cands:
        print(f"trash scan: {len(cands)} outcome-like message(s) read, {filed} row(s) set to rejected, "
              f"{flagged} need eyes.")


# Tracker statuses that settle an alert role: a decision was made, the alert email is no longer needed.
# `drafted` is not one of them - that role is still waiting on the user.
ALERT_SETTLED = {"applied", "interview", "offer", "rejected", "skipped", "withdrawn", "parked"}


def _log_alert(mail, reason):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M} trashed alert | {mail.get('date', '')} | {mail.get('sender', '')} | "
                f"{mail.get('subject', '')} | {reason}\n")


def _alert_role_done(role, rows, since):
    """A role is settled by its own status, or by a tracker row for this posting: same job URL, or same
    company with most of the role's words and dated on/after the alert (an older application to a
    similar title is a different posting). `drafted` is never settled - it is waiting on the user."""
    status = (role.get("status") or "").strip().lower()
    if status in ("sent", "skipped"):
        return True
    if status == "drafted":
        return False
    url = (role.get("url") or "").strip().rstrip("/")
    company, toks = norm(role.get("company") or ""), _role_tokens(role.get("role") or "")
    for r in rows:
        if (r.get("status") or "").strip().lower() not in ALERT_SETTLED:
            continue
        if url and (r.get("source") or "").strip().rstrip("/") == url:
            return True
        theirs = norm(r.get("company") or "")
        if not toks or not company or not (company == theirs or re.search(rf"\b{re.escape(company)}\b", theirs)):
            continue
        if (r.get("date") or "")[:10] < since[:10]:
            continue
        rtoks = set(_role_tokens(r.get("role") or ""))
        if sum(t in rtoks for t in toks) / len(toks) >= 0.6:
            return True
    return False


def _write_alerts(alerts):
    fd, tmp = tempfile.mkstemp(dir=ALERTS.parent, prefix=".alerts-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(alerts, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, ALERTS)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def handle_alerts(do_delete):
    """Trash job-alert emails whose roles are all handled (profile/job_alerts/alerts.json, written by /job-alerts)."""
    if not ALERTS.exists():
        return
    try:
        alerts = json.loads(ALERTS.read_text(encoding="utf-8") or "{}")
        if not isinstance(alerts, dict):
            raise ValueError("top level is not an object")
    except ValueError as exc:  # JSONDecodeError is a ValueError; keep the other passes running
        print(f"ALERTS file unreadable, alert pass skipped ({exc}): {ALERTS}")
        return
    _, rows = read_tracker()
    changed = False
    for msgid, entry in list(alerts.items()):
        if not isinstance(entry, dict):
            print(f"ALERT entry {msgid} is not an object (kept)")
            continue
        roles = entry.get("roles") or []
        label = f"{entry.get('date', '')} | {entry.get('sender', '')} | {entry.get('subject', '')}"
        if not isinstance(roles, list) or not all(isinstance(r, dict) for r in roles):
            print(f"ALERT has malformed roles (kept): {label}")
            continue
        # An interview invite or a person's reply recorded as an "alert" must never be auto-trashed.
        if KEEP.search(entry.get("subject") or "") or NEEDS_EYES.search(entry.get("subject") or ""):
            print(f"ALERT looks like a person or an invite, needs eyes (kept): {label}")
            continue
        skip = (entry.get("skip_reason") or "").strip()
        pending = [r for r in roles if not _alert_role_done(r, rows, entry.get("date") or "")]
        if not skip and not roles:
            print(f"ALERT has no roles recorded (kept): {label}")
            continue
        if pending:
            print(f"ALERT still open ({len(pending)} of {len(roles)} role(s) pending): {label} -> "
                  + "; ".join(f"{r.get('company')} / {r.get('role')}" for r in pending))
            continue
        reason = skip or "all roles handled: " + "; ".join(
            f"{r.get('company')} / {r.get('role')} = {r.get('status') or 'tracker'}" for r in roles)
        if not do_delete:
            print(f"would trash handled alert: {label}")
            continue
        if gmail.trash(msgid):
            _log_alert(entry, reason)
            print(f"trashed handled alert: {label}")
        else:
            print(f"handled alert already gone from the inbox (entry dropped): {label}")
        del alerts[msgid]
        changed = True
    if changed:
        _write_alerts(alerts)


_ALERTS_DONE = False


_TRASH_DONE = False


def one_pass(args):
    global _SCAN_CACHE, _TRASH_DONE, _ALERTS_DONE
    _SCAN_CACHE = None  # a fresh single scan per pass
    confirmation_pass(args.days, args.delete)
    handle_viewed(args.days, args.delete)
    if not _ALERTS_DONE:  # once per run, not every settle pass
        _ALERTS_DONE = True
        handle_alerts(args.delete)
    if args.reject:
        handle_rejections(args.days, args.delete)
        if not _TRASH_DONE:  # once per run, not every settle pass
            _TRASH_DONE = True
            handle_trash_outcomes(args.trash_days, args.delete)


def pending_receipts(window_minutes=120):
    """Fresh sends (confirmation.txt written recently) whose receipt email was never logged."""
    cutoff = datetime.now() - timedelta(minutes=window_minutes)
    waiting = []
    for r in applied_rows():
        p = folder(r)
        if not p or not (p / "confirmation.txt").exists():
            continue
        f = p / "confirmation.txt"
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff and "Confirmation email (logged" not in f.read_text(encoding="utf-8", errors="ignore"):
            continue  # old send, receipt long gone or never sent
        if "Confirmation email (logged" not in f.read_text(encoding="utf-8", errors="ignore") \
                and "mail receipt logged" not in f.read_text(encoding="utf-8", errors="ignore"):
            waiting.append(f"{r['company']} / {r['role']}")
    return waiting


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--delete", action="store_true", help="log and move matched confirmations to Trash")
    ap.add_argument("--reject", action="store_true",
                     help="also find rejection emails, mark the matched tracker row rejected, and trash them")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--trash-days", type=int, default=TRASH_DAYS,
                     help="with --reject, how far back to read Trash for rejections the user trashed themselves")
    ap.add_argument("--settle", type=float, default=0, metavar="MINUTES",
                     help="repeat the pass every ~60s for up to MINUTES, until every fresh send's receipt is "
                          "trashed; then list the sends whose receipt never arrived")
    ap.add_argument("--trash-alert", metavar="MAIL_ID", help="Gmail id of the message (as printed by gmail_client.py search)")
    ap.add_argument("--reason")
    args = ap.parse_args()

    if args.trash_alert:
        if not args.reason:
            sys.exit("--trash-alert needs --reason (every role in it sent, or skipped with a reason)")
        mail = next((m for m in inbox(args.days + 7, refresh=True) if m["id"] == args.trash_alert), None)
        if not mail:
            sys.exit("No inbox message with that id")
        _log_alert(mail, args.reason)
        print("trashed" if trash(mail) else "NOT FOUND in inbox")
        return

    import time
    deadline = time.time() + args.settle * 60
    passes = 0
    while True:
        passes += 1
        one_pass(args)
        if not args.settle or not args.delete:
            return
        waiting = pending_receipts()
        if not waiting:
            print(f"settled after {passes} pass(es): every fresh send has its receipt cleaned.")
            return
        if time.time() >= deadline:
            print("receipt NOT seen (after settle window; some boards send none): " + "; ".join(waiting))
            return
        print(f"pass {passes}: still waiting for {len(waiting)} receipt(s): " + "; ".join(waiting), flush=True)
        time.sleep(60)


if __name__ == "__main__":
    main()
