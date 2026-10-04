---
framework_version: 1.0.1
---

# Application Form Fields

`/apply` produces two artifacts: a CV and a cover letter. Many applications need a **third** - free-text fields typed directly into an application portal. Graduate programs, large-employer ATS systems and startup forms routinely ask for things neither document covers, under a character or word limit, in a box with no formatting.

This file governs that third artifact. It is not a document you compile; it is text the candidate pastes.

For browser filling/submission, follow `.claude/commands/submit.md` and also save the exact
final field values as `form_answers.json`. The plain-text draft format below is for human
review; its labels, alternatives and NOTE TO SELF blocks must never be pasted as answers.

## Standard screening answers

The answer bank is personal and lives in `profile/forms.md` (template: `profile.example/forms.md`).
**Check it before asking the candidate anything, and add every new answer the moment it is given**,
with its date. Per-application answers stay in `profile/applications/<slug>/form_answers.json`.
If `profile/` is missing, run `/onboard`.

### Portal quirks (generic; candidate-specific ones go in `profile/forms.md`)

- **LinkedIn Easy Apply** keeps every past upload under the same file name, so the list can't tell
  them apart. Always upload the application's snapshot fresh; the new file lands on top and is selected, and a
  "Resume uploaded successfully" toast confirms it. The review page pre-ticks "Follow <company>": untick it.
- **Breezy**: the resume parser fills the optional Work History and Education sections with errors (end
  dates on current roles, a blank company, a school invented from the exchange-semester sentence, the diploma
  missing). Delete the parsed entries and let the CV carry the history. A honeypot field (`hp_*`) must stay empty.
- **Rippling**: the resume parser can garble the phone number; retype it with its country code.
  A Transcend cookie banner blocks dropdown clicks until "Reject all" is clicked by position.
- **Revolut People** and **Lever** both raised picture CAPTCHAs on submit; park those.
- **BambooHR** (DOOR3): "Desired Pay" is required; for a contract that means a day rate, so ask. A honeypot field
  ("Please leave this field blank") must stay empty.

- **SmartRecruiters "Message to the Hiring Team"**: the box rejects semicolons ("This
  field cannot contain following characters: ;"). Paste a letter with full stops in their place.
- **Personio's own careers form**: "Preferred Work Location*" is a custom multi-select that looks
  like a plain label and exposes no input until clicked. It is required. Options were Amsterdam,
  Berlin, Dublin, London, Madrid, Munich, Remote; pick the candidate's real mode only. Its salary
  field is optional: leave it blank when no band is published and the role is senior (don't anchor
  at the default from `profile/forms.md` there).
- **Personio forms hosted for other companies** (`<company>.jobs.personio.com`)
  can make salary required as free text ("gross per year in EUR"). With no band published and a
  non-senior title, type the default salary wording from `profile/forms.md`. The CV and
  "Other" uploads are optional; when the page asks for "a brief cover letter", upload one as "Other".
- **Joinrs** (joinrs.com): "Sign up to apply" needs an account, so park the role with the CV ready for the candidate.
- **Ashby resume upload resets typed fields**: uploading into the
  system Resume field runs Ashby's autofill, which can drop values already typed (Full Name, Portfolio, a
  long answer) from the form's state while the boxes still display them; submit then fails with
  "Missing entry for required field". Upload the resume first, then type the fields (keyboard input,
  not a bulk fill), and read everything back before submitting.
- **Greenhouse (new job-boards UI) dropdowns** are react-select comboboxes: type, then click the option whose
  text matches exactly. A prefix filter picks the wrong one ("GMT+1" selected "GMT+12"). Timezone answer: see `profile/forms.md`. Read every combobox's displayed value back.
- **Ashby radio groups**: clicking the label can show the radio checked without
  registering it; submit then fails with "Missing entry". Click another option and back, then read back.
- **Workable inline apply (jobs.workable.com)**: decline the cookie banner first (its
  backdrop blocks "Apply now"). The address box pre-fills from IP location (it can show the wrong city): set
  the candidate's real city. Short text answers can cap at 127 characters. After submit it offers "Save your profile"
  (an account): leave it. Workable's widget API rate-limits quickly (Cloudflare 1015); use the browser.
- **Ashby yes/no questions** are two buttons (`data-option="yes"` / `"no"`) over a hidden checkbox:
  click the button, then check `aria-pressed`.
- **Canonical (Greenhouse)** makes the applicant tick "I agree to use only my own words ... the use
  of AI or other generated content will disqualify my application". Never draft those essay
  answers for the candidate; they write them themselves or skip the role.
- **RevenueCat (Ashby)** warns "Skipped questions or obviously AI-generated responses will result in your
  application being declined". Treat it like Canonical: fill only the factual fields, leave every written
  answer to the candidate, and give them fact notes rather than prose.
- **Lever** shows an hCaptcha picture puzzle on submit in the automation
  browser, so a Lever send ends with the candidate solving it. Its resume parser also rewrites fields
  after the upload settles: it typed the email twice and filled "Other website" on its own.
  Upload first, wait, then fill and read every field back.
- **"<Company> can contact me about future job opportunities"**: a
  future-roles consent, not a newsletter. Tick it, like the other consents above.
- **"How did you hear about us?" as free text**: "LinkedIn job posting" when the role
  came from the LinkedIn batch search, even if the form was then opened from the company board.

## When this applies

Trigger it whenever a posting or portal asks for any of:

- A self-introduction / personal statement / "tell us about yourself" paragraph
- Structured project entries (project name, role, start and end date, description)
- A short pitch under a hard character limit ("stand out in 140 characters", "why you, in one sentence")
- Motivation questions ("why this company", "why this program")
- Competency questions with a word cap ("describe a time you…", 200 words)

## The rule that governs everything here

**Every claim in a form field must already be defensible from the same sources the CV and cover letter are grounded against** - the union of `profile/profile.md` and the master CV (`profile/cv_content.py`), with a claim grounded if EITHER supports it. The interviewer reads the form alongside the CV. A form field is not a place to introduce new claims, inflate scope, or fill space - it is a place to *select* from what is already true and arrange it for the question asked.

All accuracy rules from `05-cv-templates.md` and `03-writing-style.md` apply unchanged.

## Field type: self-introduction paragraph

Usually 100-200 words, one paragraph, no formatting.

**Structure that works:**
1. Current status - what they are doing or completing now
2. The single strongest piece of evidence, with its number and scale
3. One line of trajectory: how they got here, if a pivot or specialisation is genuinely interesting
4. What they want next, connected to this employer's actual work

**Rules:**
- **Lead with the strongest evidence, not chronology.** A career history told in order buries the best material when the strongest work is recent.
- **Write one version per role type, not one for all applications.** The same history framed for a backend role and a data role are different paragraphs. Produce both, label them, and say which goes where.
- **Tie it to this employer in the final sentence.** Generic self-introductions are the default and read as such.
- **Count the words and state the count.** Portals truncate silently. Supply a trimmed variant and name which sentence to cut first.

## Field type: work authorization and engagement model

Nearly every form asks some version of "are you legally authorized to work in <country>?" or
"will you require sponsorship?". Read the candidate's right-to-work facts and engagement model from
`profile/profile.md` and their saved wording from `profile/forms.md`. Where the candidate can be
hired **either way** (as an employee, or as a vendor invoicing through their own company), these
answers should read as flexibility offered, never as a condition attached.

**Answer the question that was asked, then name the second option in one sentence** (when a second
option exists). The framing that works is "whichever is easier for you", because it hands the
employer a choice instead of a problem.

**Work authorization and sponsorship are specific to the country and engagement asked about.**
Use confirmed citizenship and residence facts. Never infer foreign employment authorization, or
answer every sponsorship question "No", merely because B2B invoicing is possible. For a mandatory
binary field whose correct answer is not established, ask the candidate before submitting. For a
free-text field, explain the routes without claiming an unconfirmed right to work.

Patterns (fill from the profile, keep them true):

**"Are you authorized to work in <country the candidate is not in>?"**

> I'm based in [CITY, COUNTRY]. I'm open to employment through a hiring arrangement you can
> support there, or [a B2B contract through ENTITY, with invoices]. Would either arrangement work?

**"Can you provide a company / are you registered as a business?"** (only if the profile has an entity; usually a procurement gate)

> Yes. [ENTITY] is a [VAT-registered] [COUNTRY] company. I can provide registration and VAT
> details, sign a standard contractor or supplier agreement, and invoice monthly. I'm equally happy
> to be hired as an employee if that's your normal process.

**"Where are you located?" / "What is your timezone?"**

> I work remotely, based in [COUNTRY] ([TIMEZONE]). I'm comfortable with an overlap window of [HOURS].

**Answer a location question honestly rather than letting a company registration imply an
answer.** Some employers genuinely need to know: data residency, equipment shipping, security
review, their own tax position. A mismatch discovered later costs more trust than the question
ever would have.

Do not volunteer a time-zone commitment the candidate has not agreed to. If a posting demands
sustained overlap outside their hours, that is a real constraint to raise, not to paper over.

**"Desired salary"** - for a contract, quote a **day rate**, and say so:

> I engage on a day rate rather than a salary. Happy to discuss the range once the scope and
> commitment are clear.

If the form forces a number, use the market band for the role and location and mark it
negotiable. See the Compensation section of `profile/profile.md` for the conversion.

**Where the form has no such field at all**, put one line in the cover letter's closing
paragraph instead. It is never a surprise worth saving for later.

## Field type: structured project entries

Typically **project name, role, start date, end date, description.**

**Project name.** Give the project a descriptive name, not the employer's name - "Warehouse Inventory Forecasting Platform" is a project, "Acme Corp" is an employer. Where a client is more recognisable than the employer, name the client only if the relationship is truthful (placed on-site with, delivered to).

**Role.** The candidate's role *on that project*, which may be narrower than their job title. Do not upgrade it.

**Dates.** The dates they worked on **that project**, which are not automatically the employment dates. If a role spanned two years but the named project occupied the later part, saying so is both more accurate and avoids the low-output reading described in `05-cv-templates.md` ("Check tenure against visible output"). Only narrow the dates when the candidate can say when the project actually started - never invent a boundary to improve the ratio.

**Description.** 100-150 words: what the system did and who used it, then the hardest technical problem and how it was solved, then the outcome with its number. Supply a **~60-word short version** as well; portals vary and the candidate should not have to improvise a cut.

**Scope discipline is stricter here than on a CV.** A CV bullet can be terse enough to be ambiguous about ownership. A project entry with the candidate's name and role attached reads as ownership of the whole thing. Where they contributed rather than owned, say so inside the description.

## Field type: hard character limits

These reward **a specific situation over an adjective**. Most applicants submit adjectives - "passionate", "fast learner", "team player" - so a concrete situation stands out by contrast.

**Method:**
1. Pick the single most distinctive true thing: usually a number, an unusual combination of backgrounds, or a problem shape that maps onto the employer's own work.
2. Draft 4-6 candidates at different angles.
3. **Count characters programmatically. Do not estimate.** Over-limit text is truncated mid-word.
4. Present all candidates with counts, recommend one, and say why.

Prefer the version that **maps the candidate's problem onto the employer's problem**, where a truthful mapping exists. That is what "stand out" is actually asking for.

## Output format

Save to a plain `.txt` file the candidate can copy from, alongside their other application material for that employer. One file per employer, containing every field that employer asked for.

Include:
- A header naming the employer and the roles it covers
- Each field, labelled, with word or character counts stated
- Short variants where limits may be tighter than expected
- **`NOTE TO SELF` blocks** for scope reminders and prepared answers to questions the content invites - clearly marked as *not for pasting into the form*
- A dates quick-reference, so date fields stay consistent without re-deriving them

## Verification before handing it over

- [ ] Every factual claim traces to the union of `profile/profile.md` and the master CV (`profile/cv_content.py`)
- [ ] No claim contradicts the CV or cover letter submitted for the same role
- [ ] Ownership scoped correctly on contributory work
