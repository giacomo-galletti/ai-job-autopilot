"""Per-application CV content - copy me to cv/main_<company>_<role>.py and edit.

    cp templates/cv/designed/template.py cv/main_acme_frontend.py
    # edit the overrides below
    python3 templates/cv/designed/build.py cv/main_acme_frontend.py

The base content is your `profile/cv_content.py` when it exists, otherwise the fictional
example in content_example.py. This file overrides only what one posting needs on top.
Delete any override you do not use - one left at its default value is noise for the next reader.

**Presets are optional and written for the example content.** The four role-family presets
(product_frontend, design_engineer, product_designer, ai_product) replace HEADLINE, PROFILE,
SKILLS and the sentence order with example text that names the example companies. Import one
only to see the pattern; with your own content, copy the pattern and write your own wording.

TAILORING RULES (see .claude/skills/job-application-assistant/03-writing-style.md and
05-cv-templates.md - these are the short version, that file wins on conflict):

- **Reorder and re-emphasise. Never invent.** Every claim must already be true in your
  profile content. The /apply Factual Grounding Audit strips anything that is not.
- **The interview backtrack test.** If a reworded bullet would make you say "well, what I
  actually meant was..." in an interview, it has gone too far.
- **Lead with what the posting asks for.** Rewrite summary and bullets, select relevant
  projects, and tailor skill lists to the specific requirements.
- **Use a real number wherever one exists.** Never invent one.
- **Keep the page budget.** The ATS resume is at most 2 pages, the designed one exactly 1.
  The build fails if you overrun, so cut rather than shrink.
- **The ATS resume is what gets sent.** `ATS_SKILLS_LEFT` / `ATS_SKILLS_RIGHT` are the list a
  parser scores, so they deserve the tailoring attention. `SKILLS` only affects the designed
  variant's sidebar.
"""

from content_base import *  # noqa: F401,F403
from presets._shared import reorder, skills  # noqa: F401  (for the overrides below)

# Optional: start from a role-family preset instead (example content only, see above).
# from presets.product_frontend import *  # noqa: F401,F403

# --- the role this file targets -------------------------------------------------------
# Kept as data so a later reader (and /outcome) can tell what this CV was aimed at.
TARGET = {
    "company": "TODO",
    "role": "TODO",
    "url": "TODO",
    "tailored": "2026-01-01",
}

# --- profile paragraph ----------------------------------------------------------------
# The single highest-leverage edit: same facts, aimed at this posting. Keep it to the
# base profile's length (about 5 sentences) or the designed CV grows past one page.
# PROFILE = (
#     "Product engineer with 10+ years ..."
# )

# --- headline -------------------------------------------------------------------------
# Match the posting's own title where that is honest: "Product Engineer - UI/UX, Front-end
# & AI" becomes "Front-end Engineer - Vue, Design Systems & AI" for a Vue-heavy role.
# HEADLINE = "Product Engineer · UI/UX, Front-end & AI"

# --- skills ---------------------------------------------------------------------------
# Override to push one group up for this posting.
# Order here is the sidebar order in the designed CV; an unnamed group is dropped.
# SKILLS = skills("Development", "Design", "Artificial Intelligence", "Product & Business", "Tools")

# The ATS resume's two-column list. This is the one a parser reads, so it carries the most
# weight: put the posting's own terms here wherever they are honestly true of the profile.
# ATS_SKILLS_LEFT = [...]
# ATS_SKILLS_RIGHT = [...]

# --- experience -----------------------------------------------------------------------
# Override a single job when the posting
# wants something specific at the top. Rewriting a sentence is allowed; inventing one is not.
#
# JOBS = reorder({"Example Co": [
#     "Develop the front end in Vue.js across the conversation player, scenario editor and dashboards.",
#     "Lead UI design for an AI platform where people practise high-stakes workplace conversations through realistic simulations.",
#     "Build the design-system foundations, connected to Figma, and the Nuxt marketing site in three languages.",
# ]})

# --- project cards --------------------------------------------------------------------
# The designed CV shows the two PROJECTS entries that carry a `card`. Swap which two, or
# retitle a card's description toward the posting, by overriding PROJECTS.
