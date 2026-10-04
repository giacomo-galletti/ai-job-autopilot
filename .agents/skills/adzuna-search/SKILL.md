---
name: adzuna-search
version: 1.0.0
description: >
  Use this skill whenever the user wants to search for jobs worldwide, find job
  listings, look up open positions, or explore the job market in high-paying
  countries across Europe, the Americas, and Oceania — even if they don't mention
  Adzuna explicitly. Invoke for questions about open positions, vacancies, hiring,
  or "find me a job" in the US, UK, Germany, Netherlands, Canada, France, Italy,
  Austria, Spain, Australia, New Zealand, and other Adzuna-supported markets.
  Trigger phrases include: find job, job search, jobs in <country/city>, open
  positions, vacancies, hiring, software engineer jobs, data scientist jobs,
  remote jobs, high paying jobs, jobs in the US, jobs in London, jobs in Berlin,
  jobs in Amsterdam, developer jobs Europe, salary, well-paid roles.
context: fork
allowed-tools: Bash(node .agents/skills/adzuna-search/cli/src/cli.ts *), Bash(bun run .agents/skills/adzuna-search/cli/src/cli.ts *)
---

# Adzuna Worldwide Search Skill

Search live job listings worldwide via the **official Adzuna REST API** — no HTML
scraping, fully terms-of-service compliant. Covers high-paying markets in Europe,
the Americas, and Oceania, with **salary data** so results can be ranked by pay.

## Credentials (required)

The CLI reads `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` from the environment (loaded
from the gitignored `.env`). Get a free key at <https://developer.adzuna.com>.
Never pass credentials on the command line.

## Runtime

The CLI is zero-dependency and runs under **both** Node (≥23, no install needed)
and Bun:

```bash
node .agents/skills/adzuna-search/cli/src/cli.ts <command> [flags]
# or
bun run .agents/skills/adzuna-search/cli/src/cli.ts <command> [flags]
```

## When to use this skill

- Search jobs by keyword/title/skill across one or more countries
- Find the highest-paying matches (results rank by salary by default)
- Filter by recency (`--max-days-old`)
- Get the full text of a specific listing (`detail <url>`)

## Commands

### Search

```bash
node .agents/skills/adzuna-search/cli/src/cli.ts search [flags]
```

| Flag | Meaning |
|------|---------|
| `-q, --query <text>` | Keyword(s): role, skill, company. Strongly recommended. |
| `--country <codes>` | Comma list of Adzuna country codes. Default: `us,gb,de,nl,ca,fr,it,at,es,au,nz` |
| `--max-days-old <n>` | Only jobs posted within N days |
| `--sort-by <mode>` | `salary` (default) \| `date` \| `relevance` \| `default` |
| `--results-per-page <n>` | Per-country page size (default 20, max 50) |
| `--page <n>` | Page number, 1-indexed (default 1) |
| `--limit <n>` | Cap total rows after merging + ranking |
| `--format <fmt>` | `json` (default for processing) \| `table` \| `plain` |

Results from all requested countries are merged and **re-ranked by salary
descending**; listings without a published salary sort last (never dropped).

### Detail

```bash
node .agents/skills/adzuna-search/cli/src/cli.ts detail <url> [--format plain|json]
```

`<url>` is the `url` field from a search result. Adzuna's free API has no
get-by-id endpoint, so `detail` fetches the public job page and returns cleaned
text (best-effort — employer page formats vary).

## How to use effectively

1. **Always pass `--query`.** Combine role + key skill, e.g. `--query "data engineer python"`.
2. **Default country set is broad.** Narrow with `--country us,gb` for focused runs, or widen to any supported code on demand.
3. **`--max-days-old 14`** keeps results fresh.
4. **Salary ranking is on by default** (`--sort-by salary`). Use `--sort-by date` for newest-first.
5. **Workflow:** `search --format json` → pick promising `url`s → `detail <url>` for full text.

## Usage examples

```bash
# Highest-paying data engineering roles across the default country set, last 14 days
node .agents/skills/adzuna-search/cli/src/cli.ts search \
  --query "data engineer" --max-days-old 14 --limit 25 --format table

# Remote software roles, US + UK only, JSON for processing
node .agents/skills/adzuna-search/cli/src/cli.ts search \
  --query "remote software engineer" --country us,gb --format json

# Newest product manager listings in Germany & Netherlands
node .agents/skills/adzuna-search/cli/src/cli.ts search \
  --query "product manager" --country de,nl --sort-by date --format table

# Full text of one listing
node .agents/skills/adzuna-search/cli/src/cli.ts detail "https://www.adzuna.com/land/ad/123456789"
```

## Output & errors

- `json` carries full structured fields incl. `salaryMin`/`salaryMax`/`currency` — use for processing and to pass `url` to `detail`.
- `table` is a quick salary-ranked overview; `plain` is for reading one job.
- Errors → **stderr** as `{ "error": "...", "code": "..." }`, exit code `1`.
- Per-country failures are tolerated and reported under `meta.errors`; if **all** countries fail, the command exits `1`.

## Notes

- All data comes from the official Adzuna API — no scraping, no auth against job boards.
- Salaries are in each country's **local currency** (shown per row). No currency conversion is performed.
- `salary_is_predicted` listings are marked `(est.)`.
- This skill does **not** apply to jobs. Applications are prepared as documents for the user to submit manually.
