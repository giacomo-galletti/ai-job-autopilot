"""Gmail access for the job-search tools: IMAP with a Gmail app password. Optional: the rest of the kit
works without it, and this module imports cleanly when Gmail is not configured.

Configuration (nothing personal lives in the code):
    address  JOB_KIT_GMAIL_ADDRESS, else "address" in profile/gmail.json (gitignored with profile/)
    name     JOB_KIT_GMAIL_NAME, else "name" in profile/gmail.json (display name on drafts; optional)
    secret   the app password, looked up in this order: JOB_KIT_GMAIL_APP_PASSWORD (env var, any OS),
             the macOS Keychain (service "ai-job-autopilot-gmail"), then the optional `keyring` package
             (Linux/Windows credential stores). `setup` stores it in the Keychain, or in `keyring`
             when the Keychain is not available.

This is the only module that talks to Gmail. Messages are identified by Gmail's X-GM-MSGID, which
is stable across folders and sessions. Folders are found by their SPECIAL-USE flag, never by name:
this account's Trash is "[Gmail]/Bin", and the name changes with Gmail's interface language.
Reads use BODY.PEEK, so scanning never marks mail as read. Nothing here sends mail.

    python3 tools/gmail_client.py setup                            # store the app password
    python3 tools/gmail_client.py search "newer_than:2d" [--trash|--drafts] [--limit 50]
    python3 tools/gmail_client.py read <id> [--trash|--drafts] [--max 4000]
    python3 tools/gmail_client.py trash <id> [--drafts]                # e.g. a stale reply draft
    python3 tools/gmail_client.py draft-reply <id> < reply.txt     # saved to Drafts, never sent
    python3 tools/gmail_client.py draft-new --to a@b.c --subject S --attach 'path.pdf=Shown Name.pdf' < body.txt
"""

import argparse
import email
import getpass
import html
import imaplib
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.policy import default as POLICY
from email.utils import formataddr, formatdate, getaddresses, make_msgid, parsedate_to_datetime

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "profile" / "gmail.json"
KEYCHAIN_SERVICE = "ai-job-autopilot-gmail"
HOST = "imap.gmail.com"


def _load_identity():
    """(address, display name) from the environment, else profile/gmail.json; empty when unconfigured."""
    cfg = {}
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    address = (os.environ.get("JOB_KIT_GMAIL_ADDRESS") or cfg.get("address") or "").strip()
    name = (os.environ.get("JOB_KIT_GMAIL_NAME") or cfg.get("name") or "").strip()
    return address, name


ACCOUNT, DISPLAY_NAME = _load_identity()


def _account():
    if not ACCOUNT:
        sys.exit("Gmail is not configured (it is optional). Set JOB_KIT_GMAIL_ADDRESS or put "
                 '{"address": "you@example.com"} in profile/gmail.json, then run: '
                 "python3 tools/gmail_client.py setup")
    return ACCOUNT


def _me():
    """The From header for drafts: 'Name <address>' or the bare address."""
    return formataddr((DISPLAY_NAME, _account())) if DISPLAY_NAME else _account()

_LIST_RE = re.compile(r'\((?P<flags>[^)]*)\) "(?P<delim>[^"]*)" (?P<name>.+)$')
_CONN = None
_FOLDERS = None
_SELECTED = None  # (folder name, readonly) of the open folder, re-opened after a reconnect


def parse_list_line(line):
    """'(\\HasNoChildren \\Trash) "/" "[Gmail]/Bin"' -> ({'\\HasNoChildren', '\\Trash'}, '[Gmail]/Bin')."""
    m = _LIST_RE.match(line)
    if not m:
        return set(), None
    name = m["name"].strip()
    if name.startswith('"') and name.endswith('"'):
        name = name[1:-1].replace('\\"', '"')
    return set(m["flags"].split()), name


def _header(value):
    """Decode a header for display. Spam carries unknown charsets and truncated encoded words: one such
    message must never stop a whole scan, so fall back to the raw text."""
    try:
        text = str(make_header(decode_header(str(value or ""))))
    except (LookupError, UnicodeError, ValueError):
        text = str(value or "")
    return re.sub(r"\s+", " ", text).strip()


def summarize(msgid, raw_headers):
    # Decode as UTF-8 first: senders that put raw UTF-8 in headers (no encoded words) would otherwise
    # come out garbled and fail company matching.
    h = email.message_from_string(raw_headers.decode("utf-8", errors="replace"))
    try:
        stamp = parsedate_to_datetime(h["Date"]).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        stamp = ""
    return {"id": str(msgid), "date": stamp, "sender": _header(h["From"]), "subject": _header(h["Subject"])}


# Zero-width and soft-hyphen characters that mailers use as invisible preheader padding.
_INVISIBLE = re.compile("[\u00ad\u034f\u200b-\u200f\u2060\ufeff]")
_LINK = re.compile(r"<https?://[^>]*>|https?://\S+")


def _part_text(part):
    try:
        text = part.get_content()
    except (LookupError, ValueError):
        text = (part.get_payload(decode=True) or b"").decode("utf-8", errors="replace")
    if part.get_content_type() == "text/html":
        text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
        text = re.sub(r"""(?is)<a\s[^>]*href=["']([^"']+)["'][^>]*>(.*?)</a>""",
                      lambda m: f"{re.sub(r'<[^>]+>', ' ', m[2]).strip()} \x02{m[1]}\x03", text)
        text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>", "\n", text)
        # Links were parked as \x02url\x03 so the tag stripper below cannot eat the "<url>".
        text = html.unescape(re.sub(r"<[^>]+>", " ", text)).replace("\x02", "<").replace("\x03", ">")
    return text


def text_of(raw, max_chars=None, links=True):
    """Plain text of a message, with links kept as 'label <url>' (links=False drops them, so long tracking
    URLs cannot fill a max_chars window that a caller wants for words).

    Uses the text/plain part unless it is a stub: LinkedIn, for one, ships a text/plain that is only a
    preheader and a footer, with the actual message (a rejection, say) in the HTML part alone. When the
    plain part carries well under the HTML's worth of words, read the HTML instead.
    """
    msg = email.message_from_bytes(raw, policy=POLICY)
    plain_part, html_part = msg.get_body(preferencelist=("plain",)), msg.get_body(preferencelist=("html",))
    plain = _INVISIBLE.sub("", _part_text(plain_part)) if plain_part is not None else ""
    rich = _INVISIBLE.sub("", _part_text(html_part)) if html_part is not None else ""

    def words(t):
        return len(_LINK.sub("", t).split())

    text = plain if words(plain) >= 0.6 * words(rich) else rich
    if not links:
        text = _LINK.sub("", text)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text[:max_chars] if max_chars else text


def _original_html(msg, plain):
    """The original's HTML as it was (head styles kept, body unwrapped), or its plain text escaped."""
    part = msg.get_body(preferencelist=("html",))
    if part is None:
        return '<div style="white-space:pre-wrap">' + html.escape(plain) + "</div>"
    try:
        doc = part.get_content()
    except (LookupError, ValueError):
        doc = (part.get_payload(decode=True) or b"").decode("utf-8", errors="replace")
    styles = "".join(re.findall(r"(?is)<style\b.*?</style>", doc.split("<body", 1)[0]) if "<body" in doc else [])
    body = re.search(r"(?is)<body[^>]*>(.*)</body>", doc)
    return styles + (body[1] if body else doc)


def build_reply(raw, text, me=None):
    """A reply threaded under the original (In-Reply-To/References), Cc kept, with the original below.

    The original is embedded as its own HTML inside one quote block, the way Gmail and Mail build a
    native reply - never re-typed or ">"-prefixed (the user's rule: keep the old copy in the
    same style it was). The plain-text alternative is only a fallback.
    """
    me = me or _me()
    orig = email.message_from_bytes(raw, policy=POLICY)
    subject = _header(orig["Subject"])
    if not re.match(r"(?i)re:", subject):
        subject = "Re: " + subject
    reply = EmailMessage()
    reply["From"] = me
    reply["To"] = str(orig["Reply-To"] or orig["From"])
    cc = [a for a in getaddresses([str(v) for v in orig.get_all("Cc", [])]) if a[1] and a[1].lower() != _account().lower()]
    if cc:
        reply["Cc"] = ", ".join(formataddr(a) for a in cc)
    reply["Subject"] = subject
    reply["Date"] = formatdate(localtime=True)
    reply["Message-ID"] = make_msgid(domain=_account().split("@")[-1])
    mid = orig["Message-ID"]
    if mid:
        reply["In-Reply-To"] = str(mid)
        reply["References"] = " ".join(filter(None, [str(orig["References"] or "").strip(), str(mid)]))
    attribution = f"On {orig['Date']}, {_header(orig['From'])} wrote:"
    plain = text_of(raw)
    reply.set_content(f"{text.rstrip()}\n\n{attribution}\n" + "\n".join("> " + line for line in plain.splitlines()) + "\n")
    mine = "<br>".join(html.escape(line) for line in text.rstrip().splitlines())
    reply.add_alternative(
        f'<div dir="ltr">{mine}</div><br><div class="gmail_quote"><div dir="ltr" class="gmail_attr">'
        f'{html.escape(attribution)}<br></div><blockquote class="gmail_quote" type="cite" '
        f'style="margin:0px 0px 0px 0.8ex;border-left:1px solid rgb(204,204,204);padding-left:1ex">'
        f"{_original_html(orig, plain)}</blockquote></div>", subtype="html")
    return reply


def build_message(to, subject, text, attachments=(), me=None):
    """A fresh outgoing message (an email application): plain body first, then each (path, shown name) file."""
    me = me or _me()
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = me, to, subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=_account().split("@")[-1])
    msg.set_content(text.rstrip() + "\n")
    for path, name in attachments:
        maintype, _, subtype = (mimetypes.guess_type(name)[0] or "application/octet-stream").partition("/")
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=name)
    return msg


def draft_new(to, subject, text, attachments=()):
    """Save a new message in Drafts for the user to read and send. Never sends; never retried (no duplicates)."""
    msg = build_message(to, subject, text, attachments)
    typ, _ = _imap("append", f'"{folder("drafts")}"', "(\\Draft \\Seen)",
                   imaplib.Time2Internaldate(time.time()), msg.as_bytes(), retry=False)
    return typ == "OK"


def _keychain_password():
    try:
        out = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
                             capture_output=True, text=True)
    except OSError:  # no `security` binary: not macOS
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def _keyring_password():
    try:
        import keyring  # optional: pip install keyring (Linux/Windows credential store)
        return (keyring.get_password(KEYCHAIN_SERVICE, _account()) or "").strip()
    except Exception:  # not installed, or no usable backend
        return ""


def password():
    """The app password: env var, then macOS Keychain, then the optional `keyring` package."""
    pw = (os.environ.get("JOB_KIT_GMAIL_APP_PASSWORD") or "").replace(" ", "") \
        or _keychain_password() or _keyring_password()
    if not pw:
        sys.exit("No Gmail app password found. Set JOB_KIT_GMAIL_APP_PASSWORD, or store it: "
                 "python3 tools/gmail_client.py setup (macOS Keychain, or `keyring` elsewhere)")
    return pw


def _conn():
    global _CONN
    if _CONN is None:
        try:
            conn = imaplib.IMAP4_SSL(HOST, timeout=60)
            conn.login(_account(), password())
        except (imaplib.IMAP4.error, OSError) as exc:
            sys.exit(f"Gmail login failed ({exc}). Check the network, or re-store the app password: "
                     "python3 tools/gmail_client.py setup")
        _CONN = conn
    return _CONN


def _imap(method, *args, literal=None, retry=True, **kwargs):
    """One IMAP call with clean failure. A dropped connection (the --settle loop idles for minutes between
    passes) is re-opened once, with the folder re-selected; anything else exits with a one-line message
    instead of a traceback. retry=False for calls that must not run twice (append would duplicate a draft)."""
    global _CONN
    for attempt in (1, 2):
        try:
            conn = _conn()
            if literal is not None:
                conn.literal = literal
            return getattr(conn, method)(*args, **kwargs)
        except (imaplib.IMAP4.abort, OSError) as exc:
            if attempt == 2 or not retry:
                sys.exit(f"Gmail connection lost ({exc}); run the command again.")
            _CONN = None
            conn = _conn()
            if _SELECTED:
                conn.select(f'"{_SELECTED[0]}"', readonly=_SELECTED[1])
        except imaplib.IMAP4.error as exc:
            sys.exit(f"Gmail rejected the request ({exc}).")


def folder(role):
    """'inbox' | 'trash' | 'drafts' -> this server's folder name."""
    global _FOLDERS
    if role == "inbox":
        return "INBOX"
    if _FOLDERS is None:
        _FOLDERS = {}
        for raw in _imap("list")[1]:
            flags, name = parse_list_line(raw.decode())
            for flag in ("\\Trash", "\\Drafts"):
                if flag in flags:
                    _FOLDERS[flag[1:].lower()] = name
    if role not in _FOLDERS:
        sys.exit(f"Gmail reports no folder flagged \\{role.title()}")
    return _FOLDERS[role]


def _select(mailbox, readonly=True):
    global _SELECTED
    name = folder(mailbox)
    typ, _ = _imap("select", f'"{name}"', readonly=readonly)
    if typ != "OK":
        sys.exit(f"Could not open Gmail folder {name}")
    _SELECTED = (name, readonly)


def _uid_for(msgid):
    if not str(msgid).isdigit():
        sys.exit(f"{msgid!r} is not a Gmail id (use the first column printed by: gmail_client.py search ...)")
    typ, data = _imap("uid", "SEARCH", "X-GM-MSGID", str(int(msgid)))
    uids = data[0].split() if typ == "OK" and data and data[0] else []
    return uids[0] if uids else None


def _raw(msgid, mailbox):
    _select(mailbox)
    uid = _uid_for(msgid)
    if not uid:
        return None
    _, data = _imap("uid", "FETCH", uid, "(BODY.PEEK[])")
    return next((part[1] for part in data if isinstance(part, tuple)), None)


def search(query, mailbox="inbox", limit=200):
    """Messages matching a Gmail search (X-GM-RAW), newest first, at most `limit`."""
    _select(mailbox)
    if query.isascii():
        quoted = '"' + query.replace("\\", "\\\\").replace('"', '\\"') + '"'
        typ, data = _imap("uid", "SEARCH", "X-GM-RAW", quoted)
    else:  # accented names: imaplib cannot quote them, so send a UTF-8 literal
        typ, data = _imap("uid", "SEARCH", "CHARSET", "UTF-8", "X-GM-RAW", literal=query.encode("utf-8"))
    uids = data[0].split() if typ == "OK" and data and data[0] else []
    if not uids:
        return []
    uids = uids[-limit:]  # UIDs grow with arrival in the folder: keep the newest
    _, data = _imap("uid", "FETCH", b",".join(uids), "(X-GM-MSGID BODY.PEEK[HEADER.FIELDS (DATE FROM SUBJECT)])")
    rows = []
    for part in data:
        if isinstance(part, tuple):
            found = re.search(rb"X-GM-MSGID (\d+)", part[0])
            if found:
                rows.append(summarize(found[1].decode(), part[1]))
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


def read(msgid, mailbox="inbox", max_chars=None, links=True):
    raw = _raw(msgid, mailbox)
    return text_of(raw, max_chars, links) if raw else ""


def read_many(msgids, mailbox="inbox", max_chars=None, links=True):
    """{id: text} for several messages in one folder: one id lookup and one body fetch, not one per id."""
    wanted = {str(i) for i in msgids}
    if not wanted:
        return {}
    _select(mailbox)
    _, data = _imap("uid", "FETCH", "1:*", "(X-GM-MSGID)")
    uid_of = {}
    for line in data:
        line = line[0] if isinstance(line, tuple) else line
        found = re.search(rb"X-GM-MSGID (\d+).*?UID (\d+)|UID (\d+).*?X-GM-MSGID (\d+)", line or b"")
        if found:
            msgid, uid = (found[1], found[2]) if found[1] else (found[4], found[3])
            if msgid.decode() in wanted:
                uid_of[uid] = msgid.decode()
    if not uid_of:
        return {}
    _, data = _imap("uid", "FETCH", b",".join(uid_of), "(UID BODY.PEEK[])")
    out = {}
    for part in data:
        if isinstance(part, tuple):
            found = re.search(rb"UID (\d+)", part[0])
            if found and found[1] in uid_of:
                out[uid_of[found[1]]] = text_of(part[1], max_chars, links)
    return out


def trash(msgid, mailbox="inbox"):
    """Move one message to Gmail's Trash (recoverable for 30 days). False if it is not in `mailbox`."""
    _select(mailbox, readonly=False)
    uid = _uid_for(msgid)
    if not uid:
        return False
    typ, _ = _imap("uid", "MOVE", uid, f'"{folder("trash")}"')
    return typ == "OK"


def draft_reply(msgid, text, mailbox="inbox"):
    """Save a threaded reply in Drafts. It shows up in any mail client's Drafts too. Never sends."""
    raw = _raw(msgid, mailbox)
    if raw is None:
        return False
    msg = build_reply(raw, text)
    typ, _ = _imap("append", f'"{folder("drafts")}"', "(\\Draft \\Seen)",
                   imaplib.Time2Internaldate(time.time()), msg.as_bytes(), retry=False)
    return typ == "OK"


def setup():
    account = _account()
    pw = getpass.getpass(f"Gmail app password for {account} (input hidden): ").replace(" ", "")
    if not re.fullmatch(r"[a-z]{16}", pw):
        sys.exit("That is not a 16-letter Gmail app password; nothing stored.")
    try:
        subprocess.run(["security", "add-generic-password", "-U", "-a", account, "-s", KEYCHAIN_SERVICE,
                        "-l", "ai-job-autopilot Gmail app password", "-w", pw], check=True, capture_output=True)
        print(f"stored in the Keychain as {KEYCHAIN_SERVICE}")
        return
    except subprocess.CalledProcessError as exc:  # its message would carry the command line, password included
        sys.exit(f"Could not store the password in the Keychain (security exit {exc.returncode}); "
                 "unlock the Keychain and run setup again.")
    except OSError:  # not macOS: fall through to keyring
        pass
    try:
        import keyring
        keyring.set_password(KEYCHAIN_SERVICE, account, pw)
        print(f"stored with keyring as {KEYCHAIN_SERVICE}")
    except Exception:
        sys.exit("No Keychain and no usable `keyring` package. Install keyring (pip install keyring) "
                 "or export JOB_KIT_GMAIL_APP_PASSWORD instead.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=50)
    r = sub.add_parser("read")
    r.add_argument("id")
    r.add_argument("--max", type=int, default=None)
    t = sub.add_parser("trash")
    t.add_argument("id")
    for p in (s, r, t):
        box = p.add_mutually_exclusive_group()
        if p is not t:
            box.add_argument("--trash", action="store_true", help="look in Gmail's Trash (Bin)")
        box.add_argument("--drafts", action="store_true", help="look in Drafts")
    d = sub.add_parser("draft-reply")
    d.add_argument("id")
    n = sub.add_parser("draft-new")
    n.add_argument("--to", required=True)
    n.add_argument("--subject", required=True)
    n.add_argument("--attach", action="append", default=[], metavar="PATH=SHOWN_NAME",
                   help="file to attach and the file name the recipient sees (repeatable)")
    args = ap.parse_args()

    mailbox = "trash" if getattr(args, "trash", False) else "drafts" if getattr(args, "drafts", False) else "inbox"
    if args.cmd == "setup":
        setup()
    elif args.cmd == "search":
        for row in search(args.query, mailbox, args.limit):
            print("\t".join((row["id"], row["date"], row["sender"], row["subject"])))
    elif args.cmd == "read":
        print(read(args.id, mailbox, args.max) or "NOT FOUND")
    elif args.cmd == "trash":
        print("trashed" if trash(args.id, mailbox) else f"NOT FOUND in {mailbox}")
    elif args.cmd == "draft-reply":
        text = sys.stdin.read()
        if not text.strip():
            sys.exit("Reply text goes on stdin; got nothing.")
        print(f"draft saved to {folder('drafts')}" if draft_reply(args.id, text) else "NOT FOUND in inbox")
    elif args.cmd == "draft-new":
        text = sys.stdin.read()
        if not text.strip():
            sys.exit("Message text goes on stdin; got nothing.")
        files = [tuple(a.split("=", 1)) for a in args.attach]
        if any(len(f) != 2 or not f[1] for f in files):
            sys.exit("--attach takes PATH=SHOWN_NAME")
        print(f"draft saved to {folder('drafts')}" if draft_new(args.to, args.subject, text, files) else "draft NOT saved")


if __name__ == "__main__":
    main()
