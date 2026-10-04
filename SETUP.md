# Setup Guide

Detailed setup and troubleshooting. The short version is in [README.md](README.md): clone, open in
Claude Code or Codex, run `/onboard`.

## 1. Prerequisites

### Claude Code or Codex

- [Claude Code](https://claude.com/claude-code) needs a Claude subscription or API credits.
- [Codex](https://openai.com/codex) needs an OpenAI account with Codex access.

Codex reads `AGENTS.md`, which points to the workflow files in `.claude/`. It has no slash commands,
so ask for a workflow by name ("run the onboarding", "run the scrape").

### Python

Python 3.10+. Check with `python3 --version` (on Windows, `py --version`).

```bash
python3 -m venv .venv && source .venv/bin/activate      # optional but recommended
pip install -r requirements.txt
python3 -m playwright install chromium
```

Playwright's Chromium renders the CV and cover letter to PDF. `pymupdf` (AGPL-3.0) is used only by the
layout checker in `tools/verify_layout.py`; it is installed locally and not redistributed.

### Bun (optional, for the bundled job-board CLIs)

The CLIs in `.agents/skills/` are TypeScript and run with Bun. Without it, `/scrape` falls back to web search.

```bash
curl -fsSL https://bun.sh/install | bash                 # macOS / Linux
powershell -ExecutionPolicy Bypass -c "irm https://bun.sh/install.ps1 | iex"   # Windows
```

Most CLIs have zero runtime dependencies; `bun install` in a CLI folder only pulls TypeScript types.
`adzuna-search` needs free API keys: copy `.env.example` to `.env` (gitignored) and fill them in.

## 2. Clone

```bash
git clone https://github.com/giacomo-galletti/ai-job-autopilot.git
cd ai-job-autopilot
```

Your personal data goes only into `profile/`, which is gitignored. If you also edit tracked files and
want to keep those edits in a remote, use a **private** repository, never a public fork.
Verify at any time: `git check-ignore profile/` prints `profile/`.

## 3. Run the onboarding

```
/onboard
```

Intake paths: **A** documents folder (`documents/`: CV, LinkedIn export, diplomas, references, past
applications), **B** a single CV, **C** a guided interview. All three write the same files in `profile/`.

`/onboard` then:

1. chooses job boards for you (role family, seniority, country, remote preference, languages), checks
   each against `robots.txt`, and writes `profile/portals.md` and `profile/search-queries.md`;
2. sets your CV and cover-letter theme in `profile/theme.json` and does a test render;
3. records your deal-breakers and standing rules;
4. optionally connects Gmail job alerts;
5. seeds `profile/forms.md` with reusable form answers;
6. dry-runs a fit evaluation on a sample posting.

Change one part later:

```
/onboard --section portals     # also: identity, experience, behavioral, deal-breakers,
/onboard --section search      #       search, template, theme, gmail, forms
```

Wipe everything personal with `/reset profile`.

## 4. Optional: Gmail job alerts

`tools/gmail_client.py` reads your mailbox over IMAP with a Google **app password** (2-step
verification must be on). It reads and creates drafts; it never sends. The password is stored in the
macOS Keychain by default; see the docstring in `tools/gmail_client.py` for other platforms. Never
paste the password into chat or into a file in the repository.

## 5. Optional: salary benchmarking

Put salary data in `salary_data.json` (see `tools/README_SALARY_TOOL.md`) or convert a spreadsheet:

```bash
python3 tools/convert_salary_excel.py path/to/salary-data.xlsx --source "My Salary Data"
```

If you skip this, salary lookup is simply omitted.

## 6. Test the workflow

```
/apply https://example.com/jobs/123
```

or paste the posting text. The assistant evaluates fit, asks whether to proceed, drafts a CV and
cover letter, has a reviewer pass critique them, and presents the checked PDFs.

## Troubleshooting

### Job search CLI tools not working
Make sure Bun is installed and the CLI needs network access. For `adzuna-search`, check `.env`.
Run `python3 tools/robots_check.py <url>` to see whether a site allows automated access.

### PDF render fails
Run `python3 -m playwright install chromium`. Re-run `pip install -r requirements.txt` inside your venv.

### "salary_data.json not found"
Expected without salary benchmarking; the workflow skips that step.

### `profile/` is missing or empty
Run `/onboard`. If `git check-ignore profile/` prints nothing, do not continue: fix `.gitignore` first.

### Stale `.claude/settings.local.json`
Local permission overrides belong in the untracked `.claude/settings.local.json`. Delete it if it grants
broader access than you want.
