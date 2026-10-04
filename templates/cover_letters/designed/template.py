"""Per-application cover letter - copy me to cover_letters/cover_<company>_<role>.py and edit.

    cp templates/cover_letters/designed/template.py cover_letters/cover_acme_frontend.py
    # write the letter
    python3 templates/cover_letters/designed/build.py cover_letters/cover_acme_frontend.py

Only the letter lives here. Name, headline and contact details come from the CV content
module, so the pair can never disagree about a phone number.

WRITING RULES (03-writing-style.md is the source of truth; this is the short version):

- No em-dashes. No "I am passionate about", "great fit", "leverage", "hit the ground running".
- Every company-specific claim must be verified independently before it goes in - not from a
  URL inside the posting, and not from a reviewer agent's say-so.
- Demonstrate, don't state: a specific project with its outcome beats an adjective.
- Three or four paragraphs. The build fails at two pages, and a long letter is not read.
- Find a named recipient. "Dear Hiring Manager" is the fallback, and the build warns about it.
- **Offer the engagement flexibility once, in the closing paragraph**, whenever the posting
  carries a country restriction or reads as payroll-constrained: you are happy to be hired as an
  employee, or to invoice through your own company (if you have one), whichever is simpler for
  them. Phrase it as a choice they get, never as a condition he attaches, and skip it entirely
  when the posting has no such obstacle. See your engagement-model notes in profile/.
"""

from datetime import date

# Point at the tailored CV for this application so the two documents share one profile.
# Leave as None to use the master content.
# CV_MODULE = "cv/main_acme_frontend.py"

COMPANY = "TODO Company"
ADDRESS = [
    "TODO Street",
    "TODO City, TODO Country",
]

# The posting's own title, so the reader sees the role they advertised.
SUBJECT = "TODO Application: Senior Frontend Engineer"

DATE = date.today().strftime("%d %B %Y")

GREETING = "Dear TODO,"

# Each entry is a paragraph. A nested list becomes a short bulleted run - useful when the
# posting lists requirements and the answer is genuinely a list, but prose is the default.
PARAGRAPHS = [
    "TODO opening: why this company, specifically, and what you bring in one sentence. No preamble.",
    "TODO evidence: the single most relevant thing built, with what it did and for whom.",
    "TODO fit: connect the profile to the posting's actual work. Name the gap if there is one.",
    # Close. Where the posting reads as employment or names a country, the engagement model goes
    # in here as one plain sentence, before the offer to talk.
    "TODO close: what you want next and a plain offer to talk.",
]

CLOSING = "Best regards,"
