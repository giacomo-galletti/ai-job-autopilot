# Application Form Answer Bank

<!-- Copied from profile.example/forms.md by /onboard. Methodology for free-text fields (self
     introductions, project entries, character limits) lives in
     .claude/skills/job-application-assistant/08-application-forms.md. This file is the bank of
     the candidate's own standard answers. -->

**Check this bank before asking the candidate anything, and add every new answer the moment it is
given, with its date.** "Candidate" marks the candidate's own answer; "derived" marks an answer
read from the profile that moves to "Candidate" once confirmed. Per-application answers stay in
`profile/applications/<slug>/form_answers.json`.

## Contact and identity

- Name [FULL_NAME]; email [YOUR_EMAIL]; phone [YOUR_PHONE] (country code [CC], number [NUMBER]);
  portfolio [PORTFOLIO_URL]; LinkedIn [LINKEDIN_URL]; GitHub [GITHUB_URL].
- Location typeaheads by portal: "[CITY_AS_LINKEDIN_WANTS_IT]", "[CITY_AS_LEVER_WANTS_IT]",
  "[CITY_AS_GREENHOUSE_WANTS_IT]". Current company: [CURRENT_EMPLOYER or "self-employed"].

## Work rights, location, relocation

- **Right to work:** [COUNTRY/REGION: yes/no for each region likely to be asked].
- **Sponsorship needed:** [per country].
- **Free-text sponsorship / authorization wording:** "[ANSWER_THAT_IS_TRUE_AND_OFFERS_THE_CONTRACT_ROUTE_IF_APPLICABLE]".
- **Relocation:** [answer, matching deal-breakers.md].
- **Timezone answer:** "[TIMEZONE_WORDING]".

## Availability, pay, engagement

- **Notice period / start date:** [ANSWER].
- **Salary expectation (employment):** [AMOUNT, CURRENCY, GROSS PER PERIOD, "open upward" or not].
- **Day rate (contract):** [AMOUNT or "ask me"].
- **Currency conversions:** never convert; quote the figure in the form's currency only if the candidate gave it.
- **Employment or contract:** [ANSWER].
- **Company / vendor questions:** [ENTITY_FACTS or "none"].

## Education and languages

- **Highest qualification:** [ANSWER]. **University degree:** [yes/no]. **Graduated:** [ANSWER].
- **Languages and CEFR selectors:** [LANGUAGE: LEVEL, ...].

## Experience numbers and yes/no skills

- **Years per technology:** [TECH: N, ...]. Unknown or absent: 0.
- **Years of professional experience overall:** [N]. **Years of management / product / testing / CI:** [N each].
- **Yes/no skills confirmed by the candidate:** [SKILL: yes/no (DATE)].

## Consents and optional sections

- **Future-roles consent / newsletter:** [tick / leave unticked].
- **Data processing consent:** [tick / leave unticked].
- **Demographic / EEO questions:** [answer / "prefer not to say"].
- **"How did you hear about us?":** "[SOURCE_WORDING]".

## Channels, accounts, familiarity

- [for example "No Telegram account: a form requiring a handle blocks that role"]
- [for example "Do not create accounts on employer portals: park the role instead"]

## Answers given on [DATE]

<!-- Append dated blocks below as the candidate answers new questions. -->

- [QUESTION]: [ANSWER] ([candidate / derived], [DATE], [WHERE_ASKED])

## Portal quirks seen in real sends

<!-- Candidate-specific quirks (for example a parser that garbles this phone number). General
     portal behaviour is documented in 08-application-forms.md. -->

- [PORTAL]: [QUIRK_AND_WORKAROUND]

## Country-locked remote roles

Wording for a notes / additional information / message field when a posting is restricted to a
country the candidate does not live in (delete if the candidate has no contracting route):

> [WORDING_OFFERING_THE_CONTRACT_ROUTE_THROUGH_THE_CANDIDATE'S_ENTITY]
