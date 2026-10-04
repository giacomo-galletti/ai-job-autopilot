"""CV content entry point: every renderer and per-application module imports from here.

The data comes from `profile/cv_content.py` (your own content, in the gitignored private
folder) when that file exists, otherwise from `content_example.py` (a fictional candidate, so
the template renders out of the box). Set JOB_KIT_EXAMPLE_CONTENT=1 to force the example
content even when your profile exists; the tests do this.

The designed CV joins each job's sentences into a paragraph; the ATS resume shows them as
bullets. A per-application module (cv/main_<company>_<role>.py) imports * from this file and
overrides only what the role needs - see template.py for the skeleton.
"""

import importlib.util
import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
PROFILE_CONTENT = _HERE.parents[2] / "profile" / "cv_content.py"
USING_EXAMPLE = bool(os.environ.get("JOB_KIT_EXAMPLE_CONTENT")) or not PROFILE_CONTENT.is_file()


def _load_data():
    path = _HERE / "content_example.py" if USING_EXAMPLE else PROFILE_CONTENT
    spec = importlib.util.spec_from_file_location("_cv_content_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {k: v for k, v in vars(module).items() if not k.startswith("_")}


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
globals().update(_load_data())
# Optional sections: absent from a profile means empty, and an empty section is not drawn.
for _name, _default in (("PROJECTS", []), ("REFERENCES", []), ("REFERENCES_NOTE", ""), ("CERTIFICATIONS", [])):
    globals().setdefault(_name, _default)


# ── rendering helpers shared by the builders ─────────────────────────────────────
def _ym(value):
    """Normalise a date to (year, month or None). Accepts None, 2014, (2014,), (2014, None), (2014, 7)."""
    if value is None or value == () or value == "":
        return None
    if isinstance(value, int):
        return (value, None)
    year = value[0]
    month = value[1] if len(value) > 1 else None
    return (year, month or None)


def _range(start, end, fmt):
    """'<start> - <end>' with Present for an open end; one side or none when a date is unknown."""
    s, e = _ym(start), _ym(end)
    if not s:
        return fmt(e) if e else ""
    return f"{fmt(s)} - {fmt(e) if e else 'Present'}"


def ats_dates(start=None, end=None):
    return _range(start, end, lambda ym: f"{ym[1]:02d}/{ym[0]}" if ym[1] else str(ym[0]))


def figma_dates(start=None, end=None):
    return _range(start, end, lambda ym: f"{MONTHS[ym[1] - 1]} {ym[0]}" if ym[1] else str(ym[0]))


def ats_location(entry):
    if entry.get("location") and entry.get("remote"):
        return f"{entry['location']} (Remote)"
    return entry.get("location") or ("Remote" if entry.get("remote") else "")


def figma_location(entry):
    parts = [p for p in (entry.get("location"), "Remote" if entry.get("remote") else None) if p]
    return " · ".join(parts)


def ats_sentences(job):
    """The shared sentences, with any ATS-only ones placed before the last shared sentence."""
    extra = job.get("ats_extra", [])
    if not extra:
        return job["sentences"]
    return job["sentences"][:-1] + extra + job["sentences"][-1:]


def certification_line(cert):
    """'Name - Issuer, 2022' with issuer and year left out when not given."""
    line = cert["name"]
    if cert.get("issuer"):
        line += f" - {cert['issuer']}"
    if cert.get("year"):
        line += f", {cert['year']}"
    return line


def skill_items(items):
    return ", ".join(items)
