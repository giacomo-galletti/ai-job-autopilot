# Adzuna API Reference

Official docs: <https://developer.adzuna.com/docs/search>

## Base

```
https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
```

- `{country}` — two-letter Adzuna code (see below)
- `{page}` — 1-indexed page number

## Required query params

| Param | Value |
|-------|-------|
| `app_id` | Your Adzuna application ID |
| `app_key` | Your Adzuna application key |
| `content-type` | `application/json` |

## Common optional params

| Param | Meaning |
|-------|---------|
| `what` | Keyword query (role, skill, company) |
| `results_per_page` | Page size (max 50) |
| `max_days_old` | Only jobs newer than N days |
| `sort_by` | `salary` \| `date` \| `relevance` \| `default` |
| `where` | Location string (not used by this CLI; queries are keyword-based) |

## Supported countries

`gb` (UK), `us`, `at` (Austria), `au` (Australia), `br` (Brazil), `ca` (Canada),
`de` (Germany), `es` (Spain), `fr` (France), `in` (India), `it` (Italy),
`mx` (Mexico), `nl` (Netherlands), `nz` (New Zealand), `pl` (Poland),
`sg` (Singapore), `za` (S. Africa).

**Default focus set** (high-paying EU + Americas + Oceania):
`us, gb, de, nl, ca, fr, it, at, es, au, nz`.

## Response shape (fields used)

```jsonc
{
  "count": 18903,          // total matches
  "mean": 72000,           // mean salary for the query
  "results": [
    {
      "id": "1234567890",
      "title": "Senior Data Engineer",
      "company": { "display_name": "Acme Corp" },
      "location": { "display_name": "London, UK", "area": ["UK", "London"] },
      "created": "2026-05-30T09:00:00Z",
      "redirect_url": "https://www.adzuna.com/land/ad/1234567890",
      "description": "We are looking for ...",
      "salary_min": 80000,
      "salary_max": 110000,
      "salary_is_predicted": "0",
      "contract_type": "permanent",
      "contract_time": "full_time",
      "category": { "label": "IT Jobs" }
    }
  ]
}
```

## Rate limits

The free tier allows a limited number of calls/month. The CLI retries on `429`
and `5xx` with exponential backoff. Each country in a multi-country search is one
API call, so a default 11-country run = 11 calls per page.

## Notes

- Salaries are in the country's local currency.
- There is **no get-by-id endpoint** on the free tier; full job text comes from
  fetching `redirect_url` (see the CLI `detail` command).
- `where` filtering is unreliable across countries; this CLI keeps location in the
  keyword query instead when needed (e.g. `--query "engineer amsterdam"`).
