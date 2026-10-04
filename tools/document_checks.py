#!/usr/bin/env python3
"""Checks that an application's documents were made for that application.

Shared by tools/batch_preflight.py (the submission queue) and tools/submission.py
(`prepare`), so a single-role /submit gets the same protection as a batch.

A tailored document names its employer at the start of its filename -
`cv/main_<company>_<role>.pdf`, `cover_letters/cover_<company>_<role>.pdf` - or sits in
that application's own archive, `profile/applications/<company>_<role>/submission/...`.
The company must match from the first word of that name, never as a substring anywhere in
the path: an unanchored match is how the FlexMade CV passed for "Frontend Masters".
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

# Trailing words that name a legal form rather than the company ("ADI Group" -> "adi").
LEGAL_SUFFIXES = frozenset({
    "ab", "ag", "aps", "as", "bv", "co", "company", "corp", "corporation", "gmbh", "group",
    "holding", "holdings", "inc", "limited", "llc", "ltd", "nv", "oy", "ou", "o\u00fc", "plc",
    "sa", "sarl", "sas", "sl", "spa", "srl",
})


def words(value: str) -> list[str]:
    return re.findall(r"[^\W_]+", value.casefold())


def _path(value: str) -> PurePosixPath:
    return PurePosixPath(value.strip().replace("\\", "/"))


def company_keys(company: str) -> set[str]:
    parts = words(company)
    keys = {"".join(parts)}
    while len(parts) > 1 and parts[-1] in LEGAL_SUFFIXES:
        parts = parts[:-1]
        keys.add("".join(parts))
    return {key for key in keys if key}


def pdf_path(value: str) -> str:
    """The compiled PDF for a recorded document; /apply records the .py source module."""
    if not value.strip():
        return ""
    path = _path(value)
    return str(path if path.suffix.casefold() == ".pdf" else path.with_suffix(".pdf"))


def _owner_words(value: str) -> list[str] | None:
    """Words naming the application a document was made for, or None if its name doesn't say."""
    path = _path(value)
    parts = [part.casefold() for part in path.parts]
    for i in range(len(parts) - 3):
        if parts[i:i + 2] == ["profile", "applications"] and parts[i + 3] == "submission":
            return words(path.parts[i + 2])
    stem = words(path.stem)
    if len(stem) > 1 and stem[0] in ("main", "cover"):
        return stem[1:]
    return None


def names_company(value: str, company: str) -> bool:
    owner, keys = _owner_words(value), company_keys(company)
    prefix = ""
    for word in owner or []:
        prefix += word
        if prefix in keys:
            return True
    return False


def _untailored(value: str) -> str | None:
    path = _path(value)
    parts = [part.casefold() for part in path.parts]
    if any(parts[i:i + 2] == ["documents", "cv"] for i in range(len(parts) - 1)):
        return f"{value} is a master CV from documents/cv/, not tailored for this role"
    stem = words(path.stem)
    if stem[-1:] == ["designed"]:
        return f"{value} is the two-column designed CV; portals get the ATS resume"
    if stem[:2] == ["main", "master"]:
        return f"{value} is the untailored master CV"
    return None


def cv_problems(value: str, company: str) -> list[str]:
    if not value.strip():
        return ["no tailored CV recorded for this role; run /apply first"]
    untailored = _untailored(value)
    if untailored:
        return [untailored]
    if not names_company(value, company):
        return [f"{value} is not named for {company}; upload the CV tailored for this role"]
    return []


def cover_letter_problems(value: str, company: str) -> list[str]:
    if value.strip() and not names_company(value, company):
        return [f"{value} is not named for {company}; it was written for another application"]
    return []
