#!/usr/bin/env python3
"""Local submission ledger. Browser actions remain with the agent; this tool never sends.

prepare snapshots the exact upload package; begin records authorization before a click;
finish records observed evidence; sync repairs tracking after an interrupted local write.
Run from the repository root. See .claude/commands/submit.md for the browser workflow.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
from uuid import uuid4

try:
    from tools.document_checks import cover_letter_problems, cv_problems, pdf_path
except ImportError:  # run as a script: tools/ itself is on sys.path
    from document_checks import cover_letter_problems, cv_problems, pdf_path

PROFILE = "profile/profile.md"
# confirmed: receipt seen. not_submitted: validation stopped the send, fix and re-prepare.
# uncertain: outcome unknown, never retry blindly. refused: the employer declined to take
# the application (duplicate, application limit, closed role) - final, never resend.
RESULTS = ("confirmed", "uncertain", "not_submitted", "refused")


class SubmissionError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".submission-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def save(path, value):
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(value):
    value = "".join(c for c in value.lower().replace(" ", "_") if c.isalnum() or c == "_")
    value = re.sub("_+", "_", value).strip("_")
    if not value:
        raise SubmissionError("Company and role must each contain letters or digits")
    return value


def is_drafted(row):
    return (row.get("status") or "").strip().lower() == "drafted"


def candidate_name(root):
    try:
        text = (root / PROFILE).read_text(encoding="utf-8")
    except OSError:
        return ""
    match = re.search(r"^\s*-\s*\*\*Name:\*\*\s*(.+?)\s*$", text, re.MULTILINE)
    name = match.group(1) if match else ""
    return "" if "[" in name else name  # an unfilled template placeholder


def upload_names(root):
    """The employer sees these names: simple, the same for every application. The attempt
    folder keeps snapshots apart, so uploads always go by full path, never by name."""
    name = re.sub(r"\s+", " ", re.sub(r"[^\w .&'()-]", " ", candidate_name(root))).strip(" .")
    prefix = f"{name} - " if name else ""
    return {"cv.pdf": f"{prefix}Resume.pdf", "cover_letter.pdf": f"{prefix}Cover Letter.pdf",
            "answers.json": "answers.json"}


class Ledger:
    def __init__(self, root, company, role):
        self.root = Path(root).resolve()
        self.company, self.role = company.strip(), role.strip()
        self.folder = self.root / "profile/applications" / f"{slug(company)}_{slug(role)}" / "submission"
        self.path = self.folder / "active.json"
        self.tracker = self.root / "profile/tracker.csv"

    def state(self):
        data = json.loads(self.path.read_text())
        # The per-attempt record is authoritative if a crash interrupted pointer refresh.
        data = json.loads((self.folder / data["attempt"] / "record.json").read_text())
        if (data["company"].casefold(), data["role"].casefold()) != (self.company.casefold(), self.role.casefold()):
            raise SubmissionError("Archive name collision: company/role differs")
        return data

    def persist(self, data):
        # History is written first; active.json is the current pointer/state.
        save(self.folder / data["attempt"] / "record.json", data)
        save(self.path, data)

    def row(self):
        with self.tracker.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        required = {"date", "company", "role", "status", "notes", "cv_file", "cover_letter_file"}
        if not fields or not required.issubset(fields) or any(None in r for r in rows):
            raise SubmissionError("Tracker schema is missing fields or has malformed rows")
        matches = [r for r in rows if r["company"].strip().casefold() == self.company.casefold()
                   and r["role"].strip().casefold() == self.role.casefold()]
        if len(matches) != 1:
            raise SubmissionError("Need exactly one tracker row; resolve duplicates/reapplications first")
        return fields, rows, matches[0]

    def resolve(self, value):
        path = Path(value)
        return path if path.is_absolute() else self.root / path

    def relative(self, value):
        path = self.resolve(value)
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def document_problems(self, row, cv, cover_letter):
        """The upload must be the tracker row's own documents, tailored for this company."""
        problems = cv_problems(self.relative(cv), self.company)
        if cover_letter:
            problems += cover_letter_problems(self.relative(cover_letter), self.company)
        same = lambda a, b: self.resolve(pdf_path(a)).resolve() == self.resolve(pdf_path(b)).resolve()
        recorded_cv = (row.get("cv_file") or "").strip()
        recorded_cover = (row.get("cover_letter_file") or "").strip()
        if not recorded_cv:
            problems.append("the tracker row records no tailored CV; run /apply first")
        elif not same(cv, recorded_cv):
            problems.append(f"--cv {cv} is not the CV the tracker row records ({recorded_cv})")
        if cover_letter and recorded_cover and not same(cover_letter, recorded_cover):
            problems.append(f"--cover-letter {cover_letter} is not the letter the tracker row records "
                            f"({recorded_cover})")
        return problems

    def prepare(self, url, cv, answers, cover_letter=None):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise SubmissionError("Use the verified HTTPS application URL without embedded credentials")
        if self.path.exists():
            status = self.state()["status"]
            if status == "refused":
                raise SubmissionError("The employer refused this application; it is closed, never resend it")
            if status not in {"ready", "not_submitted"}:
                raise SubmissionError("Prior attempt may have reached employer; resolve it before preparing again")
        _, _, row = self.row()
        if not is_drafted(row):
            raise SubmissionError("Only a drafted application can be prepared")
        problems = self.document_problems(row, cv, cover_letter)
        if problems:
            raise SubmissionError("Documents do not belong to this application: " + "; ".join(problems))
        sources = {"cv.pdf": cv, "answers.json": answers}
        if cover_letter:
            sources["cover_letter.pdf"] = cover_letter
        payloads = {}
        for name, source in sources.items():
            payloads[name] = self.resolve(source).read_bytes()
            if name.endswith(".pdf") and not payloads[name].startswith(b"%PDF-"):
                raise SubmissionError(f"{source} is not a PDF")
        answer_data = json.loads(payloads["answers.json"])
        if not isinstance(answer_data, dict) or not answer_data:
            raise SubmissionError("answers.json must be a nonempty field-to-value object")
        names = upload_names(self.root)
        attempt = uuid4().hex
        target = self.folder / attempt
        target.mkdir(parents=True)
        files = {}
        for name, payload in payloads.items():
            # Keys stay "cv.pdf" etc. so older records read the same; the file on disk
            # carries the simple name the employer sees.
            path = target / names[name]
            path.write_bytes(payload)
            files[name] = {"path": str(path.relative_to(self.root)), "sha256": digest(path),
                           "source": self.relative(sources[name])}
        data = {"version": 1, "company": self.company, "role": self.role, "url": url,
                "attempt": attempt, "status": "ready", "prepared_at": now(), "files": files}
        self.persist(data)
        return data

    def verify(self, data):
        for item in data["files"].values():
            if digest(self.root / item["path"]) != item["sha256"]:
                raise SubmissionError("Snapshot changed; prepare and review the new package before sending")

    def begin(self, authorization):
        data = self.state()
        if data["status"] != "ready":
            raise SubmissionError("Attempt already started or completed; never blindly repeat the submit click")
        if not authorization.strip():
            raise SubmissionError("Record the user's actual scoped submission instruction")
        _, _, row = self.row()
        if not is_drafted(row):
            raise SubmissionError("Tracker is no longer drafted")
        self.verify(data)
        data.update(status="attempting", started_at=now(), authorization=authorization.strip())
        self.persist(data)
        return data

    def finish(self, result, evidence):
        data = self.state()
        if data["status"] not in {"attempting", "uncertain"}:
            raise SubmissionError("No unresolved submission attempt")
        if result not in RESULTS:
            raise SubmissionError("Unknown result")
        source = Path(evidence)
        if not source.is_absolute():
            source = self.root / source
        payload = source.read_bytes()
        if not payload.strip():
            raise SubmissionError("Evidence must describe or show the observed result")
        target = self.folder / data["attempt"] / ("evidence-" + uuid4().hex + source.suffix)
        target.write_bytes(payload)
        timestamp = now()
        data.setdefault("observations", []).append({"result": result, "recorded_at": timestamp,
            "path": str(target.relative_to(self.root)), "sha256": digest(target)})
        data.update(status="submitted" if result == "confirmed" else result)
        if result == "confirmed":
            # Write receipt before CSV so sync can recover from a failed CSV write.
            data["confirmed_at"] = timestamp
            data["submission_date"] = datetime.fromisoformat(data["started_at"]).astimezone().date().isoformat()
        self.persist(data)
        if result == "confirmed":
            self.sync()
        elif result == "refused":
            self.close_refused(data)
        return data

    def write_rows(self, fields, rows):
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        atomic_write(self.tracker, output.getvalue())

    def close_refused(self, data):
        """An employer refusal (duplicate, application limit, closed role) ends the application."""
        fields, rows, row = self.row()
        marker = f"submission:{data['attempt']}"
        if marker in (row.get("notes") or "") or not is_drafted(row):
            return data  # Already recorded, or the row moved on; the ledger keeps the refusal.
        observed = data["observations"][-1]
        day = datetime.fromisoformat(observed["recorded_at"]).astimezone().date().isoformat()
        note = f"{day} {marker} refused by the employer, not sent; evidence {observed['path']}"
        row.update(status="withdrawn")
        row["notes"] = "; ".join(filter(None, [row.get("notes"), note]))
        self.write_rows(fields, rows)
        return data

    def sync(self):
        data = self.state()
        if data["status"] != "submitted":
            raise SubmissionError("Only confirmed submissions can update tracker")
        fields, rows, row = self.row()
        marker = f"submission:{data['attempt']}"
        if marker in (row.get("notes") or ""):
            return data  # Idempotent; never rewind later interview/outcome updates.
        if not is_drafted(row):
            raise SubmissionError("Tracker changed; receipt saved, reconcile row before sync")
        row.update(status="applied", date=data["submission_date"],
                   cv_file=data["files"]["cv.pdf"]["path"],
                   cover_letter_file=data["files"].get("cover_letter.pdf", {}).get("path", ""))
        note = f"{data['submission_date']} {marker} confirmed; receipt {self.path.relative_to(self.root)}"
        row["notes"] = "; ".join(filter(None, [row.get("notes"), note]))
        self.write_rows(fields, rows)
        return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--company", required=True)
    parser.add_argument("--role", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--url", required=True)
    p.add_argument("--cv", required=True)
    p.add_argument("--cover-letter")
    p.add_argument("--answers", required=True)
    p = sub.add_parser("begin")
    p.add_argument("--authorization-file", type=Path, required=True)
    p = sub.add_parser("finish")
    p.add_argument("--result", choices=RESULTS, required=True)
    p.add_argument("--evidence", required=True)
    sub.add_parser("sync")
    sub.add_parser("status")
    args = parser.parse_args()
    ledger = Ledger(args.root, args.company, args.role)
    lock_path = ledger.root / "profile/applications/.submission.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if args.command == "prepare":
                result = ledger.prepare(args.url, args.cv, args.answers, args.cover_letter)
            elif args.command == "begin":
                result = ledger.begin(args.authorization_file.read_text())
            elif args.command == "finish":
                result = ledger.finish(args.result, args.evidence)
            elif args.command == "sync":
                result = ledger.sync()
            else:
                result = ledger.state()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Submission ledger: {exc}\n")


if __name__ == "__main__":
    main()
