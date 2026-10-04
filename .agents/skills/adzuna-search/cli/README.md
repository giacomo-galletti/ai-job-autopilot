# adzuna-search CLI

Zero-dependency CLI for worldwide job search via the official
[Adzuna REST API](https://developer.adzuna.com/docs/search). Replaces the repo's
former Denmark-only HTML scrapers with a terms-of-service-compliant API client
that returns salary data and ranks results by pay.

## Runtime

No `npm`/`bun install` required. Runs under either:

```bash
node src/cli.ts <command> [flags]     # Node >= 23 (strips TypeScript types)
bun run src/cli.ts <command> [flags]  # Bun
```

## Credentials

Set in the environment (loaded from the repo's gitignored `.env`):

```
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

Get a free key at <https://developer.adzuna.com>. Credentials are read from the
environment only — never passed on the command line.

## Commands

```bash
# Search (salary-ranked across the default country set)
node src/cli.ts search -q "data engineer" --max-days-old 14 --format table

# Narrow to specific countries, JSON output
node src/cli.ts search -q "product manager" --country us,gb,de --format json

# Full text of one listing
node src/cli.ts detail "https://www.adzuna.com/land/ad/123456789"
```

See `node src/cli.ts --help` for all flags, or the parent `SKILL.md` for guidance.

## Tests

```bash
node --test            # pure-logic unit tests (no network)
```

## Typecheck (optional)

Requires installing dev deps first (`npm install`), then:

```bash
npm run typecheck
```
