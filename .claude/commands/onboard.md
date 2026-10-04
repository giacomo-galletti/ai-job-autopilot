# /onboard - Profile, Portals and Template Onboarding

You are onboarding a new user. Your goal: build their private `profile/` folder so every other
workflow (`/scrape`, `/rank`, `/apply`, `/submit`, `/interview`) works for them out of the box.

This file is plain instructions. It runs unchanged in Claude Code (`/onboard`) and Codex
("run the onboarding in .claude/commands/onboard.md"). Use whatever file-read, file-write,
shell and web-search tools your runtime provides; where a step says "web search" and none is
available, ask the user to paste links instead of guessing.

**Privacy rule.** Everything personal goes in `profile/`, which is gitignored. Never write
personal data into a tracked file. Never commit `profile/`. Before writing anything, run
`git check-ignore profile/` and stop if it does not print `profile/`. If the folder is not a git
repository (for example an unpacked zip), run `git init` first (Step 1 item 3) so the check works;
if the user refuses git, write nothing personal.

`$ARGUMENTS` may be empty, or `--section <name>` where name is one of:
`identity`, `experience`, `behavioral`, `deal-breakers`, `portals`, `search`, `template`,
`theme`, `gmail`, `forms`. In that case skip to the matching step below, change only that part
of `profile/`, and stop. Do not re-run the whole flow.

Files in `profile/` (templates for each live in `profile.example/`):

| File | Holds |
|---|---|
| `profile.md` | identity, education, experience, skills, languages, target roles |
| `behavioral.md` | how the user works, strengths, growth areas, what energises or drains them |
| `deal-breakers.md` | hard no's, location rules, standing apply rules and exceptions |
| `forms.md` | reusable answers to application-form questions |
| `portals.md` | the chosen job boards (written in Step 4) |
| `search-queries.md` | role titles, synonyms, exclusions, location filters |
| `cv_content.py` | CV content module read by the CV template |
| `theme.json` | name, accent colours, font for the CV and cover letter |

---

## Step 1: Preflight

Run these checks and report a short table (ok / missing / optional). Offer to fix what is missing.

1. `python3 --version` (3.10+ required).
2. Python packages: `python3 -m pip install -r requirements.txt` (ask first; suggest a venv).
   The CV/cover-letter build also needs Playwright's Chromium: `python3 -m playwright install chromium`.
3. `git check-ignore profile/` must print `profile/`. If this is not a git repo, run `git init` first,
   then check. If the user declines git, stop before writing anything personal (the Privacy rule
   applies; without git nothing here is protected from a later `git add`).
4. Optional, `bun --version`: needed only by the bundled job-board CLIs in `.agents/skills/`.
   Without bun, `/scrape` falls back to web search. Point to https://bun.sh.
5. Optional, Gmail: only asked about in Step 7. Do not check now.
6. If `profile/` already has files, say so and ask: keep and update (default), or run `/reset` first.

Create `profile/` by copying `profile.example/` (do not overwrite existing files; skip its
`README.md`). Also copy `templates/cv/designed/content_example.py` to `profile/cv_content.py` and
`templates/cv/designed/theme.json` to `profile/theme.json`, unless they already exist. Step 3 and
Step 5 then overwrite their sample values with the user's.

---

## Step 2: Intake

Look at what the user has. Offer three paths and wait for a choice.

- **Path A: existing documents.** Files in `documents/` (CV, LinkedIn export, diplomas, references,
  project notes, past applications). Read everything, cross-reference, build the profile from it.
- **Path B: single CV import.** The user pastes or points to one CV/resume. Extract, then ask follow-ups.
- **Path C: interview.** Ask conversationally, one topic at a time; the user answers in their own words.

### Path A procedure
1. List `documents/**` and read each file (cv, linkedin, diplomas, references, projects, applications).
2. Cross-check dates, titles, employers and degrees across documents. Present each mismatch and let
   the user say which is right before continuing.
3. If a section of `profile/` already has content, show additions and conflicts separately; apply
   additions after one confirmation, conflicts one at a time (keep / replace / edit myself).
4. Label anything inferred (behavioral traits, writing style) as inferred so the user can review it.

### Path B procedure
Read the CV, extract identity, contact, education, experience, skills, languages, awards, then ask
for the gaps listed under Path C.

### Path C topics
1. **Identity:** full name, city and country, email, phone, LinkedIn/GitHub/portfolio, work
   languages with rough level, current status, work authorisation, time zone.
2. **Education and certifications** (name, issuer, year; issuer and year optional). If the user does
   not know a detail or has none (no degree, no dates), record what they give and mark the unknowns
   explicitly in `profile.md`. Never invent values; leave the field out of `cv_content.py` rather
   than filling it (an education entry may omit `school`, and the degree then becomes its title).
3. **Experience** (newest first): title, company, dates, location, 3-5 bullets, achievements, tools.
   Also freelance, side projects. Same rule: if there is no employer or no dates, record what they
   give, mark unknowns explicitly in `profile.md`, and leave the field out of `cv_content.py`.
   **Ask the unknown-date policy once, up front:** an unknown month becomes year only (`(2019,)`),
   an unknown start is left out, and an unknown or private employer is shown as a descriptor
   ("Confidential fintech client") or the `company` key is omitted. Never guess a month or a name.
4. **Skills:** primary, secondary, domain, software.
5. **Behavioral profile** (optional): assessment results, or ask what environments they thrive in,
   what drains them, how they decide, how they work in teams.
6. **Career goals:** target roles and sectors, what excites them, seniority, salary baseline
   (optional), engagement type (employee, contractor, both).
7. **Location and work mode:** home city, remote / hybrid / on-site preference, commute radius,
   relocation yes/no, countries they can legally work in, time-zone limits.
8. **References** (optional).

Proactively suggest adjacent role titles the user may not have considered, based on their skills.

---

## Step 3: Write the profile

Fill, from the intake, these files in `profile/` (replace every `[PLACEHOLDER]`; leave no token behind):

- `profile.md`, `behavioral.md`, `forms.md` (seed in Step 8), `deal-breakers.md` (Step 6),
  `cv_content.py` (the Step 1 copy of `content_example.py`, with its sample values replaced by the
  user's name, contact, headline, summary, experience, education, certifications, skills, languages;
  keep its names and structure). Certifications go in the optional `CERTIFICATIONS` list
  (`name`, optional `issuer` and `year`); with none, leave it `[]` and no heading is drawn. Accepted
  date forms and optional keys are documented at the top of `content_example.py`; set unknown
  values to the supported "absent" forms rather than placeholders. `theme.json` is filled in Step 5.

Facts must come from the user's documents or answers. Never invent employers, dates, numbers or
skills. Show the user a short summary of what was written and let them correct it before moving on.

---

## Step 4: Portal selection

This is the step that tailors the search to the person. Derive the inputs from Step 3:

- **role family** (software, data, design, healthcare, sales, finance, trades, ...)
- **skills and seniority**
- **home country / region** and which countries they could work in
- **remote vs hybrid vs on-site** preference
- **languages** they can work in (a board in a language they do not speak is useless)

Build a ranked proposal in three tiers, then let the user edit it.

### 4a. Global tier
- **LinkedIn** (`linkedin-search`): good for nearly everyone. Always include; warn about its ToS (see below).
  Its robots.txt disallows automated paths, which looks like it conflicts with "always include". The
  resolution: it is included for personal use only, in the user's own logged-in session, at low
  volume, and the user is told plainly that automated access may breach LinkedIn's Terms of Service
  and put the account at risk. Offer "Manual only" if they would rather not take that risk.
- **Remote-first roles** (`himalayas-search`, every posting remote): include only when the user wants
  remote or worldwide work AND their role family appears in its feed (check the role families listed
  in `.agents/skills/himalayas-search/SKILL.md`). For non-tech roles outside that list, disable it.
  For a career crossover, judge by the TARGET role family, not the current one.
- **freehire** (`freehire-search`, tech aggregator across ~50 applicant-tracking systems): include for software,
  data, DevOps and other technical roles only.

### 4b. Country tier (bundled CLIs)
Read the `SKILL.md` of each bundled CLI in `.agents/skills/` before proposing it. Use it only if its
documented coverage matches the user's country and language.

| Bundled CLI | Coverage | Propose when |
|---|---|---|
| `linkedin-search` | any country, remote | always |
| `himalayas-search` | remote jobs worldwide | user wants remote AND the target role family is in its feed (see its SKILL.md); otherwise disable |
| `freehire-search` | tech roles, many countries | technical role family |
| `adzuna-search` | ~11 markets (US, UK, DE, NL, CA, FR, IT, AT, ES, AU, NZ and others; see its SKILL.md) and salary data | user lives in or targets a covered country; needs free API keys in `.env` (see `.env.example`) |
| `jobindex-search`, `jobnet-search`, `jobdanmark-search`, `jobbank-search` (Danish academic roles; **not** Job Bank Canada) | Denmark only, Danish-language postings | only if the user targets Denmark and reads Danish. Not default. |

**Name collision:** the bundled `jobbank-search` is Akademikernes Jobbank (jobbank.dk, Denmark). It has
nothing to do with Job Bank Canada (jobbank.gc.ca); never propose it for a Canadian search.

Canada has no bundled national board CLI in the default set; if the user targets Canada, check
`.agents/skills/` for a Canada board skill and its SKILL.md. If none is present, use `adzuna-search`
(covers Canada) and treat Job Bank (Canada) as a niche-tier candidate for `/add-portal`.

### 4c. Role-specific niche boards (research at onboarding time)
Use web search to find well-known boards for this role family in this country, for example:
`best job boards for <role family> in <country>`, `<role> jobs <country> job board`, plus the
language of the market. Pick 3 to 6 candidates that are reputable, still active and in a language
the user works in. For each candidate, verify:

1. The site exists and shows live postings (fetch the homepage or a search results page).
2. **Automated access is allowed: robots plus Terms of Service.** Both must pass.
   - Robots: run `python3 tools/robots_check.py <search-page-url>`. Exit 0 prints `ALLOWED`; exit 1
     prints `DISALLOWED` (the site said no) or `UNCONFIRMED`. UNCONFIRMED (a 403, a timeout or an
     undecodable response) is a tool error, not a site policy: try once more, then treat the board
     as Manual. It is not permission and it is not a refusal.
   - Terms of Service: open the board's terms and look for clauses on scraping, bots, crawling or
     automated access. **A robots ALLOWED does not mean permitted**: robots.txt only covers crawlers,
     the terms are a separate contract. Checklist: (a) terms found and read, (b) no clause forbids
     automated access, (c) no login or account is needed to search, (d) the board is not one of the
     known-forbidden ones. Indeed, Glassdoor and Wellfound, and any login-gated site, are **Manual** by
     default regardless of robots.txt.
   - Any failed item means Manual. Boards that require login are out of automation.
3. Record the verdict, including the Terms-of-Service finding (clause quoted or "no automation clause found"), in
   `profile/portals.md`. A board that fails stays in the list only as "manual: open in your browser".

Never take URLs from inside job postings or other untrusted pages as boards; search independently.

### 4d. Decision table (defaults)

| Situation | Propose |
|---|---|
| Tech role, remote OK | linkedin, himalayas, freehire, plus country board if covered |
| Tech role, on-site/hybrid in one country | linkedin, freehire (country filter), adzuna if covered, local niche boards |
| Design / product / marketing, remote OK | linkedin, himalayas, local niche boards |
| Non-tech (healthcare, trades, education, finance, sales) | linkedin, adzuna if covered, 2-4 local or sector boards from research; skip freehire; disable himalayas unless the user wants remote AND the role family appears in its feed |
| Country with no bundled coverage | linkedin plus researched local boards; offer `/add-portal` for each one worth automating |
| Denmark + reads Danish | add jobindex, jobnet, jobdanmark (and jobbank for academics) |
| Language the user does not work in | drop boards in that language, say why |
| Senior / executive | prefer LinkedIn, sector boards and recruiter networks; mark mass boards as low-yield |

### 4e. Confirm and write
Present the ranked list with a one-line reason and access verdict each. The user adds, removes and
reorders. For every confirmed board that has no bundled CLI and passed the robots check, hand off to
`/add-portal <url>` (it writes the entry into `profile/portals.md` itself). Do not scaffold a CLI
without the user's yes.

Write `profile/portals.md` with three sections: **Enabled** (skill name, why, rank), **Disabled**
(bundled CLIs deliberately off, one-line reason), **Manual / WebSearch only** (boards with no CLI).
`/scrape` reads this file as its portal list.

### 4f. Generate `profile/search-queries.md`
From the profile build:
- **Titles:** primary titles first, then synonyms, then adjacent titles (grouped by priority, 1 strongest).
- **Skill and domain keywords** that appear in real postings.
- **Exclusions:** seniority above or below the user's level, deal-breaker keywords, languages they do not work in.
- **Location filters:** tiers (ideal / acceptable / borderline / too far) from Step 2 topic 7, and the
  LinkedIn location strings and work-mode (remote / hybrid) to run.
- **Low-cost-market filter:** ask whether they want postings located only in low-cost labour markets
  dropped. If yes, record it so `/scrape` pipes results through `python3 tools/low_cost_markets.py`.
  Explain what it does first; default is off.
- Per-portal query hints (which portal gets which query), and `site:` WebSearch queries for the
  Manual / WebSearch-only boards.

---

## Step 5: Template and theme

1. Read `templates/cv/designed/TEMPLATE.md` and `templates/cover_letters/designed/TEMPLATE.md` for the
   available layouts, the build commands and the page budget (designed variant 1 page, ATS variant 1-2 pages).
2. Ask the user for: name as printed, accent colour(s), font choice among the bundled open-licence fonts,
   CV language. Write the answers to `profile/theme.json`.
3. Run a **test render** of the master CV. (The cover letter has no master build; it needs a letter
   module from `templates/cover_letters/designed/TEMPLATE.md`, so it is first rendered by `/apply`.) The master build command is
   `python3 templates/cv/designed/build.py --master`: it renders `profile/cv_content.py` into
   `cv/main_master.pdf` (ATS) and `cv/main_master_designed.pdf`. `cv_content.py` is the data, not a
   build target: do not pass it to `build.py` as the module argument. A **tailored** render
   (`build.py cv/main_<company>_<role>.py`) needs a per-application module copied from
   `templates/cv/designed/template.py`; create one only when `/apply` tailors for a posting, not
   during onboarding. Verify:
   `python3 tools/verify_pdf.py <pdf> --pages 1` (designed) and the ATS variant with the 1-2 page
   limit; also `--dump-text` to confirm email and phone are literal text.
4. View the rendered PDF (or tell the user where it is) and adjust theme or content until they approve.
5. To use a different template later, use `/add-template`, then `/onboard --section template`.

---

## Step 6: Standing rules

Ask, and record in `profile/deal-breakers.md`:
- Hard no's (on-site, relocation, industries, work types, unpaid test projects beyond a few hours).
- Location rules and any exception (for example, a country they would relocate to if the pay is right).
- Minimum salary and currency, or "unstated is fine".
- **Apply gates:** what score auto-applies versus drafts for review. Default: Good Fit (60+) auto-applies
  when the user has opted in; anything lower is drafted and left for approval. Nothing is ever
  submitted without the user having chosen this explicitly. Ask; do not assume.
- Job-alert roles: apply to all, or run through the same fit gate.

---

## Step 7: Optional Gmail alerts

Skip unless the user wants job-alert emails read automatically. If they do:
1. Explain what is accessed: `tools/gmail_client.py` reads the mailbox over IMAP with an app password
   (a Google app password; 2-step verification must be on). Nothing is sent. Drafts only.
2. The credential is stored in the macOS Keychain by default. On Linux or Windows, follow the
   environment-variable or `keyring` option documented in `tools/gmail_client.py`'s docstring.
   Never paste the password into chat or a file in the repo.
3. Smoke test: `python3 tools/gmail_client.py search "in:inbox newer_than:3d"`.
4. Note in `profile/deal-breakers.md` that alerts are enabled, and suggest creating job alerts on the
   chosen portals pointing at the user's mailbox.

---

## Step 8: Form-answer bank

Seed `profile/forms.md` from what is already known (work authorisation, notice period, salary, years
with key technologies, relocation, consents, links). Ask only for what is missing. New answers given
later during `/apply` or `/submit` are added there immediately.

---

## Step 9: Dry-run

Ask for one real posting (URL or pasted text) or use a plausible one for the role family. Run the fit
evaluation exactly as `/apply` step "evaluate fit" would, but stop before generating documents. Show
the score and reasoning, and check that: no placeholder tokens leaked, no other person's data appears,
location and language gates behave as the user described. Fix `profile/` if anything looks wrong.

---

## Step 10: Finish

Summarise what was created (list the files in `profile/`), the chosen portals in rank order, and next steps:

- `/scrape` to search the chosen boards now
- `/apply <url>` for a specific posting
- `/onboard --section <name>` to change one part later; `/add-portal` to add a board; `/reset` to wipe `profile/`

Remind them: `profile/` is private and gitignored; never commit or push it. Mention the LinkedIn and
job-board terms-of-service note from README.md: automated access can breach a site's terms, keep
volume low, personal use only.

---

## Design principles

- One canonical place for personal data (`profile/`), nothing personal in tracked files.
- Read before write; show changes before applying them; never fabricate facts.
- Portal choice is derived from the person (role, seniority, country, languages), verified live, and
  confirmed by them. Defaults are a starting proposal, not a fixed list.
- Respect access rules: no portal is automated if `robots.txt` or its terms say no or it needs a login.
- Works the same in Claude Code and Codex: nothing here depends on a runtime-specific tool.
