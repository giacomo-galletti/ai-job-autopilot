// `search` command: query Adzuna across one or more countries, rank by salary.
import {
  DEFAULT_COUNTRIES,
  SUPPORTED_COUNTRIES,
  AdzunaError,
  getCredentials,
  searchJobs,
  rankBySalary,
  formatTable,
  type Country,
  type JobCard,
  type SearchResult,
} from "../helpers.ts"

export interface SearchOptions {
  query?: string
  countries: string[]
  page: number
  resultsPerPage: number
  maxDaysOld?: number
  sortBy: "salary" | "date" | "relevance" | "default"
  contractType?: "contract" | "permanent"
  limit?: number
  format: "json" | "table" | "plain"
}

/** Validate + normalize the requested country codes. */
export function resolveCountries(input: string[]): Country[] {
  if (input.length === 0) return DEFAULT_COUNTRIES
  const out: Country[] = []
  for (const raw of input) {
    const c = raw.toLowerCase().trim()
    if (!(SUPPORTED_COUNTRIES as readonly string[]).includes(c)) {
      throw new AdzunaError(
        `Unsupported country code "${raw}". Supported: ${SUPPORTED_COUNTRIES.join(", ")}`,
        "BAD_COUNTRY",
      )
    }
    if (!out.includes(c as Country)) out.push(c as Country)
  }
  return out
}

export async function runSearch(opts: SearchOptions): Promise<void> {
  const creds = getCredentials()
  const countries = resolveCountries(opts.countries)

  // Per-country sort: Adzuna's "salary" sort is per-request; we also re-rank the
  // merged set client-side so the combined multi-country list is salary-ordered.
  const settled = await Promise.allSettled(
    countries.map((country) =>
      searchJobs(creds, {
        country,
        query: opts.query,
        page: opts.page,
        resultsPerPage: opts.resultsPerPage,
        maxDaysOld: opts.maxDaysOld,
      contractType: opts.contractType,
        sortBy: opts.sortBy,
      }),
    ),
  )

  const results: SearchResult[] = []
  const errors: { country: string; error: string }[] = []
  settled.forEach((r, i) => {
    if (r.status === "fulfilled") results.push(r.value)
    else errors.push({ country: countries[i], error: (r.reason as Error).message })
  })

  // A total failure (every country errored) is a real error — surface it and
  // exit non-zero. Partial failures are tolerated and reported in `errors`.
  if (results.length === 0 && errors.length > 0) {
    throw new AdzunaError(
      `All ${errors.length} country search(es) failed. First error: ${errors[0].error}`,
      "ALL_COUNTRIES_FAILED",
    )
  }

  let jobs: JobCard[] = results.flatMap((r) => r.jobs)
  if (opts.sortBy === "salary" || opts.sortBy === "default") {
    jobs = rankBySalary(jobs)
  }
  if (opts.limit && opts.limit > 0) jobs = jobs.slice(0, opts.limit)

  const totalCount = results.reduce((sum, r) => sum + r.count, 0)

  if (opts.format === "json") {
    process.stdout.write(
      JSON.stringify(
        {
          meta: {
            countries,
            query: opts.query ?? null,
            returned: jobs.length,
            total: totalCount,
            errors,
          },
          results: jobs,
        },
        null,
        2,
      ) + "\n",
    )
    return
  }

  // table / plain summary
  process.stdout.write(formatTable(jobs) + "\n")
  process.stdout.write(
    `\n${jobs.length} shown across ${countries.length} ${countries.length === 1 ? "country" : "countries"} ` +
      `(${totalCount.toLocaleString("en-US")} total matches).\n`,
  )
  if (errors.length > 0) {
    process.stdout.write(
      `\nNote: ${errors.length} country search(es) failed: ${errors
        .map((e) => `${e.country} (${e.error})`)
        .join("; ")}\n`,
    )
  }
}
