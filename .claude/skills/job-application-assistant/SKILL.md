---
name: job-application-assistant
description: >
  Assists with job applications: evaluating job postings, tailoring CVs, writing cover letters,
  and preparing for interviews. Triggers on keywords like: job posting, job application, CV,
  cover letter, resume, interview prep, job fit, career, application, apply, ansøgning, stilling
allowed-tools: Read, Glob, Grep, WebFetch, WebSearch, Bash, Edit, Write, AskUserQuestion
framework_version: 1.3.5
---

# Job Application Assistant

---

## Workflow

**First, read `profile/` (profile.md, deal-breakers.md, behavioral.md). If it is missing, run `/onboard` before anything else.**

When the user provides a job posting (URL or text), follow this workflow:

### Step 1: Research & Evaluate Fit
- Fetch the job posting content (use WebFetch for URLs). **A 403 is not a dead end** - follow the escalation order in `09-web-research.md` before concluding a page is unavailable, and prefer the employer's own careers posting over an aggregator listing
- Keep the **full posting text verbatim** for Step 3b to archive - never a summary
- Analyze the posting for required competencies, keywords, and priorities
- Research the company (website, LinkedIn, mission, recent news), per `09-web-research.md`
- Score the posting against the candidate's profile using the framework in `04-job-evaluation.md`
- Present the evaluation table and verdict
- Suggest whether the candidate should call the employer before applying (see `04-job-evaluation.md` for guidance)
- Apply `/apply` Step 1's stop rule before drafting: ask first when the verdict is below Good Fit, the location check fails, the source host is unverified, or an eligibility or language gate fails. Otherwise continue if the user already asked for this application or a scoped shortlist; ask only when the request was evaluation-only

### Step 2: Tailor CV
- Before writing either document, derive `<company>_<role>` once by the **Subfolder naming** rule in `documents/README.md`; reuse that exact value for the CV, cover letter, and Step 3b archive path. If the rule says to stop because the derived name is empty, stop before creating any file.
- Read the most relevant existing CV variant from `cv/` as a starting point
- Follow the guidelines in `05-cv-templates.md`
- Resolve the ACTIVE-TEMPLATE block in `05-cv-templates.md`; create `cv/main_<company>_<role>.py` using the active template and closest role preset
- Ground facts in `profile/profile.md` and `profile/cv_content.py`; use the current resume source recorded in the profile when reconciling facts, never the placeholder example
- Rewrite positioning, bullets and project selection substantially for the posting; preserve factual titles, dates, ownership and metrics
- Adjust: profile statement, skills section, experience bullet emphasis, section order

### Step 3: Write Cover Letter
- Follow the writing style rules in `03-writing-style.md` (critical: no em-dashes, no cliches)
- Follow the template structure in `06-cover-letter-templates.md`
- Resolve the ACTIVE-TEMPLATE block in `06-cover-letter-templates.md`; create `cover_letters/cover_<company>_<role>.py`
- Compile and inspect both documents using `/apply` Steps 5-6 before handing them off
- Ensure the letter connects specific experience to the role requirements

### Step 3b: Record the Application
- Run this once both documents exist. A CV or cover letter drafted alone is not yet an application.
- Follow **`/apply` Step 6b** (`.claude/commands/apply.md`) exactly: same header, same match-then-update rule, same `drafted` row, same posting archive, same prohibition on touching `job_scraper/seen_jobs.json`. It is stated there once so the two paths cannot drift. Four of its values are named in `/apply`'s own terms: `cv_file`/`cover_letter_file` are the paths written in Steps 2 and 3 here, `source` is the posting URL from Step 1, `deadline` is the application deadline from the posting text Step 1 keeps verbatim (empty when the posting states none - never guess one), and the posting text item 7 archives is the one Step 1 read.
- This step exists here because `/scrape` Step 5 routes straight into this skill. Without it, that path writes two documents and records nothing.

### Step 3c: Browser submission when requested
- Follow `.claude/commands/submit.md` for form filling, authorization, exact-file snapshots, sending and receipt tracking.
- A request to build or configure automation is not authorization to send real applications. A request to submit a named role or explicit shortlist is; do not ask for that permission again within its scope.

### Step 4: Interview Preparation
- Follow the framework in `07-interview-prep.md`
- Prepare STAR-format answers for likely questions
- Identify role-specific talking points
- Draft questions the candidate should ask the interviewer

---

## Reference Files

| File | Purpose |
|------|---------|
| `01-candidate-profile.md` | Pointer to the private `profile/` folder (profile.md, behavioral.md, deal-breakers.md, forms.md); templates in `profile.example/` |
| `02-behavioral-profile.md` | Pointer to `profile/behavioral.md` and how it is used |
| `03-writing-style.md` | Tone, structure, do's and don'ts |
| `04-job-evaluation.md` | Scoring framework for job fit |
| `05-cv-templates.md` | Active CV template, factual baseline and tailoring rules |
| `06-cover-letter-templates.md` | Active cover-letter template and writing structure |
| `07-interview-prep.md` | STAR examples, tough questions, roleplay guidelines |
| `08-application-forms.md` | Portal free-text fields: self-introduction, project entries, character-limited pitches; the answer bank itself is `profile/forms.md` |
| `09-web-research.md` | Fetching postings and company pages: trust boundary, the WebFetch 403 fallback, escalation order, claim verification |
| `10-email-replies.md` | Replying to recruiter and employer emails as threaded Gmail drafts: thread history kept untouched at the bottom, Cc kept, content rules for visa, invoicing and pay |

---

## Quick Commands

The user may also ask for individual steps without the full workflow:
- "Evaluate this job posting" - Step 1 only
- "Write a CV for [company]" - Step 2 only
- "Write a cover letter for [role] at [company]" - Step 3 only
- "Help me prepare for an interview at [company]" - Step 4 only
- "What jobs should I look for?" - Career strategy discussion using profile + evaluation framework
