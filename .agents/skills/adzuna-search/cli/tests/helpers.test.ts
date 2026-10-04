// Unit tests for pure logic (no network). Run with: node --test
import { test } from "node:test"
import assert from "node:assert/strict"
import {
  rankBySalary,
  salarySignal,
  formatSalary,
  buildSearchUrl,
  DEFAULT_COUNTRIES,
  type JobCard,
} from "../src/helpers.ts"
import { resolveCountries } from "../src/commands/search.ts"

function job(partial: Partial<JobCard>): JobCard {
  return {
    id: "1",
    title: "Engineer",
    company: "Acme",
    location: "Remote",
    country: "us",
    date: "2026-06-01",
    url: "https://example.com",
    salaryMin: null,
    salaryMax: null,
    salaryPredicted: false,
    currency: "USD",
    contractType: null,
    contractTime: null,
    category: null,
    description: null,
    ...partial,
  }
}

test("salarySignal prefers max, falls back to min, then -1", () => {
  assert.equal(salarySignal(job({ salaryMin: 100, salaryMax: 200 })), 200)
  assert.equal(salarySignal(job({ salaryMin: 100, salaryMax: null })), 100)
  assert.equal(salarySignal(job({ salaryMin: null, salaryMax: null })), -1)
})

test("rankBySalary sorts desc and pushes unknown-salary jobs last, stably", () => {
  const jobs = [
    job({ id: "a", salaryMax: 100 }),
    job({ id: "b", salaryMax: null }),
    job({ id: "c", salaryMax: 300 }),
    job({ id: "d", salaryMax: null }),
  ]
  const ranked = rankBySalary(jobs).map((j) => j.id)
  assert.deepEqual(ranked, ["c", "a", "b", "d"]) // b before d = stable
})

test("formatSalary renders ranges, single values, est. flag, and em dash", () => {
  assert.equal(formatSalary(job({ salaryMin: null, salaryMax: null })), "—")
  assert.equal(formatSalary(job({ salaryMin: 80000, salaryMax: 120000 })), "USD 80,000–USD 120,000")
  assert.equal(formatSalary(job({ salaryMin: 90000, salaryMax: 90000 })), "USD 90,000")
  assert.equal(
    formatSalary(job({ salaryMin: 50000, salaryMax: 60000, salaryPredicted: true })),
    "USD 50,000–USD 60,000 (est.)",
  )
})

test("buildSearchUrl includes credentials, query, and options", () => {
  const url = buildSearchUrl(
    { appId: "ID", appKey: "KEY" },
    { country: "de", query: "data engineer", page: 2, resultsPerPage: 30, maxDaysOld: 7, sortBy: "salary" },
  )
  assert.match(url, /\/jobs\/de\/search\/2\?/)
  assert.match(url, /app_id=ID/)
  assert.match(url, /app_key=KEY/)
  assert.match(url, /what=data\+engineer/)
  assert.match(url, /max_days_old=7/)
  assert.match(url, /sort_by=salary/)
})

test("buildSearchUrl omits sort_by when default", () => {
  const url = buildSearchUrl({ appId: "i", appKey: "k" }, { country: "us", sortBy: "default" })
  assert.doesNotMatch(url, /sort_by=/)
})

test("resolveCountries defaults when empty and validates codes", () => {
  assert.deepEqual(resolveCountries([]), DEFAULT_COUNTRIES)
  assert.deepEqual(resolveCountries(["US", "gb", "us"]), ["us", "gb"]) // lowercased + deduped
  assert.throws(() => resolveCountries(["zz"]), /Unsupported country code/)
})
