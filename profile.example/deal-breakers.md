# Deal-breakers, Gates and Standing Rules

<!-- Copied from profile.example/deal-breakers.md by /onboard. Every rule here is the
     candidate's own, with the date they gave it. Framework files (04-job-evaluation.md,
     /apply, /scrape, /rank, the scout agents) read this file; nothing is hardcoded elsewhere.
     Delete rules that do not apply; add the candidate's own. -->

## Work mode and location

- **Preferred:** [remote / hybrid / on-site]. Ranks first.
- **Accepted:** [for example "hybrid within commuting distance of <city>"]. Ranks below an equivalent preferred role.
- **Commutable places:** [LIST_OF_CITIES_OR_RADIUS - for example "<city A>, <city B>"; anything farther counts as relocation].
- **Hard no:** [for example "fully on-site and relocation-required roles"].
- **Exceptions (user-defined, dated):**
  - [EXCEPTION_1 - for example "relocation to <country> is acceptable if the stated salary is at least <amount> and the role makes sense; if no salary is stated, apply" ([DATE])]

## Roles and environments that are a no

- [for example "maintenance-only or legacy-only work with no ownership"]
- [for example "approval-heavy or micromanaged environments"]
- [for example "unpaid test projects beyond a few hours"]

## Pay

- **Floor:** [FLOOR_AMOUNT_AND_CURRENCY_PER_PERIOD, or "none: ranking signal only"]. Applies to [employment / contract / both].
- A stated salary below the floor: [skip / flag]. No stated salary: [apply / ask].

## Engagement

- **Employment:** [open / not open]. **Contract or B2B:** [open through <ENTITY> / not open].
- Offering both is [a selling point / not applicable].

## Country-restricted remote roles

A "remote, <country> only" lock means one of four things. Classify it, then follow the candidate's
choice below. (Delete this section if the candidate has no contracting route.)

1. **Payroll**: the employer can only put employees on a local payroll. [Pursue / offer the vendor route / skip]
2. **Timezone**: local working-hours overlap. [Judge case by case against the candidate's timezone]
3. **Legal or contractual**: data residency, clearance, regulated industry, government client, procurement that will not onboard a one-person vendor. **Does not bend.**
4. **Rate arbitrage**: the employer targets a lower-cost market on purpose. [Drop at search time with `tools/low_cost_markets.py` / keep]

Default for a country lock without a case-3 reason: [apply and offer the contracting route in the form's notes field / skip].

## Apply gates (standing routine)

The apply cycle (discover -> evaluate -> apply -> clean up) runs without asking per role when:

- the overall fit verdict in `04-job-evaluation.md` is at least **[GATE_SCORE, for example 60 / Good Fit]**, or
- the role is covered by a standing rule below.

Anything weaker is drafted and left `status=drafted` in the tracker for the candidate to review.
Nothing is auto-submitted unattended unless the candidate has said so here:

- **Auto-submit allowed:** [yes / no]. Scope: [for example "roles from job-alert emails and roles that clear the fit gate"].
- **Standing rules:**
  - [for example "apply to every role in a job-alert email" ([DATE])]
  - [for example "apply to country-locked remote roles and offer invoicing" ([DATE])]

## Never auto-submit

- [for example "forms that require essays written in the applicant's own words with an AI-use ban"]
- [for example "forms with a truthful-answer gap, such as a location field with no honest option"]

## Housekeeping rules

- Close the browser tab of an application once it is sent; trash its confirmation email only after logging the application.
- After a cycle, run `/mail-cleanup` as the last step.
- [OTHER_USER_RULES]
