#!/usr/bin/env python3
"""Build a safe, reviewable browser-submission queue from the tracker.

This tool never opens a browser or submits an application. It removes work that
cannot be executed cleanly (bad URLs, missing or wrong documents, duplicate rows,
non-drafted statuses, on-site or relocation roles) before a batch reaches the live
form runner, and orders what is left by fit band, remote before hybrid.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

try:
    from tools.document_checks import cover_letter_problems, cv_problems, pdf_path
except ImportError:  # run as a script: tools/ itself is on sys.path
    from document_checks import cover_letter_problems, cv_problems, pdf_path


KNOWN_ATS = ("greenhouse.io", "lever.co", "ashbyhq.com", "myworkdayjobs.com",
             "workday.com", "smartrecruiters.com", "workable.com", "careers-page.com")
FINAL_STATUSES = {"applied", "submitted", "rejected", "withdrawn", "skipped",
                  "expired", "offer", "offer_declined", "hired", "no_response"}
# 04-job-evaluation.md verdict bands. Below Good Fit the framework says to discuss first.
BANDS = ((75, "Strong Fit"), (60, "Good Fit"), (45, "Moderate Fit"), (30, "Weak Fit"), (0, "Poor Fit"))
GOOD_FIT = 60
# Within a band remote goes first; on-site and relocation rows are blocked outright.
WORK_MODE_ORDER = {"remote": 0, "unknown": 1, "hybrid": 2}

NEGATORS = frozenset({"no", "not", "non", "without", "never"})
EXPLICIT_MODE = re.compile(r"work[\s-]*mode:\s*(remote|hybrid|on[\s-]?site)", re.IGNORECASE)
RELOCATION = re.compile(
    r"\b(?:must|required to|need to|needs to|have to|has to) relocate\b"
    r"|\b(?:requires?|required|mandatory) relocation\b"
    r"|\brelocation (?:is )?(?:required|mandatory|necessary|expected)\b", re.IGNORECASE)
HYBRID = re.compile(r"\bhybrid\b", re.IGNORECASE)
ONSITE = re.compile(r"\bon[\s-]?site\b|\bin[\s-]office\b|\boffice[\s-]based\b", re.IGNORECASE)
REMOTE = re.compile(r"\bremote\b", re.IGNORECASE)


def _affirmed(pattern: re.Pattern, text: str) -> bool:
    """True when the text mentions the pattern without negating it in the same clause."""
    for match in pattern.finditer(text):
        clause = re.split(r"[;,.:()\n]", text[:match.start()])[-1]
        if not NEGATORS.intersection(re.findall(r"[a-z]+", clause.casefold())[-3:]):
            return True
    return False


def work_mode(notes: str, role_type: str = "") -> str:
    """remote | hybrid | onsite | relocation | unknown, from the row's own words.

    An explicit `Work mode: ...` note (written by /apply Step 6b) wins over inference.
    """
    text = "\n".join(filter(None, (notes, role_type)))
    explicit = EXPLICIT_MODE.findall(text)
    if explicit:
        return re.sub(r"[\s-]", "", explicit[-1].casefold())
    if _affirmed(RELOCATION, text):
        return "relocation"
    if _affirmed(HYBRID, text):
        return "hybrid"
    onsite, remote = _affirmed(ONSITE, text), _affirmed(REMOTE, text)
    if onsite and not remote:
        return "onsite"
    return "remote" if remote and not onsite else "unknown"


def _fit(value: str) -> int | None:
    return int(value) if value.strip().isdigit() else None


def _band(fit: int | None) -> int:
    """Index into BANDS, best first; an unscored row sorts after every band."""
    if fit is None:
        return len(BANDS)
    return next(i for i, (floor, _) in enumerate(BANDS) if fit >= floor)


def _path(root: Path, value: str) -> Path:
    path = Path(value.strip())
    return path if path.is_absolute() else root / path


def _valid_pdf(root: Path, value: str) -> bool:
    path = _path(root, value)
    return path.is_file() and path.read_bytes()[:5] == b"%PDF-"


def _host_class(source: str) -> str:
    parsed = urlsplit(source.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return "invalid"
    host = parsed.hostname.lower().rstrip(".")
    return "known_ats" if any(host == apex or host.endswith("." + apex) for apex in KNOWN_ATS) else "manual_review"


def build_queue(root: Path, tracker: Path, limit: int | None = None) -> dict:
    required = {"company", "role", "status", "source", "cv_file", "cover_letter_file"}
    with tracker.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("tracker is missing one of: " + ", ".join(sorted(required)))
        rows = list(reader)

    counts: dict[str, int] = {}
    keys = [((row.get("company") or "").strip().casefold(),
             (row.get("role") or "").strip().casefold()) for row in rows]
    seen: dict[tuple[str, str], int] = {}
    for key in keys:
        seen[key] = seen.get(key, 0) + 1
    candidates = []
    for row_number, row in enumerate(rows, start=2):
        status = (row.get("status") or "").strip().lower()
        counts[status or "<blank>"] = counts.get(status or "<blank>", 0) + 1
        key = ((row.get("company") or "").strip().casefold(), (row.get("role") or "").strip().casefold())
        if status in FINAL_STATUSES:
            continue
        company = (row.get("company") or "").strip()
        reasons: list[str] = []
        warnings: list[str] = []
        source = (row.get("source") or "").strip()
        host_class = _host_class(source)
        if status != "drafted":
            reasons.append(f"status is {status or 'blank'}, expected drafted")
        if not company or not (row.get("role") or "").strip():
            reasons.append("company and role are required")
        if seen[key] > 1:
            reasons.append("duplicate company/role in tracker")
        if host_class == "invalid":
            reasons.append("source must be a verified HTTPS URL without credentials")

        cv_file = (row.get("cv_file") or "").strip()
        cover_file = (row.get("cover_letter_file") or "").strip()
        cv_pdf, cover_pdf = pdf_path(cv_file), pdf_path(cover_file)
        reasons += cv_problems(cv_file, company)
        if cv_pdf and not _valid_pdf(root, cv_pdf):
            reasons.append(f"CV PDF {cv_pdf} is missing or has no PDF header")
        reasons += cover_letter_problems(cover_file, company)
        if cover_pdf and not _valid_pdf(root, cover_pdf):
            reasons.append(f"cover-letter PDF {cover_pdf} is missing or has no PDF header")

        mode = work_mode(row.get("notes") or "", row.get("role_type") or "")
        if mode in ("onsite", "relocation"):
            reasons.append(f"work mode reads as {mode}: fully on-site and relocation roles are never sent. "
                           "If the notes are wrong, record 'Work mode: remote' or 'Work mode: hybrid' in them")
        elif mode == "hybrid":
            warnings.append("hybrid: confirm the office days don't force a move before sending")
        elif mode == "unknown":
            warnings.append("work mode not recorded; add 'Work mode: remote|hybrid|on-site' to notes")

        fit = _fit(row.get("fit_rating") or "")
        if fit is None:
            warnings.append("fit not scored numerically")
        elif fit < GOOD_FIT:
            warnings.append(f"fit {fit} ({BANDS[_band(fit)][1]}) is below Good Fit; send only if the user chose to")

        candidates.append({
            "row": row_number,
            "company": company,
            "role": (row.get("role") or "").strip(),
            "source": source,
            "status": status,
            "cv_file": cv_file,
            "cv_pdf": cv_pdf,
            "cover_letter_file": cover_file,
            "cover_letter_pdf": cover_pdf,
            "fit_rating": (row.get("fit_rating") or "").strip(),
            "work_mode": mode,
            "host_class": host_class,
            "manual_effort": "lower" if host_class == "known_ats" else "higher",
            "ready": not reasons,
            "reasons": reasons,
            "warnings": warnings,
        })

    # Ready first, then fit band, then remote before hybrid within the band, then best fit.
    candidates.sort(key=lambda item: (not item["ready"], _band(_fit(item["fit_rating"])),
                                      WORK_MODE_ORDER.get(item["work_mode"], len(WORK_MODE_ORDER)),
                                      -(_fit(item["fit_rating"]) or 0),
                                      item["manual_effort"] != "lower", item["row"]))
    if limit is not None:
        candidates = candidates[:limit]
    ready = [item for item in candidates if item["ready"]]
    blocked = [item for item in candidates if not item["ready"]]
    return {"generated_on": date.today().isoformat(), "tracker": str(tracker),
            "counts": counts, "total_considered": len(candidates),
            "ready_count": len(ready), "blocked_count": len(blocked),
            "applications": candidates}


def write_outputs(queue: dict, json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [f"# Browser submission preflight - {queue['generated_on']}", "",
             f"Ready: **{queue['ready_count']}** · blocked: **{queue['blocked_count']}**", "",
             "The queue is preparation only. It never submits or opens a browser.", ""]
    for item in queue["applications"]:
        marker = "READY" if item["ready"] else "BLOCKED"
        lines.append(f"- **{marker}** {item['company']} - {item['role']} (fit {item['fit_rating'] or '?'}; "
                     f"{item['work_mode']}; {item['manual_effort']} manual effort; {item['host_class']})")
        if item["reasons"]:
            lines.append("  - " + "; ".join(item["reasons"]))
        if item.get("warnings"):
            lines.append("  - ⚠ " + "; ".join(item["warnings"]))
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--tracker", type=Path, default=None)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--markdown", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    tracker = (args.tracker or root / "profile/tracker.csv").resolve()
    queue = build_queue(root, tracker, args.limit)
    json_path = (args.json or root / "profile/applications/batch_preflight.json").resolve()
    markdown_path = (args.markdown or root / "profile/applications/batch_preflight.md").resolve()
    write_outputs(queue, json_path, markdown_path)
    print(json.dumps({"ready": queue["ready_count"], "blocked": queue["blocked_count"],
                      "json": str(json_path), "markdown": str(markdown_path)}, indent=2))


if __name__ == "__main__":
    main()
