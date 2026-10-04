"""Helpers every preset uses. Not a preset itself.

The two things presets do to the master content are reorder skill groups and reorder the
sentences inside a job. Both are here so a preset file is just its positioning decisions.
"""

import sys

from content_base import JOBS as _BASE_JOBS
from content_base import SKILLS as _BASE_SKILLS


def skills(*group_names):
    """The named skill groups, in the order given. Unnamed groups are dropped.

    Order is the sidebar order in the designed CV. Dropping a group is a positioning
    decision, not a claim about what the candidate can do - the ATS lists carry the keywords.
    """
    by_name = {name: group for name, group in _BASE_SKILLS}
    missing = [n for n in group_names if n not in by_name]
    if missing:
        raise KeyError(f"no such skill group(s): {missing}. Have: {list(by_name)}")
    return [(name, by_name[name]) for name in group_names]


def reorder(by_company=None, **sentences_by_company):
    """Jobs with some companies' sentences reordered, and some rephrased.

    Pass a list per company. Each item is either:

      **an int** - the index of a sentence in content_base.py's list for that job. Use this
      whenever the preset only changes *order*: the sentence then stays in sync with the
      master, so editing content_base once updates every preset that points at it.

      **a string** - a rephrasing, for when the preset needs different emphasis. A string is a
      copy and will NOT track later edits to the master, so use one only where the wording
      genuinely has to differ, and keep it a rephrasing of an existing sentence. Whether it
      still says something true is not checkable here; the /apply Factual Grounding Audit is
      what enforces that.

        reorder(Freelance=[3, 0, 1, 2])                          # pure reorder, stays in sync
        reorder(Freelance=[0, 1, "Build the front end myself"])  # one sentence rephrased
        reorder({"Example Co": [2, 0]})                        # company names with spaces: pass a dict

    Jobs you don't name keep their current version: the calling module's JOBS if it has
    one. In a per-application module that imported a preset, that is the preset's JOBS, so
    overriding one job never puts the master wording back on the others. In a preset, which
    has no JOBS of its own yet, that is content_base.py's.
    """
    sentences_by_company = {**(by_company or {}), **sentences_by_company}
    known = {job["company"]: job for job in _BASE_JOBS}
    unknown = set(sentences_by_company) - set(known)
    if unknown:
        raise KeyError(f"no such job(s): {sorted(unknown)}. Have: {sorted(known)}")

    current = sys._getframe(1).f_globals.get("JOBS", _BASE_JOBS)
    out = []
    for job in current:
        job = dict(job)
        chosen = sentences_by_company.get(job["company"])
        if chosen is not None:
            base = known[job["company"]]["sentences"]
            resolved = []
            for item in chosen:
                if isinstance(item, int):
                    if not -len(base) <= item < len(base):
                        raise IndexError(
                            f"{job['company']}: sentence index {item} is out of range "
                            f"(the job has {len(base)})"
                        )
                    resolved.append(base[item])
                else:
                    resolved.append(item)
            job["sentences"] = resolved
        out.append(job)
    return out
