---
framework_version: 2.0.0
---

# Candidate Profile (pointer)

The candidate's facts are personal data and live in the gitignored `profile/` folder, not in this
tracked file:

| Need | File |
|------|------|
| Identity, languages, education, experience, projects, skills, metrics, engagement model, compensation, evaluation inputs | `profile/profile.md` |
| Behavioral assessment | `profile/behavioral.md` |
| Hard no's, location rules, apply gates, country rules, standing routine | `profile/deal-breakers.md` |
| Standard form answers and portal quirks | `profile/forms.md` |
| Master CV content used by the CV and cover letter templates | `profile/cv_content.py` |
| Enabled job boards and search queries | `profile/portals.md`, `profile/search-queries.md` |

Placeholder templates for all of these are in `profile.example/` (tracked, placeholders only).

**If `profile/` does not exist, stop and run `/onboard`** before evaluating, drafting or applying.

## Rules for using the profile

- Every claim in a CV, cover letter, form field or email must trace to `profile/profile.md` or
  `profile/cv_content.py`. Never invent or stretch a fact, skill, metric, date or title.
- When the candidate confirms, corrects or supplies a fact, write it back to `profile/profile.md`
  (or the answer to `profile/forms.md`) in the same turn, with the date.
- Metrics marked off-limits in the profile stay off every document. Where the profile says no
  statistics exist, write around the absence; do not estimate.
- Tailor substantially per posting, but preserve actual employers, historical titles, dates,
  ownership and metrics.
- When mentioning agentic coding or AI tooling, name the specific tool the profile lists.
