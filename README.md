# AI Job Autopilot

*An AI agent that automates your job search: it finds postings, scores your fit, writes a tailored CV
and cover letter for each one, and fills in the applications for you to review and send.*

It runs on your machine, in [Claude Code](https://claude.com/claude-code) or
[Codex](https://openai.com/codex). Run `/onboard` once and it learns your profile (from your CV, or by
interviewing you), picks the job boards that fit your role and country, and then does the repetitive work:

```
find jobs  ->  score fit against your profile  ->  tailor CV + cover letter  ->  fill the application  ->  track the result
(/scrape)      (/rank, /apply)                     (/apply)                        (/submit)                 (/outcome)
```

You stay in charge of what gets sent.

> This is an independent open-source project. It is not affiliated with, endorsed by, or maintained by
> Anthropic or OpenAI. It drafts documents and fills forms for you to review; you stay responsible for
> everything you send.

## Quick start

```bash
git clone https://github.com/giacomo-galletti/ai-job-autopilot.git
cd ai-job-autopilot
claude            # or: codex
```

Then, inside the assistant:

```
/onboard
```

Codex has no slash commands: say "Run the onboarding in `.claude/commands/onboard.md`".

`/onboard` takes about 15 minutes. It checks your tools, reads your CV (or interviews you), builds your
profile, proposes **job boards chosen for your role, seniority, country and languages**, sets up a CV
and cover-letter theme with a test render, optionally connects job-alert email, and finishes with a
dry-run evaluation of a sample posting. Re-run any part later with `/onboard --section <name>`.

Then try:

```
/scrape                       # search your chosen boards for new jobs
/apply <job posting URL>      # evaluate fit, draft CV + cover letter
```

## What you get

| Command | What it does |
|---|---|
| `/onboard` | Builds your private `profile/`, chooses job boards, sets the CV/letter theme |
| `/scrape` | Searches the boards you selected and deduplicates across runs |
| `/rank` | Batch-scores scraped postings and returns a ranked shortlist |
| `/apply <url>` | Fit evaluation, tailored CV and cover letter, reviewer pass, PDF checks |
| `/submit` | Fills an application form in a browser; you approve the send |
| `/interview` | Builds a stage-specific interview prep pack |
| `/outcome` | Records results (interviews, offers, rejections) and archives what was sent |
| `/upskill`, `/expand` | Skill-gap analysis; enrich the profile from public sources you link |
| `/job-alerts`, `/mail-cleanup`, `/gmail-sync` | Optional Gmail job-alert and confirmation handling |
| `/add-portal`, `/add-template` | Add a job board or a CV/letter template of your own |
| `/html-report`, `/notion-sync` | Dashboards of your pipeline |
| `/reset` | Wipes `profile/` (with confirmation) so you can start over |

Bundled job-board CLIs (in `.agents/skills/`, need [bun](https://bun.sh)): LinkedIn, Himalayas (remote),
freehire (tech), Adzuna (about eleven countries, free API key), and Danish boards (Jobindex, Jobnet,
Jobdanmark, Jobbank). `/onboard` enables only the ones that fit you and uses web search to find
well-known boards for your field and country; `/add-portal` builds a CLI for any board that permits it.

## Privacy model

Everything personal lives in **`profile/`**, which is **gitignored**. `profile.example/` holds the
empty templates and is tracked. Generated CVs, letters, the application tracker, scraper state and
job-alert data are gitignored too.

- Never commit or push `profile/`. Check with `git check-ignore profile/`.
- If you modify tracked files (templates, commands) and want to push them, keep that copy in a
  **private** repository. A public fork cannot be made private.
- Nothing is sent anywhere by the kit itself. The assistant you run it in sees what you show it.
- Gmail access, if enabled, is read plus draft only. The kit never sends mail.

## Requirements

- Claude Code or Codex
- Python 3.10+ and `pip install -r requirements.txt`, then `python3 -m playwright install chromium`
  (CVs and letters are rendered to PDF with Playwright)
- Optional: [bun](https://bun.sh) for the bundled job-board CLIs (web search is the fallback)
- Optional: Gmail with an app password for job-alert handling. The credential is stored in the macOS
  Keychain by default; see `tools/gmail_client.py` for other platforms.

Details and troubleshooting: [SETUP.md](SETUP.md).

## Repository layout

```
.claude/commands/        workflow definitions (/onboard, /scrape, /apply, ...), read by Claude Code and Codex
.claude/skills/          evaluation, writing and scraping guidance
.claude/agents/          sub-agents used by the multi-step cycles
.agents/skills/          job-board CLIs (one folder per board)
templates/cv/designed/   CV template; templates/cover_letters/designed/ the matching letter
tools/                   PDF verification, robots.txt check, Gmail client, trackers
profile.example/         empty profile templates (tracked)
cv/main_example.tex      stock LaTeX examples (and cover_letters/cover_example.tex) kept for CI; not user evidence
profile/                 YOUR data (gitignored, created by /onboard)
documents/               optional drop folders for your CV, LinkedIn export, past applications (gitignored content)
```

## Terms of service, honestly

Some job boards forbid automated access in their terms. LinkedIn's public job pages are the main
example: scraping them can breach LinkedIn's Terms of Service and may get your account restricted.
The kit keeps volume low, checks `robots.txt` before adding a board (`tools/robots_check.py`), and refuses
boards behind a login, but whether to use a given board is your decision and your responsibility.
Personal, low-volume use only; do not use it for bulk data collection or commercial resale.
Submitting applications automatically is also against some employers' policies; the default is that
you review and approve each send. Unattended auto-submit is off unless you turn it on during
`/onboard` (apply gates), and you can limit it to roles above a fit score you choose.

## Licenses and attribution

- This project is derived from [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search)
  (MIT, copyright Mads Lorentzen). The original licence is kept in [LICENSE](LICENSE).
- Job-board CLI skills originate from Mikkel Krogsholm's [skills repo](https://github.com/mikkelkrogsholm/skills).
- `pymupdf` (PyMuPDF), used by the layout checker, is licensed AGPL-3.0. It is installed as a
  separate dependency and not redistributed here; skip it if AGPL is a concern for you.
- Bundled fonts carry their own open licences, included next to the font files.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT, see [LICENSE](LICENSE).
