# profile.example/

Placeholder templates for the private `profile/` folder. Everything here is committed and
contains **placeholders only** (`[FULL_NAME]`, `[YOUR_EMAIL]`, ...). Never put real data in this
folder.

`/onboard` copies these files to `profile/` (which is gitignored) and fills them in from your CV,
LinkedIn export or an interview. All tracked framework files (CLAUDE.md, AGENTS.md, the skills,
the commands, the agents) read the candidate's facts from `profile/`, never from here.

| File | Holds |
|------|-------|
| `profile.md` | Identity, languages, education, experience, projects, skills, metrics, engagement model, compensation |
| `behavioral.md` | Self-assessed behavioral profile and posting-language mapping |
| `deal-breakers.md` | Hard no's, location rules, apply gates, country exceptions, standing routine rules |
| `forms.md` | Answer bank for screening and application-form questions, plus portal quirks you have met |
| `portals.md` | Which job boards are enabled for this candidate, and why |
| `search-queries.md` | Role families, titles, synonyms, exclusions used by `/scrape` |

Also in `profile/`, created by `/onboard` or by the commands (no template here): `cv_content.py`, the
candidate's master CV content that the CV and cover letter modules import; `applications/<slug>/`,
one folder per application (posting archive, form answers, prep packs); and `tracker.csv`, the application tracker.
