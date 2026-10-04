---
name: himalayas-search
version: 1.0.0
description: >
  Use this skill to search live remote job listings worldwide via the himalayas.app public
  feed, or to look up one posting. Every job on himalayas.app is remote, so it is the right
  source for a remote-only search; the feed carries ~99k postings across engineering, design,
  product, marketing and support. Its key field for a candidate who can only be hired in some
  countries is locationRestrictions, which this CLI filters on. Trigger phrases: remote jobs,
  work from anywhere, worldwide remote roles, remote developer jobs, remote design jobs,
  "remote jobs I can do from <country>", jobs open to Europe, look up this himalayas posting.
context: fork
enabled: true  # set to false to keep this portal installed but have /scrape skip it
allowed-tools: Bash(bun run .agents/skills/himalayas-search/cli/src/cli.ts *)
---

# himalayas Search Skill

Search live remote job listings from the **[himalayas.app](https://himalayas.app)** feed.
Public JSON, no authentication, no key. `robots.txt` permits `/jobs/api`; checked 2026-09-18.

## The one thing to know

**The feed ignores every filter you send it.** `?categories=Frontend`, `?seniority=Senior` and
`?search=x` all return the same unfiltered result set, and `?limit=100` returns 20. So this CLI
pages the feed and filters client-side, and `--pages` is the real cost control: one request per
20 jobs. A 60-page scan is 1,200 postings and takes roughly a minute.

Because filtering is local, the filters are better than a typical board's: `--hireable-from`
reads each job's `locationRestrictions` and drops the ones a candidate in that country cannot
take, which on this feed is most of them.

## Commands

```
bun run .agents/skills/himalayas-search/cli/src/cli.ts search [flags]
bun run .agents/skills/himalayas-search/cli/src/cli.ts detail <guid|url> [--max-pages <n>]
```

### Search flags

**Run its queries one after another.** Firing several searches at once (each pages through the feed) gets HTTP 429 from himalayas.app, seen 2026-10-04 when four recipe queries ran in parallel; `helpers.ts` backs off, but not enough for that load. Run them sequentially, or combine alternatives into one `--query "a OR b"`. Other portals can still run alongside it.

| Flag | Meaning |
|---|---|
| `--query`, `-q` | Keywords against title, excerpt and categories. `OR` or `\|` separates alternatives. |
| `--category` | Comma list against the job's categories and parentCategories. |
| `--seniority` | Comma list, e.g. `Senior,Lead`. |
| `--max-days-old` | Only jobs published within N days. |
| `--hireable-from` | Drop jobs whose `locationRestrictions` exclude that country. `Italy` also accepts Europe / EU / EEA / EMEA-wide postings. |
| `--timezone` | Keep jobs whose `timezoneRestrictions` overlap this UTC offset. Central Europe is `1` (CET) or `2` (CEST). |
| `--tz-tolerance` | How far a timezone may differ and still count. Default `3`. |
| `--pages` | Feed pages to scan, 20 jobs each. Default `40`. |
| `--limit`, `-n` | Stop after N matches. |
| `--no-description` | Omit descriptions for a cheaper discovery pass. |
| `--format` | `json` (default), `table`, `plain`. |

## Examples

```sh
# Remote design/front-end roles, country restrictions left visible for ranking
bun run .agents/skills/himalayas-search/cli/src/cli.ts search \
  -q "frontend OR design engineer OR product designer" \
  --max-days-old 14 --pages 60 --no-description --format table

# Only roles with no location restriction at all (a narrow, high-confidence list)
bun run .agents/skills/himalayas-search/cli/src/cli.ts search \
  -q "frontend OR design engineer OR product designer" \
  --hireable-from Italy --max-days-old 14 --pages 60 --no-description --format table

# Senior design work in a European timezone
bun run .agents/skills/himalayas-search/cli/src/cli.ts search \
  --category Design,Frontend --seniority Senior,Lead --timezone 2 --pages 40 --format table

# AI product roles, worldwide, last week
bun run .agents/skills/himalayas-search/cli/src/cli.ts search \
  -q "AI OR LLM OR machine learning" --category Developer --max-days-old 7 --format json

# Full text for one posting
bun run .agents/skills/himalayas-search/cli/src/cli.ts detail \
  https://himalayas.app/companies/acme/jobs/senior-frontend --format plain
```

## Output

| Field | Notes |
|---|---|
| `title`, `company`, `companySlug` | |
| `salary` | Formatted from minSalary/maxSalary/currency/salaryPeriod; empty when the posting states none |
| `seniority` | The feed's own list, e.g. `["Senior"]` |
| `locationRestrictions` | **Empty means worldwide.** Otherwise the only countries/regions that can be hired |
| `timezoneRestrictions` | UTC offsets the employer will work with; empty means any |
| `categories`, `date`, `url`, `description` | `description` is HTML in the feed and is stripped to text here |

## Notes

- **`--hireable-from` is a hard drop, so use it deliberately.** In a 1,200-posting scan most
  matching roles were locked to one country (United States, India, Pakistan, Philippines) and the
  flag cut them all. That is right for a candidate who needs local employment and **wrong for one
  who contracts through their own company**: a "United States" lock is usually a payroll
  constraint that an invoice from an EU entity sidesteps. Prefer running without the flag and
  ranking on the `location` field instead - see `profile/profile.md`'s Engagement Model for
  the four things a country lock can mean. Use the flag when a deliberately narrow,
  no-restrictions-at-all list is what you want.
- **Job pages refuse non-browser clients** (HTTP 403), so `detail` does not fetch them. It does
  not need to: the feed carries the full description. `detail` is a bounded scan of the feed,
  so a posting older than `--max-pages × 20` will not be found - raise the flag for old jobs.
- The feed is newest-first, so `--max-days-old` stops paging once a whole page predates the cutoff.
- The output says how far back the scan really got: `truncated` is `true` when `--pages` ran out
  before `--max-days-old` was reached (or a later page failed, with `error` saying why), and
  `oldest_scanned` is the publication date of the oldest posting looked at. A truncated run also
  prints a warning on stderr. On 2026-09-24, 60 pages (1,200 postings) covered about two days,
  so a 14-day window needs far more pages than the recipes below use.
- If a page after the first fails even after retries, the postings already scanned are kept
  and returned with `truncated: true`; only a failing first page is an error.
- `HIMALAYAS_API_URL` overrides the base URL, for testing against a fixture server.
