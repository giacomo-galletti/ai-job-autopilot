/**
 * Shared plumbing for the himalayas.app feed.
 *
 * The feed at /jobs/api is exactly that: a feed. It accepts `limit`, `offset` and `cursor`
 * and ignores every filter parameter you pass it - `?categories=Frontend` and `?search=x`
 * both come back with the same unfiltered 98k-job total. So this CLI pages the feed and
 * filters client-side, which is slower but honest about what the API actually does.
 */

export const BASE_URL = process.env.HIMALAYAS_API_URL ?? "https://himalayas.app"
export const USER_AGENT = "Mozilla/5.0 (compatible; himalayas-cli/1.0)"

/**
 * Jobs per request. The feed accepts a `limit` and then ignores it: asking for 100 returns
 * 20, which is the real server-side cap. Setting it honestly here keeps `--pages` meaning
 * what the help text says it means.
 */
export const PAGE_SIZE = 20

export interface HimalayasJob {
  title: string
  excerpt: string
  companyName: string
  companySlug: string
  employmentType: string | null
  minSalary: number | null
  maxSalary: number | null
  salaryPeriod: string | null
  currency: string | null
  seniority: string[]
  locationRestrictions: string[]
  timezoneRestrictions: number[]
  categories: string[]
  parentCategories: string[]
  description: string
  pubDate: number
  expiryDate: number
  applicationLink: string
  guid: string
}

export interface FeedPage {
  jobs: HimalayasJob[]
  nextCursor?: string | null
  totalCount?: number
}

export class HttpError extends Error {
  constructor(readonly status: number, message: string) {
    super(message)
  }
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

/** GET with exponential backoff and jitter on 429/5xx. Mirrors the other portal CLIs. */
export async function fetchJson(url: string, timeoutMs = 30000, maxRetries = 5): Promise<unknown> {
  let lastError: unknown
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)
    try {
      const res = await fetch(url, {
        headers: { "User-Agent": USER_AGENT, Accept: "application/json" },
        signal: controller.signal,
      })
      if (res.status === 429 || res.status >= 500) {
        throw new HttpError(res.status, `himalayas returned HTTP ${res.status}`)
      }
      if (!res.ok) {
        throw new HttpError(res.status, `himalayas returned HTTP ${res.status} for ${url}`)
      }
      return await res.json()
    } catch (err) {
      lastError = err
      const retriable =
        err instanceof HttpError ? err.status === 429 || err.status >= 500 : true
      if (!retriable || attempt === maxRetries) break
      const backoff = Math.min(2 ** attempt * 500, 8000)
      await sleep(backoff + Math.random() * 250)
    } finally {
      clearTimeout(timer)
    }
  }
  throw lastError
}

export async function fetchPage(cursor?: string | null, limit = PAGE_SIZE): Promise<FeedPage> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (cursor) params.set("cursor", cursor)
  const data = (await fetchJson(`${BASE_URL}/jobs/api?${params}`)) as FeedPage
  return { jobs: data.jobs ?? [], nextCursor: data.nextCursor ?? null, totalCount: data.totalCount }
}

/** Strip the HTML the feed puts in `description`, so a terminal shows readable text. */
export function stripHtml(html: string): string {
  return html
    .replace(/<\s*(script|style)[^>]*>[\s\S]*?<\s*\/\s*\1\s*>/gi, " ")
    .replace(/<\s*br\s*\/?\s*>/gi, "\n")
    .replace(/<\s*\/\s*(p|div|li|h[1-6]|tr)\s*>/gi, "\n")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&#39;|&rsquo;/g, "'")
    .replace(/&quot;|&rdquo;|&ldquo;/g, '"')
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
}

export function isoDate(epochSeconds: number): string {
  return new Date(epochSeconds * 1000).toISOString().slice(0, 10)
}

export function formatSalary(job: HimalayasJob): string {
  const { minSalary, maxSalary, currency, salaryPeriod } = job
  if (!minSalary && !maxSalary) return ""
  const cur = currency ?? ""
  const period = salaryPeriod && salaryPeriod !== "annual" ? `/${salaryPeriod}` : ""
  const n = (v: number) => v.toLocaleString("en-US")
  if (minSalary && maxSalary && minSalary !== maxSalary) {
    return `${cur} ${n(minSalary)}-${n(maxSalary)}${period}`.trim()
  }
  return `${cur} ${n((maxSalary ?? minSalary) as number)}${period}`.trim()
}
