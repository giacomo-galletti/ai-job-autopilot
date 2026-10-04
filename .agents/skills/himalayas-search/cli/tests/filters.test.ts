import { describe, expect, test } from "bun:test"
import { hireableFrom, timezoneOverlaps } from "../src/commands/search.js"
import { formatSalary, isoDate, stripHtml } from "../src/helpers.js"

const job = (over: Record<string, unknown> = {}) =>
  ({
    title: "t", excerpt: "", companyName: "c", companySlug: "c", employmentType: null,
    minSalary: null, maxSalary: null, salaryPeriod: null, currency: null,
    seniority: [], locationRestrictions: [], timezoneRestrictions: [],
    categories: [], parentCategories: [], description: "", pubDate: 0, expiryDate: 0,
    applicationLink: "", guid: "", ...over,
  }) as never

describe("hireableFrom", () => {
  test("an empty restriction list means worldwide, which anyone can take", () => {
    expect(hireableFrom(job(), "Italy")).toBe(true)
  })

  test("a country-locked posting is excluded, not surfaced for later rejection", () => {
    expect(hireableFrom(job({ locationRestrictions: ["United States"] }), "Italy")).toBe(false)
    expect(hireableFrom(job({ locationRestrictions: ["Philippines"] }), "Italy")).toBe(false)
  })

  test("Italy accepts Europe-wide and EU-wide postings, not just its own name", () => {
    for (const region of ["Europe", "European Union", "EMEA", "EEA"]) {
      expect(hireableFrom(job({ locationRestrictions: [region] }), "Italy")).toBe(true)
    }
    expect(hireableFrom(job({ locationRestrictions: ["Italy"] }), "Italy")).toBe(true)
  })

  test("one qualifying entry in a mixed list is enough", () => {
    expect(hireableFrom(job({ locationRestrictions: ["Canada", "Europe"] }), "Italy")).toBe(true)
  })
})

describe("timezoneOverlaps", () => {
  test("no stated timezone means any timezone", () => {
    expect(timezoneOverlaps(job(), 2, 3)).toBe(true)
  })

  test("tolerance is inclusive at its edge", () => {
    expect(timezoneOverlaps(job({ timezoneRestrictions: [5] }), 2, 3)).toBe(true)
    expect(timezoneOverlaps(job({ timezoneRestrictions: [6] }), 2, 3)).toBe(false)
  })

  test("a US-Pacific-only posting is out of reach from CET", () => {
    expect(timezoneOverlaps(job({ timezoneRestrictions: [-8] }), 2, 3)).toBe(false)
  })
})

describe("formatting", () => {
  test("salary renders a range, a single figure, or nothing at all", () => {
    expect(formatSalary(job({ minSalary: 90000, maxSalary: 120000, currency: "USD" }))).toBe("USD 90,000-120,000")
    expect(formatSalary(job({ minSalary: 90000, maxSalary: 90000, currency: "EUR" }))).toBe("EUR 90,000")
    expect(formatSalary(job())).toBe("")
  })

  test("a non-annual period is named so a monthly figure is not read as a salary", () => {
    expect(formatSalary(job({ minSalary: 3500, maxSalary: 9500, currency: "USD", salaryPeriod: "month" })))
      .toBe("USD 3,500-9,500/month")
  })

  test("stripHtml leaves readable text, not tags or entities", () => {
    expect(stripHtml("<p>Hello<br/>world</p><script>bad()</script>")).toBe("Hello\nworld")
    expect(stripHtml("R&amp;D &lt;team&gt;")).toBe("R&D <team>")
  })

  test("isoDate converts the feed's epoch seconds", () => {
    expect(isoDate(1789719857)).toBe("2026-09-18")
  })
})
