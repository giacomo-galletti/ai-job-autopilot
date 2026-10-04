# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project is derived from [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search)
(MIT). The history of that project is not carried over.

## [Unreleased]

### Added

- CV template: optional `CERTIFICATIONS`; job/school dates and `company` are optional and year-only dates
  are accepted; empty Projects/References sections draw no heading; language rows no longer show
  flags. `.env.example` is now tracked.
- **`/onboard`** - runtime-neutral onboarding (Claude Code and Codex) that builds the private
  `profile/` folder, selects job boards for the user's role, seniority, country and languages,
  configures the CV/letter theme with a test render, and ends with a dry-run evaluation.
- **Portal selection** - ranked board proposal (global, country, niche), verified with
  `tools/robots_check.py`, stored in `profile/portals.md`; `/scrape` reads it.
- `requirements.txt`.

### Changed

- Personal data moved out of tracked files into the gitignored `profile/` folder.
- `/reset` wipes `profile/` (and optionally `documents/`) after explicit confirmation.
- `/add-portal` registers new boards in `profile/portals.md`.
- `/setup` is now an alias for `/onboard`.
