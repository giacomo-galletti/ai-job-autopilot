#!/usr/bin/env bun
/**
 * himalayas-cli - search the himalayas.app remote-jobs feed.
 *
 * The feed is public, unauthenticated and unfiltered: it ignores every query parameter
 * except limit/offset/cursor. All filtering below happens client-side after fetching, so
 * `--pages` is the cost control - one request per 100 jobs.
 */

import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"

const FORMATS = ["json", "table", "plain"] as const
type Format = (typeof FORMATS)[number]

const HELP = `himalayas-cli - search remote jobs on himalayas.app (worldwide, remote-only)

USAGE
  bun run src/cli.ts search [flags]
  bun run src/cli.ts detail <guid|url> [--max-pages <n>] [--format json|plain]

SEARCH FLAGS
  --query, -q <text>        Keywords matched against title, excerpt and categories.
                            Use OR or | to pass alternatives: -q "frontend OR design engineer"
  --category <names>        Comma list matched against the job's categories and
                            parentCategories, e.g. --category Frontend,Design
  --seniority <levels>      Comma list, e.g. --seniority Senior,Lead
  --max-days-old <n>        Only jobs published within N days.
  --hireable-from <country> Drop jobs whose locationRestrictions exclude that country.
                            "Italy" also accepts Europe/EU/EEA/EMEA-wide postings.
  --timezone <offset>       Keep jobs whose timezoneRestrictions overlap this UTC offset.
                            Central Europe is 1 (CET) / 2 (CEST).
  --tz-tolerance <hours>    How far a timezone may differ and still count. Default 3.
  --pages <n>               Feed pages to scan, 20 jobs each (the server's cap). Default 40.
  --limit, -n <n>           Stop after N matches.
  --no-description          Omit the full description for a cheaper discovery pass.
  --format <fmt>            json (default) | table | plain

EXAMPLES
  bun run src/cli.ts search -q "frontend OR design engineer" --hireable-from Italy --max-days-old 14 --format table
  bun run src/cli.ts search --category Frontend,Design --seniority Senior --timezone 2 --pages 8 --format table
  bun run src/cli.ts search -q "product designer" --hireable-from Italy --no-description --limit 20 --format table
  bun run src/cli.ts search -q "AI OR LLM" --category Developer --max-days-old 7 --format json
  bun run src/cli.ts detail https://himalayas.app/companies/acme/jobs/senior-frontend --format plain

NOTES
  Every posting on himalayas.app is remote, so there is no on-site noise to filter out.
  Job pages themselves refuse non-browser clients, so detail reads the feed instead -
  bounded by --max-pages, and a job older than that window will not be found.
`

function fail(message: string): never {
  console.error(`error: ${message}`)
  process.exit(2)
}

function takeValue(args: string[], i: number, flag: string): string {
  const value = args[i + 1]
  if (value === undefined || value.startsWith("--")) fail(`${flag} needs a value`)
  return value
}

function asInt(raw: string, flag: string): number {
  const n = Number(raw)
  if (!Number.isFinite(n) || !Number.isInteger(n)) fail(`${flag} must be a whole number, got ${raw}`)
  return n
}

function list(raw: string): string[] {
  return raw.split(",").map((s) => s.trim()).filter(Boolean)
}

async function main() {
  const args = process.argv.slice(2)
  if (!args.length || args.includes("--help") || args.includes("-h")) {
    console.log(HELP)
    return
  }

  const command = args[0]
  let format: Format = "json"

  if (command === "search") {
    const opts: SearchOpts = { pages: 40, timezoneTolerance: 3, includeDescription: true }
    for (let i = 1; i < args.length; i++) {
      const arg = args[i]
      switch (arg) {
        case "--query": case "-q": opts.query = takeValue(args, i++, arg); break
        case "--category": opts.category = list(takeValue(args, i++, arg)); break
        case "--seniority": opts.seniority = list(takeValue(args, i++, arg)); break
        case "--max-days-old": opts.maxDaysOld = asInt(takeValue(args, i++, arg), arg); break
        case "--hireable-from": opts.hireableFrom = takeValue(args, i++, arg); break
        case "--timezone": opts.timezone = asInt(takeValue(args, i++, arg), arg); break
        case "--tz-tolerance": opts.timezoneTolerance = asInt(takeValue(args, i++, arg), arg); break
        case "--pages": opts.pages = asInt(takeValue(args, i++, arg), arg); break
        case "--limit": case "-n": opts.limit = asInt(takeValue(args, i++, arg), arg); break
        case "--no-description": opts.includeDescription = false; break
        case "--format": {
          const value = takeValue(args, i++, arg) as Format
          if (!FORMATS.includes(value)) fail(`--format must be one of ${FORMATS.join(", ")}`)
          format = value
          break
        }
        default: fail(`unknown flag ${arg}`)
      }
    }
    if (opts.pages < 1) fail("--pages must be at least 1")

    const { results, scanned, truncated, oldestScanned, error } = await runSearch(opts)
    if (truncated) {
      // stderr, so a JSON consumer still gets clean stdout but a person running it sees the gap.
      console.error(
        `warning: coverage stopped at postings from ${oldestScanned ?? "an unknown date"}, short of ` +
          `--max-days-old ${opts.maxDaysOld}` + (error ? ` (${error})` : `; raise --pages to reach further back`),
      )
    }

    if (format === "json") {
      console.log(JSON.stringify({
        count: results.length, scanned, truncated, oldest_scanned: oldestScanned,
        ...(error ? { error } : {}), results,
      }, null, 2))
      return
    }
    if (!results.length) {
      console.log(`No matches (scanned ${scanned} postings).`)
      return
    }
    if (format === "table") {
      const pad = (s: string, w: number) => (s.length > w ? s.slice(0, w - 1) + "…" : s.padEnd(w))
      console.log(
        pad("TITLE", 44) + pad("COMPANY", 22) + pad("SALARY", 20) + pad("OPEN TO", 24) + "DATE",
      )
      console.log("-".repeat(120))
      for (const r of results) {
        const openTo = r.locationRestrictions.length ? r.locationRestrictions.join(", ") : "Worldwide"
        console.log(pad(r.title, 44) + pad(r.company, 22) + pad(r.salary || "-", 20) + pad(openTo, 24) + r.date)
      }
      console.log(`\n${results.length} match(es) from ${scanned} postings scanned.`)
      return
    }
    for (const r of results) {
      console.log(`${r.title}\n${r.company} · ${r.locationRestrictions.join(", ") || "Worldwide"} · ${r.date}`)
      if (r.salary) console.log(`Salary: ${r.salary}`)
      console.log(r.url)
      if (r.description) console.log(`\n${r.description}\n`)
      console.log("-".repeat(60))
    }
    return
  }

  if (command === "detail") {
    const idOrUrl = args[1]
    if (!idOrUrl || idOrUrl.startsWith("--")) fail("detail needs a guid or URL")
    const opts: DetailOpts = { idOrUrl, maxPages: 25 }
    for (let i = 2; i < args.length; i++) {
      const arg = args[i]
      switch (arg) {
        case "--max-pages": opts.maxPages = asInt(takeValue(args, i++, arg), arg); break
        case "--format": {
          const value = takeValue(args, i++, arg) as Format
          if (value !== "json" && value !== "plain") fail("detail --format must be json or plain")
          format = value
          break
        }
        default: fail(`unknown flag ${arg}`)
      }
    }

    const result = await runDetail(opts)
    if (format === "json") {
      console.log(JSON.stringify(result, null, 2))
      return
    }
    if (!result.found || !result.job) {
      console.log(
        `Not found in the newest ${result.scanned} postings. The feed is newest-first, so raise --max-pages for an older job.`,
      )
      process.exit(1)
    }
    const j = result.job
    console.log(`${j.title}\n${j.company} · ${j.locationRestrictions.join(", ") || "Worldwide"} · ${j.date}`)
    if (j.employmentType) console.log(`Employment: ${j.employmentType}`)
    if (j.salary) console.log(`Salary: ${j.salary}`)
    if (j.seniority.length) console.log(`Seniority: ${j.seniority.join(", ")}`)
    if (j.categories.length) console.log(`Categories: ${j.categories.slice(0, 12).join(", ")}`)
    console.log(`Expires: ${j.expires}`)
    console.log(`URL: ${j.url}\n`)
    console.log(j.description)
    return
  }

  fail(`unknown command ${command}. Use search or detail.`)
}

main().catch((err) => {
  console.error(`error: ${err instanceof Error ? err.message : String(err)}`)
  process.exit(1)
})
