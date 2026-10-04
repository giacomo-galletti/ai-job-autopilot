/**
 * Search the himalayas feed with client-side filters.
 *
 * Every filter here runs after the fetch, because the feed ignores query parameters. That
 * makes `--pages` the real cost control: each page is one request for 100 jobs.
 */

import { PAGE_SIZE, fetchPage, formatSalary, isoDate, stripHtml } from "../helpers.js"
import type { HimalayasJob } from "../helpers.js"

export interface SearchOpts {
  query?: string
  category?: string[]
  seniority?: string[]
  maxDaysOld?: number
  timezone?: number
  timezoneTolerance: number
  hireableFrom?: string
  pages: number
  limit?: number
  includeDescription: boolean
}

export interface SearchRow {
  guid: string
  title: string
  company: string
  companySlug: string
  employmentType: string | null
  salary: string
  seniority: string[]
  /** The /scrape Step 2 contract field. Every job here is remote; this says remote to whom. */
  location: string
  locationRestrictions: string[]
  timezoneRestrictions: number[]
  categories: string[]
  date: string
  url: string
  description?: string
}

const lower = (s: string) => s.toLowerCase()

/** A job matches the query when any word of it appears in title, excerpt or categories. */
function matchesQuery(job: HimalayasJob, query: string): boolean {
  const haystack = lower(
    [job.title, job.excerpt, job.categories.join(" "), job.parentCategories.join(" ")].join(" "),
  )
  return query
    .split(/\s+OR\s+|\s*\|\s*/i)
    .map((term) => lower(term.trim()))
    .filter(Boolean)
    .some((term) => haystack.includes(term))
}

function matchesAny(values: string[], wanted: string[]): boolean {
  const have = values.map(lower)
  return wanted.some((w) => have.some((v) => v.includes(lower(w))))
}

/**
 * Can someone in `country` take this job?
 *
 * An empty locationRestrictions list means worldwide - that is the common case and it passes.
 * Otherwise the country (or its region, e.g. "Europe"/"EMEA"/"EU") has to be named. A job
 * restricted to "United States" is excluded rather than surfaced and rejected later: a
 * country-locked posting is not a near miss, it is a no.
 */
export function hireableFrom(job: HimalayasJob, country: string): boolean {
  if (!job.locationRestrictions?.length) return true
  const wanted = lower(country)
  const regions = ["worldwide", "anywhere", "global", "remote"]
  if (wanted === "italy" || wanted === "it") {
    regions.push("europe", "emea", "european union", "eu", "eea", "italy", "cet")
  }
  return job.locationRestrictions.some((r) => {
    const restriction = lower(r)
    return restriction.includes(wanted) || regions.some((g) => restriction.includes(g))
  })
}

/** Does the job's timezone band overlap `tz` within `tolerance` hours? */
export function timezoneOverlaps(job: HimalayasJob, tz: number, tolerance: number): boolean {
  if (!job.timezoneRestrictions?.length) return true
  return job.timezoneRestrictions.some((offset) => Math.abs(offset - tz) <= tolerance)
}

export interface SearchResult {
  results: SearchRow[]
  scanned: number
  /**
   * True when the scan stopped before covering what was asked: the --pages budget ran out
   * before --max-days-old was reached, or a later page failed. Every result is still real,
   * but postings older than `oldestScanned` were never looked at.
   */
  truncated: boolean
  /** Publication date of the oldest posting scanned, so a reader sees how far back it got. */
  oldestScanned: string | null
  /** Why a later page stopped the scan, when one did. */
  error?: string
}

export async function runSearch(opts: SearchOpts, getPage = fetchPage): Promise<SearchResult> {
  const cutoff =
    opts.maxDaysOld === undefined ? null : Date.now() / 1000 - opts.maxDaysOld * 86400

  const rows: SearchRow[] = []
  let cursor: string | null | undefined
  let scanned = 0
  let oldest: number | null = null
  let covered = false // reached the cutoff or the end of the feed
  const coverage = () => ({ scanned, oldestScanned: oldest === null ? null : isoDate(oldest) })

  for (let page = 0; page < opts.pages; page++) {
    let fetched: Awaited<ReturnType<typeof fetchPage>>
    try {
      fetched = await getPage(cursor, PAGE_SIZE)
    } catch (err) {
      // Nothing collected yet: a real error. Otherwise keep the pages already scanned.
      if (page === 0) throw err
      return { results: rows, ...coverage(), truncated: true, error: err instanceof Error ? err.message : String(err) }
    }
    const { jobs, nextCursor } = fetched
    if (!jobs.length) {
      covered = true
      break
    }
    scanned += jobs.length

    for (const job of jobs) {
      oldest = oldest === null ? job.pubDate : Math.min(oldest, job.pubDate)
      if (cutoff !== null && job.pubDate < cutoff) continue
      if (opts.query && !matchesQuery(job, opts.query)) continue
      if (opts.category?.length && !matchesAny([...job.categories, ...job.parentCategories], opts.category)) continue
      if (opts.seniority?.length && !matchesAny(job.seniority ?? [], opts.seniority)) continue
      if (opts.hireableFrom && !hireableFrom(job, opts.hireableFrom)) continue
      if (opts.timezone !== undefined && !timezoneOverlaps(job, opts.timezone, opts.timezoneTolerance)) continue

      rows.push({
        guid: job.guid,
        title: job.title,
        company: job.companyName,
        companySlug: job.companySlug,
        employmentType: job.employmentType,
        salary: formatSalary(job),
        seniority: job.seniority ?? [],
        location: job.locationRestrictions?.length
          ? `Remote (${job.locationRestrictions.join(", ")})`
          : "Remote (Worldwide)",
        locationRestrictions: job.locationRestrictions ?? [],
        timezoneRestrictions: job.timezoneRestrictions ?? [],
        categories: job.categories ?? [],
        date: isoDate(job.pubDate),
        url: job.applicationLink || job.guid,
        ...(opts.includeDescription ? { description: stripHtml(job.description ?? "") } : {}),
      })

      // --limit is a cap the caller asked for, not lost coverage.
      if (opts.limit && rows.length >= opts.limit) return { results: rows, ...coverage(), truncated: false }
    }

    // The feed is newest-first, so once a whole page predates the cutoff there is no
    // point paging further back.
    if ((cutoff !== null && jobs.every((j) => j.pubDate < cutoff)) || !nextCursor) {
      covered = true
      break
    }
    cursor = nextCursor
  }

  // Without --max-days-old the page budget is the whole request, so running it out is not a
  // shortfall. With it, stopping before the cutoff means part of the window went unscanned.
  return { results: rows, ...coverage(), truncated: cutoff !== null && !covered }
}
