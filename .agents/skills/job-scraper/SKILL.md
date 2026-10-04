---
name: scrape
description: >
  Thin Codex pointer to the canonical /scrape skill in .claude/skills/job-scraper/. Finds new job postings matching the candidate profile via the installed portal-search CLIs. Triggers on: job scrape, find jobs, search jobs, new jobs, /scrape
---

# Job Scraper (pointer)

The single source of truth is `.claude/skills/job-scraper/SKILL.md` (workflow) and
`.claude/skills/job-scraper/search-queries.md` (method). The candidate's enabled portals and queries
are in `profile/portals.md` and `profile/search-queries.md`; if `profile/` is missing run
`/onboard`. The portal CLIs themselves are the sibling skills in `.agents/skills/*-search/`.
