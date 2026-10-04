---
framework_version: 1.0.0
---

# Email Replies (recruiter and employer messages)

How to prepare a reply to a recruiter or employer email as a Gmail draft (it shows up in the Drafts folder of the Gmail account, where the candidate opens and sends it). Applies whenever the candidate asks for "a reply to <email>", and to any follow-up this workspace drafts. **Draft only, never send**: the candidate reads it and sends it themselves.

## The one hard rule: the email history stays, untouched, at the bottom

The reply must be a real reply to the original message, threaded under it and carrying the original as it was. The new text goes **above** the quote. `tools/gmail_client.py draft-reply` does exactly this: `In-Reply-To`/`References` set, the original's own HTML embedded unchanged inside one quote block (the structure Gmail and desktop mail clients use for a native reply), Cc kept. Never:

- re-type, summarise or edit the original, or prefix its lines with ">";
- leave an empty draft for the candidate to fill: the draft carries your text.

## Procedure (Gmail, `tools/gmail_client.py`)

1. Find the original: `python3 tools/gmail_client.py search 'from:<sender> newer_than:14d' --limit 10`, confirm the subject, read it with `python3 tools/gmail_client.py read <id>`.
2. Write the reply text to `profile/applications/<slug>/reply_draft.txt` (just your text: no quote, no "On ... wrote:").
3. `python3 tools/gmail_client.py draft-reply <id> < profile/applications/<slug>/reply_draft.txt` - prints `draft saved to [Gmail]/Drafts`. Never send; nothing in this workspace sends mail.
4. Verify: `python3 tools/gmail_client.py search 'subject:"<subject>"' --drafts` shows exactly one draft (draft ids change every time a mail client saves it, so always search again for the id instead of reusing an old one); `read <draft id> --drafts` shows your text first, then the "wrote:" line and the original.
5. Rebuilding a draft: remove the stale one with `python3 tools/gmail_client.py trash <draft id> --drafts`, then repeat from step 3. Keep exactly one draft per reply. When the candidate has edited the draft and asks for a change, start from their edited text (`read <draft id> --drafts`), not from the saved copy, so their edits survive.
6. Tell the candidate the draft is in their Drafts and what it says in one line.

## Recipients: keep everyone the original copied

`draft-reply` keeps every Cc of the original except the candidate's own address, and replies to the original's Reply-To (or From). Anyone Cc'd on the original, such as a colleague of the sender, stays in the Cc of the reply. Check the draft's Cc in step 4 and say so if it differs. Never add recipients that were not on the original.

## Content rules

- Answer every question the sender asked, in the order asked. Facts only from `profile/profile.md`, the answer bank in `profile/forms.md`, and what the candidate says in the conversation. Never invent experience.
- Keep it short; the candidate trims. No em-dashes. Reply in the language the sender wrote in if the profile lists it as a working language, otherwise English.
- **Projects named as examples** must match the profile's state: "building" for in-progress work, never "shipped".
- **Engagement and visa.** If the profile's Engagement Model offers contract work, a short fixed-term contract (about 6 months or less) can be offered through the candidate's own entity: no payroll or work-permit process for the employer. If the role could become permanent, say that permanent employment abroad would need visa and relocation support, and that this can be discussed then. State right-to-work facts exactly as in the profile.
- **Pay.** Use the answer bank. Say it in one short sentence. State whether a figure is gross or net as the candidate gave it, and never convert currencies.
- Notice period and location: from `profile/profile.md`.

Related: `08-application-forms.md` (methodology), `profile/forms.md` (answer bank), `profile/profile.md` (Engagement Model).
