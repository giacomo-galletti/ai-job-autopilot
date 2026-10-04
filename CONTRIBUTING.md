# Contributing

Thanks for considering a contribution. This project is a general template: people clone it and adapt
it to their own market, language and profile. Contributions are judged first on whether they keep it
market-agnostic and person-agnostic, then on execution quality.

## What fits

- Fixes with a demonstrated failing case (a test is ideal).
- Improvements to `/onboard`, portal selection and the evaluation, writing and scraping guidance that
  help many users.
- Portal CLIs that follow the contract below and permit automated access.
- Better fonts, themes and templates under open licences.
- Documentation fixes.

## What does not fit

- Anything containing personal data: names, contact details, employers, salary figures, real
  application records. Use neutral fixtures such as "Alex Example" and `example.com` addresses.
- Features that submit applications without the user's review and approval.
- Code that bypasses a site's `robots.txt`, login wall or rate limits.
- Cosmetic rewrites of working code.

## Privacy rules for contributors

- Never commit `profile/`, `documents/` content, generated CVs or letters, trackers, `.env` or scraper state.
  They are gitignored; if `git status` shows one, stop.
- Tests must not depend on a real person's data.
- Run `python3 tools/security_guards.py` and the test suite before opening a PR.

## Portal-skill contract

`search` and `detail` commands, `--format json|table|plain`, errors as JSON on stderr with exit 1,
backoff on 429/5xx, zero runtime dependencies by default. See `.claude/commands/add-portal.md`.
Portals that touch terms-restricted sources carry a prominent personal-use warning. CI makes no live
portal requests; keep it that way.

## Development

```bash
pip install -r requirements.txt
python3 -m pytest tests -q
python3 tools/lint_skills.py
```

Commands are plain markdown specs read by both Claude Code and Codex. Do not rely on a
runtime-specific tool in them. Questions and proposals are welcome in issues before you build.
