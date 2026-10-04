#!/usr/bin/env node
// adzuna-search CLI — worldwide job search via the official Adzuna REST API.
// Zero dependencies. Runs under both `node src/cli.ts` and `bun run src/cli.ts`.
import { AdzunaError, writeError } from "./helpers.ts"
import { runSearch, type SearchOptions } from "./commands/search.ts"
import { runDetail, type DetailOptions } from "./commands/detail.ts"

const USAGE = `adzuna-search — worldwide job search (Adzuna API)

Usage:
  search [flags]                 Search jobs across one or more countries
  detail <url> [--format ...]    Best-effort full text for one job (by apply URL)

Search flags:
  -q, --query <text>        Keyword(s): role, skill, company
      --country <codes>     Comma list of Adzuna country codes (default: us,gb,de,nl,ca,fr,it,at,es,au,nz)
      --max-days-old <n>    Only jobs posted within N days
      --sort-by <mode>      salary | date | relevance | default   (default: salary)
      --results-per-page <n>  Per-country page size (default: 20, max 50)
      --page <n>            Page number, 1-indexed (default: 1)
      --limit <n>           Cap total rows after merging/ranking
      --format <fmt>        json | table | plain                  (default: table)
  -h, --help                Show this help

Credentials (required) are read from the environment, never the CLI:
  ADZUNA_APP_ID, ADZUNA_APP_KEY   (free key: https://developer.adzuna.com)
`

interface ParsedArgs {
  _: string[]
  flags: Record<string, string | boolean>
}

function parseArgs(argv: string[]): ParsedArgs {
  const out: ParsedArgs = { _: [], flags: {} }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === "-h" || a === "--help") {
      out.flags.help = true
    } else if (a === "-q" || a === "--query") {
      out.flags.query = argv[++i] ?? ""
    } else if (a.startsWith("--")) {
      const key = a.slice(2)
      const next = argv[i + 1]
      if (next === undefined || next.startsWith("-")) {
        out.flags[key] = true
      } else {
        out.flags[key] = next
        i++
      }
    } else {
      out._.push(a)
    }
  }
  return out
}

function asInt(v: string | boolean | undefined): number | undefined {
  if (typeof v !== "string") return undefined
  const n = parseInt(v, 10)
  return Number.isFinite(n) ? n : undefined
}

async function main(): Promise<void> {
  const argv = process.argv.slice(2)
  const { _, flags } = parseArgs(argv)
  const command = _[0]

  if (flags.help || !command) {
    process.stdout.write(USAGE)
    return
  }

  if (command === "search") {
    const format = (flags.format as string) || "table"
    if (!["json", "table", "plain"].includes(format)) {
      throw new AdzunaError(`Invalid --format "${format}" (use json|table|plain)`, "BAD_FORMAT")
    }
    const sortBy = ((flags["sort-by"] as string) || "salary") as SearchOptions["sortBy"]
    if (!["salary", "date", "relevance", "default"].includes(sortBy)) {
      throw new AdzunaError(`Invalid --sort-by "${sortBy}"`, "BAD_SORT")
    }
    const contractType = flags["contract-type"] as string | undefined
    if (contractType !== undefined && contractType !== "contract" && contractType !== "permanent") {
      throw new AdzunaError(`Invalid --contract-type "${contractType}" (use contract|permanent)`, "BAD_CONTRACT_TYPE")
    }
    const countries = typeof flags.country === "string"
      ? flags.country.split(",").map((s) => s.trim()).filter(Boolean)
      : []
    const opts: SearchOptions = {
      query: typeof flags.query === "string" ? flags.query : undefined,
      countries,
      page: asInt(flags.page) ?? 1,
      resultsPerPage: Math.min(asInt(flags["results-per-page"]) ?? 20, 50),
      maxDaysOld: asInt(flags["max-days-old"]),
      sortBy,
      contractType: contractType as SearchOptions["contractType"],
      limit: asInt(flags.limit),
      format: format as SearchOptions["format"],
    }
    await runSearch(opts)
    return
  }

  if (command === "detail") {
    const url = _[1]
    if (!url) throw new AdzunaError("detail requires a job URL argument", "BAD_URL")
    const format = (flags.format as string) || "plain"
    if (!["plain", "json"].includes(format)) {
      throw new AdzunaError(`Invalid --format "${format}" (use plain|json)`, "BAD_FORMAT")
    }
    const opts: DetailOptions = { url, format: format as DetailOptions["format"] }
    await runDetail(opts)
    return
  }

  throw new AdzunaError(`Unknown command "${command}". Run with --help.`, "BAD_COMMAND")
}

main().catch((err) => {
  if (err instanceof AdzunaError) {
    writeError(err.message, err.code)
  } else {
    writeError((err as Error).message ?? String(err), "UNEXPECTED")
  }
  process.exit(1)
})
