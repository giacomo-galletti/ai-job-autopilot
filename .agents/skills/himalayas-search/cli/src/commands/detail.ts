/**
 * Full text for one posting.
 *
 * himalayas.app's job pages return 403 to a non-browser client, so this does not fetch the
 * page. It does not need to: the feed already carries the full `description`, so detail is a
 * bounded scan of the feed for a matching guid or application link. The feed is newest-first,
 * so a job found by a recent search is normally a page or two in.
 */

import { PAGE_SIZE, fetchPage, formatSalary, isoDate, stripHtml } from "../helpers.js"

export interface DetailOpts {
  idOrUrl: string
  maxPages: number
}

export interface DetailResult {
  found: boolean
  scanned: number
  job?: {
    guid: string
    title: string
    company: string
    employmentType: string | null
    salary: string
    seniority: string[]
    location: string
    locationRestrictions: string[]
    timezoneRestrictions: number[]
    categories: string[]
    date: string
    expires: string
    url: string
    description: string
  }
}

/** Accepts a full URL, a guid, or a trailing slug - all three appear in search output. */
function matches(candidate: string, wanted: string): boolean {
  const norm = (s: string) => s.replace(/\/+$/, "").toLowerCase()
  const a = norm(candidate)
  const b = norm(wanted)
  return a === b || a.endsWith(`/${b}`)
}

export async function runDetail(opts: DetailOpts): Promise<DetailResult> {
  let cursor: string | null | undefined
  let scanned = 0

  for (let page = 0; page < opts.maxPages; page++) {
    const { jobs, nextCursor } = await fetchPage(cursor, PAGE_SIZE)
    if (!jobs.length) break
    scanned += jobs.length

    const job = jobs.find(
      (j) => matches(j.guid, opts.idOrUrl) || matches(j.applicationLink ?? "", opts.idOrUrl),
    )
    if (job) {
      return {
        found: true,
        scanned,
        job: {
          guid: job.guid,
          title: job.title,
          company: job.companyName,
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
          expires: isoDate(job.expiryDate),
          url: job.applicationLink || job.guid,
          description: stripHtml(job.description ?? ""),
        },
      }
    }

    if (!nextCursor) break
    cursor = nextCursor
  }

  return { found: false, scanned }
}
