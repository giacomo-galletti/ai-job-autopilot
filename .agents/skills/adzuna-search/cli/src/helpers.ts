// Adzuna API client + shared types/formatters for the adzuna-search CLI.
// Zero-dependency: uses only web-standard fetch + Node/Bun globals so it runs
// under both `node <file>.ts` (Node >= 23 strips types) and `bun run`.

import fs from "node:fs"
import path from "node:path"

export const BASE_URL = "https://api.adzuna.com/v1/api/jobs"

// Adzuna country codes that are supported. The repo's default focus is the
// high-paying EU + Americas + Oceania subset, but any of these may be queried.
export const SUPPORTED_COUNTRIES = [
  "gb", "us", "at", "au", "br", "ca", "de", "es",
  "fr", "in", "it", "mx", "nl", "nz", "pl", "sg", "za",
] as const

export type Country = (typeof SUPPORTED_COUNTRIES)[number]

// Default countries searched when none are specified (see design doc).
export const DEFAULT_COUNTRIES: Country[] = [
  "us", "gb", "de", "nl", "ca", "fr", "it", "at", "es", "au", "nz",
]

// ISO 4217 currency shown per country (Adzuna returns salaries in local currency).
export const COUNTRY_CURRENCY: Record<string, string> = {
  gb: "GBP", us: "USD", at: "EUR", au: "AUD", br: "BRL", ca: "CAD",
  de: "EUR", es: "EUR", fr: "EUR", in: "INR", it: "EUR", mx: "MXN",
  nl: "EUR", nz: "NZD", pl: "PLN", sg: "SGD", za: "ZAR",
}

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

let dotenvLoaded = false
/**
 * Minimal, dependency-free .env loader. Walks up from the current directory to
 * find the nearest `.env` and populates process.env for keys not already set
 * (real environment / shell vars always win). Bun auto-loads .env, so this is a
 * no-op safety net there; it's what makes `node src/cli.ts` work without
 * `--env-file`. Best-effort: any read/parse error is silently ignored.
 */
export function loadDotEnv(): void {
  if (dotenvLoaded) return
  dotenvLoaded = true
  try {
    let dir = process.cwd()
    for (let i = 0; i < 8; i++) {
      const candidate = path.join(dir, ".env")
      if (fs.existsSync(candidate)) {
        const content = fs.readFileSync(candidate, "utf8")
        for (const line of content.split("\n")) {
          const trimmed = line.trim()
          if (!trimmed || trimmed.startsWith("#")) continue
          const eq = trimmed.indexOf("=")
          if (eq === -1) continue
          const key = trimmed.slice(0, eq).trim()
          let val = trimmed.slice(eq + 1).trim()
          if (
            (val.startsWith('"') && val.endsWith('"')) ||
            (val.startsWith("'") && val.endsWith("'"))
          ) {
            val = val.slice(1, -1)
          }
          if (key && process.env[key] === undefined) process.env[key] = val
        }
        return
      }
      const parent = path.dirname(dir)
      if (parent === dir) break
      dir = parent
    }
  } catch {
    // best-effort; getCredentials() will report MISSING_CREDENTIALS if needed
  }
}

export class AdzunaError extends Error {
  code: string
  constructor(message: string, code: string) {
    super(message)
    this.code = code
  }
}

export interface Credentials {
  appId: string
  appKey: string
}

/** Read Adzuna credentials from the environment. Throws AdzunaError if missing. */
export function getCredentials(): Credentials {
  loadDotEnv()
  const appId = process.env.ADZUNA_APP_ID?.trim()
  const appKey = process.env.ADZUNA_APP_KEY?.trim()
  if (!appId || !appKey) {
    throw new AdzunaError(
      "Missing Adzuna credentials. Set ADZUNA_APP_ID and ADZUNA_APP_KEY " +
        "(get a free key at https://developer.adzuna.com). They are read from " +
        "the environment / .env — never pass them on the command line.",
      "MISSING_CREDENTIALS",
    )
  }
  return { appId, appKey }
}

// ---- Adzuna API response shapes (only the fields we use) ----

interface RawCompany {
  display_name?: string
}
interface RawLocation {
  display_name?: string
  area?: string[]
}
interface RawCategory {
  label?: string
}
interface RawAdzunaJob {
  id?: string
  title?: string
  company?: RawCompany
  location?: RawLocation
  created?: string
  redirect_url?: string
  description?: string
  salary_min?: number
  salary_max?: number
  salary_is_predicted?: string | number | boolean
  contract_type?: string
  contract_time?: string
  category?: RawCategory
}
interface RawSearchResponse {
  results?: RawAdzunaJob[]
  count?: number
  mean?: number
}

// ---- Normalized shapes the CLI emits ----

export interface JobCard {
  id: string
  title: string
  company: string | null
  location: string | null
  country: string
  date: string | null
  url: string
  salaryMin: number | null
  salaryMax: number | null
  salaryPredicted: boolean
  currency: string
  contractType: string | null
  contractTime: string | null
  category: string | null
  description: string | null
}

function stripTags(html: string): string {
  return html.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim()
}

function toBool(v: unknown): boolean {
  return v === true || v === 1 || v === "1"
}

function normalizeJob(raw: RawAdzunaJob, country: string): JobCard {
  return {
    id: String(raw.id ?? ""),
    title: raw.title ? stripTags(raw.title) : "(untitled)",
    company: raw.company?.display_name?.trim() || null,
    location: raw.location?.display_name?.trim() || null,
    country,
    date: raw.created ?? null,
    url: raw.redirect_url ?? "",
    salaryMin: typeof raw.salary_min === "number" ? raw.salary_min : null,
    salaryMax: typeof raw.salary_max === "number" ? raw.salary_max : null,
    salaryPredicted: toBool(raw.salary_is_predicted),
    currency: COUNTRY_CURRENCY[country] ?? "",
    contractType: raw.contract_type ?? null,
    contractTime: raw.contract_time ?? null,
    category: raw.category?.label ?? null,
    description: raw.description ? stripTags(raw.description) : null,
  }
}

export interface SearchParams {
  country: string
  query?: string
  page?: number
  resultsPerPage?: number
  maxDaysOld?: number
  sortBy?: "salary" | "date" | "relevance" | "default"
  /**
   * Adzuna's contract_type facet. "contract" is the one that matters for a candidate who
   * engages as a business: it narrows to the postings already written as engagements rather
   * than employment, where the invoicing question never has to be raised.
   */
  contractType?: "contract" | "permanent"
}

export interface SearchResult {
  country: string
  jobs: JobCard[]
  count: number
  mean: number | null
}

/** GET with retry/backoff on 429 + 5xx. Deterministic (no random jitter). */
async function fetchJson<T>(url: string): Promise<T> {
  const maxRetries = 5
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    let response: Response
    try {
      response = await fetch(url)
    } catch (err) {
      if (attempt === maxRetries) {
        throw new AdzunaError(
          `Network error contacting Adzuna: ${(err as Error).message}`,
          "NETWORK_ERROR",
        )
      }
      await sleep(delay)
      delay = Math.min(delay * 2, 5000)
      continue
    }
    if (response.status === 429 || response.status >= 500) {
      if (attempt === maxRetries) {
        throw new AdzunaError(
          `Adzuna API failed: ${response.status} ${response.statusText}`,
          "API_ERROR",
        )
      }
      await sleep(delay)
      delay = Math.min(delay * 2, 5000)
      continue
    }
    if (response.status === 401 || response.status === 403) {
      throw new AdzunaError(
        "Adzuna rejected the credentials (401/403). Check ADZUNA_APP_ID / ADZUNA_APP_KEY.",
        "AUTH_ERROR",
      )
    }
    if (!response.ok) {
      throw new AdzunaError(
        `Adzuna API failed: ${response.status} ${response.statusText}`,
        "API_ERROR",
      )
    }
    return response.json() as Promise<T>
  }
  throw new AdzunaError("Adzuna API failed after max retries", "API_ERROR")
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** Build the Adzuna search URL (credentials included as query params per the API spec). */
export function buildSearchUrl(creds: Credentials, p: SearchParams): string {
  const page = p.page && p.page > 0 ? p.page : 1
  const qs = new URLSearchParams({
    app_id: creds.appId,
    app_key: creds.appKey,
    "content-type": "application/json",
    results_per_page: String(p.resultsPerPage ?? 20),
  })
  if (p.query) qs.set("what", p.query)
  if (p.maxDaysOld && p.maxDaysOld > 0) qs.set("max_days_old", String(p.maxDaysOld))
  if (p.sortBy && p.sortBy !== "default") qs.set("sort_by", p.sortBy)
  // The API takes these as separate boolean flags, not as one field with a value.
  if (p.contractType === "contract") qs.set("contract", "1")
  if (p.contractType === "permanent") qs.set("permanent", "1")
  return `${BASE_URL}/${p.country}/search/${page}?${qs.toString()}`
}

/** Execute one country search. */
export async function searchJobs(creds: Credentials, p: SearchParams): Promise<SearchResult> {
  const url = buildSearchUrl(creds, p)
  const data = await fetchJson<RawSearchResponse>(url)
  const jobs = (data.results ?? []).map((r) => normalizeJob(r, p.country))
  return {
    country: p.country,
    jobs,
    count: typeof data.count === "number" ? data.count : jobs.length,
    mean: typeof data.mean === "number" ? data.mean : null,
  }
}

/**
 * Best-effort full text for a single job. Adzuna's free API has no get-by-id
 * endpoint, so `detail` fetches the job's public redirect URL and strips tags.
 * The employer page format varies, so this is best-effort, not guaranteed.
 */
export async function fetchDetailText(url: string): Promise<string> {
  const response = await fetch(url, {
    headers: {
      "User-Agent": "Mozilla/5.0 (compatible; adzuna-search-cli/1.0)",
      Accept: "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    },
    redirect: "follow",
  })
  if (!response.ok) {
    throw new AdzunaError(
      `Could not fetch job page: ${response.status} ${response.statusText}`,
      "DETAIL_ERROR",
    )
  }
  const html = await response.text()
  const body = html.replace(/<script[\s\S]*?<\/script>/gi, "").replace(/<style[\s\S]*?<\/style>/gi, "")
  return stripTags(body).slice(0, 8000)
}

// ---- Ranking + formatting ----

/** A single comparable salary signal for ranking (max preferred, else min). */
export function salarySignal(job: JobCard): number {
  if (job.salaryMax != null) return job.salaryMax
  if (job.salaryMin != null) return job.salaryMin
  return -1 // unknown salary sorts last
}

/** Sort jobs by salary descending; unknown-salary jobs go last (stable). */
export function rankBySalary(jobs: JobCard[]): JobCard[] {
  return [...jobs]
    .map((job, i) => ({ job, i }))
    .sort((a, b) => {
      const d = salarySignal(b.job) - salarySignal(a.job)
      return d !== 0 ? d : a.i - b.i
    })
    .map((x) => x.job)
}

export function formatSalary(job: JobCard): string {
  const { salaryMin, salaryMax, currency, salaryPredicted } = job
  if (salaryMin == null && salaryMax == null) return "—"
  const fmt = (n: number) => `${currency} ${Math.round(n).toLocaleString("en-US")}`
  let s: string
  if (salaryMin != null && salaryMax != null && salaryMin !== salaryMax) {
    s = `${fmt(salaryMin)}–${fmt(salaryMax)}`
  } else {
    s = fmt(salaryMax ?? salaryMin!)
  }
  return salaryPredicted ? `${s} (est.)` : s
}

export function truncate(s: string | null, n: number): string {
  if (!s) return ""
  return s.length > n ? s.slice(0, n - 1) + "…" : s
}

export function formatTable(jobs: JobCard[]): string {
  if (jobs.length === 0) return "No jobs found."
  const rows = jobs.map((j, i) => {
    const cols = [
      String(i + 1),
      j.country.toUpperCase(),
      truncate(j.title, 40),
      truncate(j.company ?? "—", 24),
      truncate(j.location ?? "—", 22),
      formatSalary(j),
      j.date ? j.date.slice(0, 10) : "—",
    ]
    return cols.join(" | ")
  })
  const header = "# | CO | Title | Company | Location | Salary | Date"
  return [header, "-".repeat(header.length), ...rows].join("\n")
}

export function formatPlain(job: JobCard): string {
  const lines = [
    job.title,
    `Company:  ${job.company ?? "—"}`,
    `Location: ${job.location ?? "—"} (${job.country.toUpperCase()})`,
    `Salary:   ${formatSalary(job)}`,
    `Type:     ${[job.contractType, job.contractTime].filter(Boolean).join(", ") || "—"}`,
    `Category: ${job.category ?? "—"}`,
    `Posted:   ${job.date ? job.date.slice(0, 10) : "—"}`,
    `Apply:    ${job.url}`,
    "",
    job.description ?? "(no description)",
  ]
  return lines.join("\n")
}
