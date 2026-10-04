# Search Queries for Job Scraper (method)

The candidate-specific part (scope, target functions, titles, keywords, per-portal recipes) lives
in `profile/search-queries.md`, written by `/onboard`. The enabled portals and the reasons are in
`profile/portals.md`; hard limits (location, low-cost markets, country rules) are in
`profile/deal-breakers.md`. If `profile/` is missing, run `/onboard` first. This file holds only
the generic method.

## Portal notes (generic)

**Indeed is deliberately absent from the bundled set.** Its terms prohibit automated access and the
site returns HTTP 403 to any honest client; reaching it would mean impersonating a browser to defeat
bot protection. Adzuna covers part of the same aggregated market under an official API. Check
`tools/robots_check.py` before scaffolding any new portal, and respect a `robots.txt` that
disallows the path.

Per-portal recipes in `profile/search-queries.md` use the CLI flags documented in each portal's
SKILL.md. Check `truncated` and `oldest_scanned` in client-filtering CLIs (for example
`himalayas-search`) and report the real search window in the `/scrape` summary rather than a
nominal one.

The `site:` templates in `profile/search-queries.md` are the **WebSearch fallback** only - for
boards without a CLI, company career pages, or when a CLI fails.

## Scoring hints for Step 3 (generic)

Apply the candidate-specific hints in `profile/search-queries.md`, then these:

Rank a match **up** when the posting says: contract, contractor, freelance, B2B, day rate,
"we work with contractors", agency, studio, project-based, fractional or fixed-term, **if** the
profile's engagement model (see `profile/profile.md`) offers contract work. For UK contracts,
"outside IR35" is a positive signal and "inside IR35" is usually a worse fit.

Drop before presenting: whatever `profile/deal-breakers.md` lists as a hard no, a language
requirement the candidate does not declare, unpaid trial projects beyond a few hours, and
requirements the profile cannot meet and the posting hard-gates (clearance, PhD).

**A country restriction is a flag, not a drop** unless `profile/deal-breakers.md` says otherwise.
Present it with a note on which kind it looks like (payroll / timezone / legal / rate arbitrage;
see the country-restriction section of `profile/deal-breakers.md`). Low-cost-market postings are
dropped at search time by `tools/low_cost_markets.py` when the profile enables that filter, and
never reach this step.
