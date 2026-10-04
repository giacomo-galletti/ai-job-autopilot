# Search Queries

<!-- Copied from profile.example/search-queries.md by /onboard and filled from the candidate's
     profile. /scrape reads this file together with profile/portals.md and profile/deal-breakers.md.
     The generic method (portal CLI recipes format, WebSearch fallback, scoring hints) lives in
     .claude/skills/job-scraper/search-queries.md. -->

## Scope

- **Location:** [WHERE_THE_CANDIDATE_CAN_WORK - for example "remote worldwide" or "remote + hybrid in <city>"].
  Remote ranks first, hybrid within commuting range second; the hard limits are in `deal-breakers.md`.
- **Engagement:** [employment only / contract only / either, employer's choice].
- **Hard exclusions at search time:** [FROM_deal-breakers.md - on-site, relocation, low-cost markets, legal blocks].
- **Timezone:** [HOME_TIMEZONE]. Sustained overlap demands outside it are flagged, not dropped (unless deal-breakers.md says otherwise).
- **Languages:** [WORKING_LANGUAGES]. Postings needing a language not declared in `profile.md` are excluded by the Language Gate in `04-job-evaluation.md`.

## Per-portal recipes

One block per enabled portal in `portals.md`, using that portal CLI's real flags (read its SKILL.md).

```
bun run .agents/skills/[portal-skill]/cli/src/cli.ts search -q "[TITLE_OR_KEYWORDS]" --limit 20 --format json
```

## Query Categories

Organised by **function**, not job title. Run Priorities 1-N by default; `broad` runs all of them.

### Priority 1: [FUNCTION_NAME]

[WHY_THIS_FUNCTION_FITS_THE_PROFILE]

Title variants: [TITLE_1], [TITLE_2], [TITLE_3].

```
site:linkedin.com/jobs "[TITLE]" [remote or city]
"[TITLE]" "[KEY_SKILL]" -[EXCLUDED_WORD]
```

**Note:** [TITLES_THAT_LOOK_RIGHT_BUT_ARE_NOT - for example same title in another industry].

### Priority 2: [FUNCTION_NAME]

[REPEAT_AS_NEEDED]

## Candidate-specific scoring hints

Rank up when the posting mentions: [SIGNALS_THAT_MATCH].
Rank down (but keep) when: [SIGNALS_THAT_FIT_WORSE].
Drop before presenting: [DEAL-BREAKER_SIGNALS - mirrors deal-breakers.md].
