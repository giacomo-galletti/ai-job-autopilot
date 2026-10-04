import { describe, expect, test } from "bun:test"
import { runSearch } from "../src/commands/search.js"
import type { FeedPage } from "../src/helpers.js"

const DAY = 86400
const now = () => Math.floor(Date.now() / 1000)

const job = (pubDate: number, title = "Frontend Engineer") =>
  ({
    title, excerpt: "", companyName: "c", companySlug: "c", employmentType: null,
    minSalary: null, maxSalary: null, salaryPeriod: null, currency: null,
    seniority: [], locationRestrictions: [], timezoneRestrictions: [],
    categories: [], parentCategories: [], description: "", pubDate, expiryDate: 0,
    applicationLink: "", guid: `g-${pubDate}-${title}`,
  }) as never

const opts = (over: Record<string, unknown> = {}) =>
  ({ timezoneTolerance: 3, pages: 3, includeDescription: false, ...over }) as never

/** A fake feed: one entry per page, each a list of pubDates, or an Error to throw. */
function feed(pages: (number[] | Error)[]) {
  let calls = 0
  const getPage = async (): Promise<FeedPage> => {
    const page = pages[calls++]
    if (page instanceof Error) throw page
    return { jobs: (page ?? []).map((d) => job(d)), nextCursor: calls < pages.length ? `c${calls}` : null } as never
  }
  return { getPage, calls: () => calls }
}

describe("runSearch coverage", () => {
  test("a page budget that runs out before --max-days-old is reported as truncated", async () => {
    const t = now()
    const { getPage } = feed([[t - 3600, t - 7200], [t - DAY, t - 2 * DAY], [t - 3 * DAY], [t - 4 * DAY]])
    const out = await runSearch(opts({ maxDaysOld: 14, pages: 2 }), getPage)
    expect(out.truncated).toBe(true)
    expect(out.scanned).toBe(4)
    expect(out.oldestScanned).toBe(new Date((t - 2 * DAY) * 1000).toISOString().slice(0, 10))
  })

  test("reaching the cutoff is full coverage, not truncation", async () => {
    const t = now()
    const { getPage, calls } = feed([[t - DAY], [t - 20 * DAY, t - 21 * DAY], [t - 22 * DAY]])
    const out = await runSearch(opts({ maxDaysOld: 14, pages: 5 }), getPage)
    expect(out.truncated).toBe(false)
    expect(out.results.length).toBe(1)
    expect(calls()).toBe(2)
  })

  test("the end of the feed is full coverage, not truncation", async () => {
    const t = now()
    const { getPage } = feed([[t - DAY]])
    const out = await runSearch(opts({ maxDaysOld: 14, pages: 5 }), getPage)
    expect(out.truncated).toBe(false)
  })

  test("a later page failing keeps what was already collected", async () => {
    const t = now()
    const { getPage } = feed([[t - DAY, t - 2 * DAY], new Error("himalayas returned HTTP 429")])
    const out = await runSearch(opts({ maxDaysOld: 14 }), getPage)
    expect(out.results.length).toBe(2)
    expect(out.truncated).toBe(true)
    expect(out.error).toContain("429")
  })

  test("a failing first page is still an error", async () => {
    const { getPage } = feed([new Error("himalayas returned HTTP 503")])
    await expect(runSearch(opts({ maxDaysOld: 14 }), getPage)).rejects.toThrow("503")
  })
})
