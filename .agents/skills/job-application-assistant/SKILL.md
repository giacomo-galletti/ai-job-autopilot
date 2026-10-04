---
name: job-application-assistant
description: >
  Thin Codex pointer to the canonical job-application-assistant skill in .claude/skills/. Evaluates job postings, tailors CVs, writes cover letters, prepares interviews. Triggers on: job posting, job application, CV, cover letter, resume, interview prep, job fit, apply.
---

# Job Application Assistant (pointer)

The single source of truth is `.claude/skills/job-application-assistant/`. Do not keep a copy here.

1. Read the candidate's private data in `profile/` first (`profile.md`, `deal-breakers.md`, and
   when relevant `behavioral.md`, `forms.md`). If `profile/` is missing, run `/onboard`
   (`.claude/commands/onboard.md`).
2. Read `.claude/skills/job-application-assistant/SKILL.md` and follow its workflow. The method
   files `03-writing-style.md` to `10-email-replies.md` sit next to it.
3. Where a file names a Claude-only tool, use the closest available Codex tool and state any
   verification gap.
